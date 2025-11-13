"""
Orchestrator Agent - The brain of the automated X account system.

This agent coordinates all sub-agents (News Hunter, Meme Lord, Image Generator, Content Curator),
makes intelligent decisions about what to post when, ensures content variety, prevents duplicates,
and maintains a consistent once-per-day posting schedule.

Key Responsibilities:
- Agent coordination and content type selection
- Scheduling (once per day, varied times)
- Content variety management
- Duplicate prevention (3-layer check)
- Quality control
- X posting with Tweepy
- Learning and optimization
"""

import os
import asyncio
import json
import hashlib
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pytz
from dotenv import load_dotenv
import tweepy
from openai import OpenAI

# Import sub-agents
from news_hunter import NewsHunterAgent
from meme_lord import MemeLordAgent
from image_generator import ImageGeneratorAgent
from content_curator import ContentCuratorAgent


class OrchestratorAgent:
    """The orchestrator agent that coordinates all posting activities."""

    def __init__(
        self,
        db_dir: str = None,
        log_dir: str = None,
        dry_run: bool = False
    ):
        """
        Initialize the Orchestrator Agent.

        Args:
            db_dir: Directory for state and posts database
            log_dir: Directory for logs
            dry_run: If True, don't actually post to X (for testing)
        """
        load_dotenv()

        # Directories - auto-detect based on environment
        script_dir = Path(__file__).parent
        if db_dir is None:
            # Use relative path from script location (works on Render)
            db_dir = script_dir / "orchestrator_db"
        if log_dir is None:
            log_dir = script_dir / "logs"

        self.db_dir = Path(db_dir)
        self.log_dir = Path(log_dir)
        self.db_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Database files
        self.state_file = self.db_dir / "orchestrator_state.json"
        self.posts_db_file = self.db_dir / "posts_database.json"
        self.backup_content_file = script_dir / "backup_content.json"

        # Configuration
        self.dry_run = dry_run
        self.timezone = pytz.timezone("Europe/Stockholm")

        # Configuration from orchestrator.md
        self.config = {
            # Posting
            "posts_per_day": 1,
            "posting_times": {
                "morning": {"hours": (8, 10), "probability": 0.30},
                "lunch": {"hours": (12, 13), "probability": 0.20},
                "afternoon": {"hours": (15, 17), "probability": 0.10},
                "evening": {"hours": (18, 20), "probability": 0.30},
                "night": {"hours": (21, 22), "probability": 0.10}
            },
            "time_variance_minutes": 30,

            # Content Mix (base weights)
            "base_weights": {
                "news": 0.35,
                "curator": 0.30,
                "meme": 0.20,
                "image": 0.15
            },
            "max_same_type_streak": 2,

            # Quality Control
            "min_quality_score": 6,
            "max_regeneration_attempts": 2,
            "duplicate_similarity_threshold": 0.85,

            # History
            "track_days": 30,
            "recent_topics_size": 10,

            # Error Handling
            "max_retries": 3,
            "retry_delay_minutes": 60,
            "use_backup_after_fails": 2
        }

        # API Keys
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.x_api_key = os.getenv("X_API_KEY")
        self.x_api_secret = os.getenv("X_API_SECRET")
        self.x_access_token = os.getenv("X_ACCESS_TOKEN")
        self.x_access_token_secret = os.getenv("X_ACCESS_TOKEN_SECRET")
        self.x_bearer_token = os.getenv("X_BEARER_TOKEN")

        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Initialize OpenAI client for embeddings
        self.openai_client = OpenAI(api_key=self.openai_api_key)

        # Initialize Tweepy (only if not dry run and credentials available)
        self.twitter_client = None
        self.twitter_api_v1 = None
        if not self.dry_run:
            if all([self.x_api_key, self.x_api_secret, self.x_access_token, self.x_access_token_secret]):
                # V2 Client for posting
                self.twitter_client = tweepy.Client(
                    bearer_token=self.x_bearer_token,
                    consumer_key=self.x_api_key,
                    consumer_secret=self.x_api_secret,
                    access_token=self.x_access_token,
                    access_token_secret=self.x_access_token_secret
                )

                # V1 API for media upload
                auth = tweepy.OAuth1UserHandler(
                    self.x_api_key,
                    self.x_api_secret,
                    self.x_access_token,
                    self.x_access_token_secret
                )
                self.twitter_api_v1 = tweepy.API(auth)
            else:
                logging.warning("X API credentials not complete. Posting will fail if attempted.")

        # Initialize sub-agents (will be created on demand to avoid import errors)
        self.news_agent = None
        self.meme_agent = None
        self.image_agent = None
        self.curator_agent = None

        # Setup logging first
        self._setup_logging()

        # Initialize databases
        self._init_databases()

        logging.info("Orchestrator Agent initialized")
        logging.info(f"Dry run mode: {self.dry_run}")
        logging.info(f"Timezone: {self.timezone}")

    def _setup_logging(self):
        """Setup logging configuration."""
        log_file = self.log_dir / f"orchestrator_{datetime.now().strftime('%Y%m%d')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )

    def _init_databases(self):
        """Initialize database files if they don't exist."""
        # State file
        if not self.state_file.exists():
            initial_state = {
                "last_post_time": None,
                "last_7_days_posts": [],
                "week_counts": {
                    "news": 0,
                    "curator": 0,
                    "meme": 0,
                    "image": 0
                },
                "recent_topics": [],
                "curated_tweet_ids": [],
                "engagement_by_type": {
                    "news": {"avg_likes": 0, "avg_rt": 0, "count": 0},
                    "curator": {"avg_likes": 0, "avg_rt": 0, "count": 0},
                    "meme": {"avg_likes": 0, "avg_rt": 0, "count": 0},
                    "image": {"avg_likes": 0, "avg_rt": 0, "count": 0}
                },
                "next_post_scheduled": None,
                "preferred_time_windows": ["morning", "evening"],
                "week_start_date": datetime.now(self.timezone).strftime("%Y-%m-%d")
            }
            self._save_json(self.state_file, initial_state)
            logging.info("Initialized state database")

        # Posts database
        if not self.posts_db_file.exists():
            initial_posts_db = {
                "posts": []
            }
            self._save_json(self.posts_db_file, initial_posts_db)
            logging.info("Initialized posts database")

        # Backup content file
        if not self.backup_content_file.exists():
            backup_content = {
                "news": [
                    "AI agents are transforming how we work. The future of automation is here and it's getting wild.",
                    "New AI models dropping every week. Can't keep up anymore but loving the chaos."
                ],
                "meme": [
                    "me: automates everything\nalso me: spends 10 hours debugging the automation",
                    "AI in 2025: generates entire movies\nAlso AI: can't count the Rs in strawberry"
                ],
                "curator": [],
                "image": []
            }
            self._save_json(self.backup_content_file, backup_content)
            logging.info("Initialized backup content file")

    def _load_json(self, filepath: Path) -> Dict:
        """Load JSON file."""
        with open(filepath, 'r') as f:
            return json.load(f)

    def _save_json(self, filepath: Path, data: Dict):
        """Save JSON file."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def load_state(self) -> Dict:
        """Load orchestrator state."""
        state = self._load_json(self.state_file)

        # Check if we need to reset weekly counters
        week_start = datetime.strptime(state["week_start_date"], "%Y-%m-%d")
        now = datetime.now(self.timezone)
        days_since_week_start = (now - week_start.replace(tzinfo=self.timezone)).days

        if days_since_week_start >= 7:
            # Reset weekly counters
            state["week_counts"] = {
                "news": 0,
                "curator": 0,
                "meme": 0,
                "image": 0
            }
            state["week_start_date"] = now.strftime("%Y-%m-%d")
            self._save_json(self.state_file, state)
            logging.info("Reset weekly counters")

        return state

    def save_state(self, state: Dict):
        """Save orchestrator state."""
        self._save_json(self.state_file, state)

    def load_posts_db(self) -> Dict:
        """Load posts database."""
        return self._load_json(self.posts_db_file)

    def save_posts_db(self, posts_db: Dict):
        """Save posts database."""
        self._save_json(self.posts_db_file, posts_db)

    def should_post_now(self) -> bool:
        """
        Check if it's time to post based on schedule.

        Returns:
            True if it's time to post, False otherwise
        """
        state = self.load_state()
        now = datetime.now(self.timezone)

        # If next_post_scheduled is set, check if we've reached that time
        if state["next_post_scheduled"]:
            scheduled_time = datetime.fromisoformat(state["next_post_scheduled"])
            if scheduled_time.tzinfo is None:
                scheduled_time = self.timezone.localize(scheduled_time)

            if now >= scheduled_time:
                logging.info(f"Scheduled post time reached: {scheduled_time}")
                return True
            else:
                logging.info(f"Not yet time to post. Next scheduled: {scheduled_time}")
                return False

        # If no schedule set, check if we posted today
        if state["last_post_time"]:
            last_post = datetime.fromisoformat(state["last_post_time"])
            if last_post.tzinfo is None:
                last_post = self.timezone.localize(last_post)

            # Check if last post was today
            if last_post.date() == now.date():
                logging.info("Already posted today")
                return False

            # Check if at least 20 hours have passed (minimum gap)
            hours_since_last = (now - last_post).total_seconds() / 3600
            if hours_since_last < 20:
                logging.info(f"Too soon since last post ({hours_since_last:.1f} hours)")
                return False

        # Ready to post
        logging.info("Ready to post")
        return True

    def select_content_type(self, state: Dict) -> str:
        """
        Select content type using weighted probabilities with penalties and boosts.

        Args:
            state: Current orchestrator state

        Returns:
            Selected content type: 'news', 'curator', 'meme', or 'image'
        """
        logging.info("Selecting content type...")

        # Start with base weights
        weights = self.config["base_weights"].copy()
        last_7_days = state["last_7_days_posts"]

        # Get yesterday's content type
        yesterday_type = last_7_days[-1]["type"] if last_7_days else None
        day_before_type = last_7_days[-2]["type"] if len(last_7_days) >= 2 else None

        logging.info(f"Last 7 days: {[p['type'] for p in last_7_days]}")
        logging.info(f"Yesterday: {yesterday_type}, Day before: {day_before_type}")

        # Apply adjustment rules
        for content_type in weights.keys():
            original_weight = weights[content_type]

            # Rule 1: Recency Penalty - posted yesterday
            if yesterday_type == content_type:
                weights[content_type] *= 0.3
                logging.info(f"  {content_type}: Recency penalty (posted yesterday) {original_weight:.3f} -> {weights[content_type]:.3f}")

            # Rule 2: Repetition Penalty - posted 2 days in a row
            if yesterday_type == content_type and day_before_type == content_type:
                weights[content_type] = 0
                logging.info(f"  {content_type}: Repetition penalty (posted 2 days in row) -> 0")

            # Rule 3: Boost Underused - not posted in 4+ days
            days_since_last = self._days_since_content_type(last_7_days, content_type)
            if days_since_last >= 4:
                weights[content_type] *= 1.5
                logging.info(f"  {content_type}: Boost underused ({days_since_last} days) {original_weight:.3f} -> {weights[content_type]:.3f}")

            # Rule 4: Weekly Balance - check if over quota
            week_counts = state["week_counts"]
            expected_weekly = {
                "news": 2.5,      # 35% of 7
                "curator": 2.1,   # 30% of 7
                "meme": 1.4,      # 20% of 7
                "image": 1.0      # 15% of 7
            }

            if week_counts[content_type] > expected_weekly[content_type]:
                weights[content_type] *= 0.5
                logging.info(f"  {content_type}: Over weekly quota ({week_counts[content_type]}/{expected_weekly[content_type]:.1f}) -> {weights[content_type]:.3f}")

        # Normalize weights
        total = sum(weights.values())
        if total == 0:
            # All weights are zero, reset to base
            logging.warning("All weights are zero, using base weights")
            weights = self.config["base_weights"].copy()
            total = sum(weights.values())

        normalized = {k: v / total for k, v in weights.items()}

        logging.info(f"Final probabilities: {normalized}")

        # Weighted random selection
        choices = list(normalized.keys())
        probabilities = list(normalized.values())
        selected = random.choices(choices, weights=probabilities, k=1)[0]

        logging.info(f"Selected content type: {selected}")
        return selected

    def _days_since_content_type(self, last_7_days: List[Dict], content_type: str) -> int:
        """
        Calculate days since a content type was last posted.

        Args:
            last_7_days: List of last 7 days posts
            content_type: Content type to check

        Returns:
            Number of days since last posted (7+ if not in last 7 days)
        """
        for i, post in enumerate(reversed(last_7_days)):
            if post["type"] == content_type:
                return i
        return 7

    async def call_agent(self, content_type: str, state: Dict) -> Optional[Dict]:
        """
        Call the appropriate sub-agent based on content type.

        Args:
            content_type: Type of content to generate
            state: Current orchestrator state

        Returns:
            Dict with 'text', 'media_path', 'metadata' or None if failed
        """
        logging.info(f"Calling {content_type} agent...")

        try:
            if content_type == "news":
                # Lazy load news agent
                if not self.news_agent:
                    self.news_agent = NewsHunterAgent(model="gpt-5-mini")

                post_text = await self.news_agent.search_and_generate()
                return {
                    "text": post_text,
                    "media_path": None,
                    "metadata": {
                        "agent": "news_hunter",
                        "source": "serper_search"
                    }
                }

            elif content_type == "meme":
                # Lazy load meme agent
                if not self.meme_agent:
                    self.meme_agent = MemeLordAgent(model="gpt-5-mini")

                post_text = await self.meme_agent.generate_meme_post()
                return {
                    "text": post_text,
                    "media_path": None,
                    "metadata": {
                        "agent": "meme_lord",
                        "source": "generated"
                    }
                }

            elif content_type == "image":
                # Lazy load image agent
                if not self.image_agent:
                    self.image_agent = ImageGeneratorAgent(model="gpt-5-mini")

                result = await self.image_agent.generate_image()
                if result["status"] == "completed" and result.get("local_paths"):
                    # Use first generated image
                    return {
                        "text": "The future of AI agents >",  # Default caption
                        "media_path": result["local_paths"][0],
                        "metadata": {
                            "agent": "image_generator",
                            "source": "midjourney",
                            "image_urls": result["urls"]
                        }
                    }
                else:
                    logging.error(f"Image generation failed: {result.get('error')}")
                    return None

            elif content_type == "curator":
                # Lazy load curator agent
                if not self.curator_agent:
                    self.curator_agent = ContentCuratorAgent(model="gpt-5-mini")

                curated = await self.curator_agent.curate_content(limit=1)
                if curated and len(curated) > 0:
                    item = curated[0]
                    return {
                        "text": item["commentary"],
                        "media_path": item.get("media_path"),
                        "metadata": {
                            "agent": "content_curator",
                            "source": "x_viral",
                            "original_author": item["original_author"],
                            "original_tweet_id": item["original_tweet_id"],
                            "engagement": item["engagement"]
                        }
                    }
                else:
                    logging.error("Content curator returned no results")
                    return None

        except Exception as e:
            logging.error(f"Error calling {content_type} agent: {e}", exc_info=True)
            return None

    def validate_content(self, content: Dict) -> Tuple[bool, float, str]:
        """
        Validate content quality.

        Args:
            content: Content dict with 'text' and 'media_path'

        Returns:
            Tuple of (is_valid, quality_score, reason)
        """
        logging.info("Validating content...")

        text = content["text"]
        media_path = content.get("media_path")
        quality_score = 10.0
        issues = []

        # Text validation
        if not text or len(text.strip()) == 0:
            return False, 0, "Empty text"

        if len(text) > 280:
            quality_score -= 5
            issues.append(f"Text too long ({len(text)}/280 chars)")

        # Check for broken formatting
        if text.count('"') % 2 != 0 or text.count("'") % 2 != 0:
            quality_score -= 1
            issues.append("Unbalanced quotes")

        # Media validation (if present)
        if media_path:
            media_file = Path(media_path)
            if not media_file.exists():
                quality_score -= 3
                issues.append("Media file not found")
            else:
                # Check file size
                file_size_mb = media_file.stat().st_size / (1024 * 1024)
                if file_size_mb > 512:
                    quality_score -= 2
                    issues.append(f"Media too large ({file_size_mb:.1f} MB)")

                # Check extension
                valid_extensions = ['.mp4', '.jpg', '.jpeg', '.png', '.gif', '.webm']
                if media_file.suffix.lower() not in valid_extensions:
                    quality_score -= 2
                    issues.append(f"Invalid media format ({media_file.suffix})")

        # Overall quality check
        is_valid = quality_score >= self.config["min_quality_score"]

        if is_valid:
            logging.info(f"Content validated successfully. Quality score: {quality_score}/10")
        else:
            reason = "; ".join(issues)
            logging.warning(f"Content validation failed. Quality score: {quality_score}/10. Issues: {reason}")
            return False, quality_score, reason

        return True, quality_score, "OK"

    def _compute_text_hash(self, text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode()).hexdigest()

    def _get_embedding(self, text: str) -> List[float]:
        """
        Get OpenAI embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logging.error(f"Error getting embedding: {e}")
            return []

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def check_duplicates(self, content: Dict) -> Tuple[bool, str]:
        """
        Check for duplicates using 3-layer detection.

        Args:
            content: Content dict with 'text' and metadata

        Returns:
            Tuple of (is_duplicate, reason)
        """
        logging.info("Checking for duplicates...")

        text = content["text"]
        posts_db = self.load_posts_db()
        posts = posts_db["posts"]

        # Layer 1: Exact Match
        text_hash = self._compute_text_hash(text)
        for post in posts:
            if post.get("text_hash") == text_hash:
                logging.warning("Duplicate detected: Exact text match")
                return True, "Exact text match"

        # Layer 2: Semantic Similarity
        embedding = self._get_embedding(text)
        if embedding:
            # Check last 30 days of posts
            cutoff_date = datetime.now(self.timezone) - timedelta(days=self.config["track_days"])

            for post in posts:
                post_date = datetime.fromisoformat(post["posted_at"])
                if post_date.tzinfo is None:
                    post_date = self.timezone.localize(post_date)

                if post_date < cutoff_date:
                    continue

                if post.get("embedding"):
                    similarity = self._cosine_similarity(embedding, post["embedding"])
                    if similarity > self.config["duplicate_similarity_threshold"]:
                        logging.warning(f"Duplicate detected: Semantic similarity {similarity:.2f}")
                        return True, f"Semantic similarity {similarity:.2f}"

        # Layer 3: Topic Overlap (for curated content)
        if content["metadata"].get("agent") == "content_curator":
            original_tweet_id = content["metadata"].get("original_tweet_id")
            if original_tweet_id:
                for post in posts:
                    if post.get("metadata", {}).get("original_tweet_id") == original_tweet_id:
                        logging.warning("Duplicate detected: Same source tweet")
                        return True, "Same source tweet already curated"

        logging.info("No duplicates detected")
        return False, "No duplicates"

    async def post_to_x(self, content: Dict) -> Optional[str]:
        """
        Post content to X using Tweepy.

        Args:
            content: Content dict with 'text' and 'media_path'

        Returns:
            Tweet ID if successful, None otherwise
        """
        if self.dry_run:
            logging.info("DRY RUN: Would post to X:")
            logging.info(f"  Text: {content['text']}")
            logging.info(f"  Media: {content.get('media_path')}")
            return "dry_run_tweet_id_12345"

        if not self.twitter_client:
            logging.error("Twitter client not initialized. Cannot post.")
            return None

        try:
            text = content["text"]
            media_path = content.get("media_path")

            media_ids = []

            # Upload media if present
            if media_path and self.twitter_api_v1:
                logging.info(f"Uploading media: {media_path}")
                media = self.twitter_api_v1.media_upload(filename=media_path)
                media_ids.append(media.media_id)
                logging.info(f"Media uploaded: {media.media_id}")

            # Post tweet
            logging.info("Posting tweet...")
            response = self.twitter_client.create_tweet(
                text=text,
                media_ids=media_ids if media_ids else None
            )

            tweet_id = response.data["id"]
            logging.info(f"Tweet posted successfully! ID: {tweet_id}")
            return tweet_id

        except Exception as e:
            logging.error(f"Error posting to X: {e}", exc_info=True)
            return None

    def update_state_after_post(self, state: Dict, content_type: str, content: Dict, tweet_id: str):
        """
        Update orchestrator state after successful post.

        Args:
            state: Current state
            content_type: Type of content posted
            content: Posted content
            tweet_id: Posted tweet ID
        """
        now = datetime.now(self.timezone)

        # Update last post time
        state["last_post_time"] = now.isoformat()

        # Update last 7 days posts
        state["last_7_days_posts"].append({
            "type": content_type,
            "date": now.strftime("%Y-%m-%d"),
            "tweet_id": tweet_id
        })

        # Keep only last 7
        if len(state["last_7_days_posts"]) > 7:
            state["last_7_days_posts"] = state["last_7_days_posts"][-7:]

        # Update week counts
        state["week_counts"][content_type] += 1

        # Update recent topics (extract from text)
        # Simple extraction: look for capitalized words/phrases
        text = content["text"]
        words = text.split()
        topics = [w for w in words if len(w) > 3 and w[0].isupper()]
        state["recent_topics"].extend(topics[:3])
        state["recent_topics"] = state["recent_topics"][-self.config["recent_topics_size"]:]

        # Update curated tweet IDs if curator
        if content_type == "curator" and content["metadata"].get("original_tweet_id"):
            state["curated_tweet_ids"].append(content["metadata"]["original_tweet_id"])
            state["curated_tweet_ids"] = state["curated_tweet_ids"][-50:]  # Keep last 50

        # Schedule next post
        next_post_time = self.schedule_next_post(now)
        state["next_post_scheduled"] = next_post_time.isoformat()

        # Save state
        self.save_state(state)
        logging.info("State updated successfully")

    def update_posts_database(self, content_type: str, content: Dict, tweet_id: str, quality_score: float):
        """
        Add post to posts database.

        Args:
            content_type: Type of content
            content: Content dict
            tweet_id: Posted tweet ID
            quality_score: Quality score
        """
        posts_db = self.load_posts_db()

        # Create embedding
        embedding = self._get_embedding(content["text"])

        # Create post entry
        post_entry = {
            "post_id": tweet_id,
            "posted_at": datetime.now(self.timezone).isoformat(),
            "content_type": content_type,
            "text": content["text"],
            "text_hash": self._compute_text_hash(content["text"]),
            "embedding": embedding,
            "media_url": content.get("media_path"),
            "agent_used": content["metadata"]["agent"],
            "metadata": content["metadata"],
            "quality_score": quality_score,
            "engagement": {
                "likes": 0,
                "retweets": 0,
                "views": 0
            }
        }

        posts_db["posts"].append(post_entry)

        # Clean old posts (keep only last 30 days)
        cutoff_date = datetime.now(self.timezone) - timedelta(days=self.config["track_days"])
        posts_db["posts"] = [
            p for p in posts_db["posts"]
            if datetime.fromisoformat(p["posted_at"]) > cutoff_date
        ]

        self.save_posts_db(posts_db)
        logging.info("Posts database updated")

    def schedule_next_post(self, current_time: datetime) -> datetime:
        """
        Schedule next post time (24h + variance).

        Args:
            current_time: Current posting time

        Returns:
            Scheduled next post time
        """
        # Select time window based on probabilities
        time_windows = self.config["posting_times"]
        window_names = list(time_windows.keys())
        window_probs = [time_windows[w]["probability"] for w in window_names]

        selected_window = random.choices(window_names, weights=window_probs, k=1)[0]
        window_config = time_windows[selected_window]

        # Get hour range
        start_hour, end_hour = window_config["hours"]

        # Tomorrow in the selected window
        tomorrow = current_time + timedelta(days=1)
        base_hour = random.randint(start_hour, end_hour - 1)
        base_minute = random.randint(0, 59)

        # Apply variance
        variance_minutes = random.randint(-self.config["time_variance_minutes"],
                                         self.config["time_variance_minutes"])

        scheduled_time = tomorrow.replace(hour=base_hour, minute=base_minute, second=0, microsecond=0)
        scheduled_time += timedelta(minutes=variance_minutes)

        logging.info(f"Next post scheduled for: {scheduled_time} ({selected_window} window)")
        return scheduled_time

    async def get_backup_content(self, content_type: str) -> Optional[Dict]:
        """
        Get backup content if all agents fail.

        Args:
            content_type: Type of content needed

        Returns:
            Content dict or None
        """
        logging.info(f"Using backup content for {content_type}")

        backup_data = self._load_json(self.backup_content_file)
        backup_list = backup_data.get(content_type, [])

        if not backup_list:
            logging.error(f"No backup content available for {content_type}")
            return None

        # Use first backup content
        text = backup_list[0]

        return {
            "text": text,
            "media_path": None,
            "metadata": {
                "agent": "backup",
                "source": "backup_content",
                "original_type": content_type
            }
        }

    async def run_daily(self):
        """
        Main daily orchestration workflow.

        This is the main entry point that should be called once per day.
        """
        logging.info("="*60)
        logging.info("ORCHESTRATOR DAILY RUN STARTING")
        logging.info("="*60)

        # Check if it's time to post
        if not self.should_post_now():
            logging.info("Not time to post yet. Exiting.")
            return

        # Load state
        state = self.load_state()

        # Select content type
        content_type = self.select_content_type(state)

        # Try to generate content (with retries)
        content = None
        for attempt in range(self.config["max_regeneration_attempts"] + 1):
            logging.info(f"Content generation attempt {attempt + 1}/{self.config['max_regeneration_attempts'] + 1}")

            # Call agent
            content = await self.call_agent(content_type, state)

            if not content:
                logging.warning(f"Agent returned no content on attempt {attempt + 1}")
                if attempt < self.config["max_regeneration_attempts"]:
                    continue
                else:
                    # Try backup content
                    content = await self.get_backup_content(content_type)
                    break

            # Validate content
            is_valid, quality_score, reason = self.validate_content(content)
            if not is_valid:
                logging.warning(f"Content validation failed: {reason}")
                if attempt < self.config["max_regeneration_attempts"]:
                    continue
                else:
                    break

            # Check duplicates
            is_duplicate, dup_reason = self.check_duplicates(content)
            if is_duplicate:
                logging.warning(f"Duplicate detected: {dup_reason}")
                if attempt < self.config["max_regeneration_attempts"]:
                    continue
                else:
                    break

            # Content is good!
            break

        # If we still don't have valid content, abort
        if not content:
            logging.error("Failed to generate valid content after all attempts. Aborting.")
            return

        # Final validation
        is_valid, quality_score, reason = self.validate_content(content)
        if not is_valid:
            logging.error(f"Final content validation failed: {reason}. Aborting.")
            return

        # Post to X
        logging.info("Posting content to X...")
        tweet_id = await self.post_to_x(content)

        if not tweet_id:
            logging.error("Failed to post to X. Aborting.")
            return

        # Update state and database
        logging.info("Updating state and database...")
        self.update_state_after_post(state, content_type, content, tweet_id)
        self.update_posts_database(content_type, content, tweet_id, quality_score)

        logging.info("="*60)
        logging.info("ORCHESTRATOR DAILY RUN COMPLETED SUCCESSFULLY")
        logging.info(f"Posted: {content_type}")
        logging.info(f"Tweet ID: {tweet_id}")
        logging.info(f"Quality Score: {quality_score}/10")
        logging.info("="*60)

    async def run_weekly_analysis(self):
        """
        Weekly analysis and optimization.

        Analyzes performance and adjusts weights accordingly.
        """
        logging.info("Running weekly analysis...")

        state = self.load_state()
        posts_db = self.load_posts_db()

        # Analyze engagement by content type
        engagement_by_type = {
            "news": {"likes": [], "retweets": []},
            "curator": {"likes": [], "retweets": []},
            "meme": {"likes": [], "retweets": []},
            "image": {"likes": [], "retweets": []}
        }

        # Collect last 7 days engagement
        cutoff_date = datetime.now(self.timezone) - timedelta(days=7)
        for post in posts_db["posts"]:
            post_date = datetime.fromisoformat(post["posted_at"])
            if post_date.tzinfo is None:
                post_date = self.timezone.localize(post_date)

            if post_date < cutoff_date:
                continue

            content_type = post["content_type"]
            engagement = post.get("engagement", {})

            engagement_by_type[content_type]["likes"].append(engagement.get("likes", 0))
            engagement_by_type[content_type]["retweets"].append(engagement.get("retweets", 0))

        # Calculate averages
        for content_type in engagement_by_type:
            likes = engagement_by_type[content_type]["likes"]
            retweets = engagement_by_type[content_type]["retweets"]

            avg_likes = sum(likes) / len(likes) if likes else 0
            avg_retweets = sum(retweets) / len(retweets) if retweets else 0

            state["engagement_by_type"][content_type]["avg_likes"] = avg_likes
            state["engagement_by_type"][content_type]["avg_rt"] = avg_retweets
            state["engagement_by_type"][content_type]["count"] = len(likes)

            logging.info(f"{content_type}: {len(likes)} posts, avg {avg_likes:.1f} likes, {avg_retweets:.1f} RTs")

        # Save updated state
        self.save_state(state)
        logging.info("Weekly analysis complete")


async def main():
    """
    Example usage of the Orchestrator Agent.
    """
    # Initialize orchestrator (dry_run=True for testing)
    orchestrator = OrchestratorAgent(dry_run=True)

    # Run daily workflow
    await orchestrator.run_daily()


if __name__ == "__main__":
    asyncio.run(main())
