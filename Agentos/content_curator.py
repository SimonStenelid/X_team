"""
Content Curator Agent - Finds viral AI posts on X, downloads media, and generates unique commentary.

This agent uses:
1. Apify Twitter Scraper to find viral AI content (150 tweets/run on free tier)
2. OpenAI Agents SDK (GPT-4o) to generate Min Choi style commentary
3. gallery-dl for reliable video/media downloads from X/Twitter (preferred method)
4. Requests library to download videos/images as fallback (when direct URLs available)
5. JSON database to track reposted content and avoid duplicates

Download Strategy:
- Primary: gallery-dl (handles X authentication, highest quality)
- Fallback: Direct URL download from Apify data
- Last resort: Manual download notification with tweet URL
"""

import os
import asyncio
import json
import requests
import time
import subprocess
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from dotenv import load_dotenv
from apify_client import ApifyClient
from agents import Agent, Runner


class ContentCuratorAgent:
    """Agent that finds viral AI content and creates curated posts."""

    def __init__(
        self,
        model: str = "gpt-4o",
        media_dir: str = "/Users/simonstenelid/Desktop/X_team/Agentos/curated_media",
        db_dir: str = "/Users/simonstenelid/Desktop/X_team/Agentos/curated_db"
    ):
        """
        Initialize the Content Curator agent with API keys and configuration.

        Args:
            model: AI model to use for commentary generation (default: gpt-4o)
            media_dir: Directory to save downloaded media (default: Agentos/curated_media)
            db_dir: Directory to store tracking database (default: Agentos/curated_db)
        """
        load_dotenv()

        self.apify_api_key = os.getenv("APIFY_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model = model

        if not self.apify_api_key:
            raise ValueError("APIFY_API_KEY not found in environment")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        # Initialize Apify client
        self.apify_client = ApifyClient(self.apify_api_key)

        # Create directories
        self.media_dir = Path(media_dir)
        self.db_dir = Path(db_dir)
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.db_dir.mkdir(parents=True, exist_ok=True)

        # Database files
        self.db_file = self.db_dir / "reposted_tweets.json"
        self._init_database()

        # Configuration
        self.config = {
            "min_engagement": 1000,  # minimum likes
            "max_age_hours": 48,  # only tweets from last 48 hours
            "max_retries": 3,  # for downloads
            "sweet_spot_min": 1000,  # ideal engagement range
            "sweet_spot_max": 5000,
            "use_gallery_dl": True,  # prefer gallery-dl for downloads
            "gallery_dl_quality": "best",  # video quality: best, worst, or specific format
            "download_timeout": 60,  # seconds for gallery-dl
        }

    def _init_database(self):
        """Initialize the tracking database if it doesn't exist."""
        if not self.db_file.exists():
            with open(self.db_file, 'w') as f:
                json.dump({"reposted_tweets": []}, f, indent=2)

    def _load_database(self) -> Dict:
        """Load the tracking database."""
        with open(self.db_file, 'r') as f:
            return json.load(f)

    def _save_database(self, data: Dict):
        """Save the tracking database."""
        with open(self.db_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _is_already_reposted(self, tweet_id: str) -> bool:
        """Check if a tweet has already been reposted."""
        db = self._load_database()
        return any(t["tweet_id"] == tweet_id for t in db["reposted_tweets"])

    def _track_reposted_content(self, tweet_data: Dict):
        """Add a tweet to the tracking database."""
        db = self._load_database()

        entry = {
            "tweet_id": tweet_data["id"],
            "original_author": tweet_data["author"]["userName"],
            "original_text": tweet_data.get("text", ""),
            "reposted_at": datetime.now().isoformat(),
            "engagement": {
                "likes": tweet_data.get("likeCount", 0),
                "retweets": tweet_data.get("retweetCount", 0),
                "replies": tweet_data.get("replyCount", 0),
            },
            "media_url": tweet_data.get("media_url", ""),
            "our_commentary": tweet_data.get("our_commentary", "")
        }

        db["reposted_tweets"].append(entry)
        self._save_database(db)

    async def search_viral_content(self, max_items: int = 30) -> List[Dict]:
        """
        Search for viral AI content using Apify Twitter Scraper.

        Args:
            max_items: Maximum number of tweets to search (free tier: 150 max)

        Returns:
            List of tweet data dictionaries
        """
        print(f"\nSearching for viral AI content on X...")
        print(f"Target: min {self.config['min_engagement']} likes, last {self.config['max_age_hours']}h")
        print(f"Using Apify Twitter Scraper (free tier: 150 tweets max)")

        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=self.config['max_age_hours'])

        # Format dates for Apify
        start_str = start_date.strftime("%Y-%m-%d_%H:%M:%S_UTC")
        end_str = end_date.strftime("%Y-%m-%d_%H:%M:%S_UTC")

        # Prepare search terms
        search_terms = [
            f"#Veo2 min_faves:{self.config['min_engagement']} since:{start_str} until:{end_str}",
            f"#Sora min_faves:{self.config['min_engagement']} since:{start_str} until:{end_str}",
            f"#AIVideo min_faves:{self.config['min_engagement']} since:{start_str} until:{end_str}",
            f"ChatGPT video min_faves:{self.config['min_engagement']} since:{start_str} until:{end_str}",
        ]

        print(f"Search terms: {len(search_terms)} queries")
        print(f"Date range: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")

        # Prepare Apify input
        run_input = {
            "searchTerms": search_terms,
            "lang": "en",
            "since": start_str,
            "until": end_str,
            "min_faves": self.config['min_engagement'],
            "maxItems": max_items,
        }

        try:
            print(f"\nLaunching Apify actor...")

            # Run the Apify actor
            run = self.apify_client.actor(
                "kaitoeasyapi/twitter-x-data-tweet-scraper-pay-per-result-cheapest"
            ).call(run_input=run_input)

            print(f"✅ Actor completed successfully")
            print(f"Dataset ID: {run['defaultDatasetId']}")

            # Fetch results
            print(f"Fetching results...")
            tweets = []

            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                tweets.append(item)

            print(f"Found {len(tweets)} candidate tweets")

            # Filter out tweets below engagement threshold
            filtered_tweets = [
                t for t in tweets
                if t.get('likeCount', 0) >= self.config['min_engagement']
            ]

            print(f"After engagement filter: {len(filtered_tweets)} tweets with {self.config['min_engagement']}+ likes")

            return filtered_tweets

        except Exception as e:
            print(f"❌ Error running Apify scraper: {e}")
            return []

    def filter_content(self, tweets: List[Dict]) -> List[Dict]:
        """
        Filter tweets based on quality criteria.

        Args:
            tweets: List of tweet data from Apify

        Returns:
            Filtered and ranked list of tweets
        """
        print(f"\nFiltering {len(tweets)} tweets...")

        filtered = []

        for tweet in tweets:
            tweet_id = tweet.get("id")
            author = tweet.get("author", {}).get("userName", "")
            likes = tweet.get("likeCount", 0)

            # Skip if already reposted
            if self._is_already_reposted(str(tweet_id)):
                continue

            # Skip if own account (you can add your username here)
            # if author.lower() == "yourusername":
            #     continue

            # Score the tweet
            score = 0

            # Engagement-based scoring (sweet spot: 1K-5K likes)
            if self.config['sweet_spot_min'] <= likes <= self.config['sweet_spot_max']:
                score += 10
            elif likes < self.config['sweet_spot_min']:
                score += 5
            else:
                score += 3  # Too viral, probably too late

            # Content type priority (based on text content)
            text = tweet.get("text", "").lower()
            if any(term in text for term in ["veo", "sora", "chatgpt", "claude"]):
                score += 5  # Key AI tools
            if any(term in text for term in ["tool", "model", "release", "launched", "dropped"]):
                score += 3  # New releases
            elif any(term in text for term in ["demo", "showcase", "generated", "ai"]):
                score += 2  # Demos

            # Check for media
            if tweet.get("videos"):
                score += 2
            elif tweet.get("photos"):
                score += 1

            tweet["_score"] = score
            filtered.append(tweet)

        # Sort by score (descending)
        filtered.sort(key=lambda x: x["_score"], reverse=True)

        print(f"Filtered to {len(filtered)} high-quality tweets")
        if filtered:
            top = filtered[0]
            print(f"Top tweet: @{top['author']['userName']} with {top['likeCount']} likes (score: {top['_score']})")

        return filtered

    def _download_with_gallery_dl(self, tweet_url: str, tweet_id: str) -> Optional[str]:
        """
        Download media using gallery-dl (preferred method).

        Args:
            tweet_url: Full URL to the tweet
            tweet_id: Tweet ID for filename

        Returns:
            Local file path if successful, None otherwise
        """
        if not shutil.which("gallery-dl"):
            print("  ⚠️  gallery-dl not found in PATH, falling back to direct download")
            return None

        print(f"  Using gallery-dl to download from: {tweet_url}")

        try:
            # Prepare gallery-dl command
            output_template = str(self.media_dir / f"{tweet_id}")

            cmd = [
                "gallery-dl",
                "--no-part",  # don't create .part files
                "--no-mtime",  # don't set file modification time
                "-o", f"filename={tweet_id}.{{extension}}",  # custom filename
                "-d", str(self.media_dir),  # output directory
                tweet_url
            ]

            print(f"  Running: {' '.join(cmd)}")

            # Run gallery-dl with timeout
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.config['download_timeout']
            )

            if result.returncode == 0:
                # Find the downloaded file
                # gallery-dl may create subdirectories (e.g., twitter/username/)
                # First check for files with tweet_id in name recursively
                downloaded_files = list(self.media_dir.rglob(f"*{tweet_id}*"))

                if downloaded_files:
                    # Find the actual media file (not directories)
                    media_files = [f for f in downloaded_files if f.is_file() and f.suffix in ['.mp4', '.jpg', '.png', '.gif', '.webm']]

                    if media_files:
                        # Take the first/largest media file
                        target_file = media_files[0]
                        file_size = target_file.stat().st_size / (1024 * 1024)

                        # Move file to root of media_dir with clean name
                        extension = target_file.suffix
                        new_path = self.media_dir / f"{tweet_id}{extension}"

                        # Move the file
                        shutil.move(str(target_file), str(new_path))
                        print(f"  ✅ Successfully downloaded via gallery-dl: {new_path.name} ({file_size:.2f} MB)")

                        # Clean up empty subdirectories
                        try:
                            for subdir in self.media_dir.iterdir():
                                if subdir.is_dir():
                                    # Recursively check if directory tree is empty
                                    if not any(subdir.rglob("*")):
                                        shutil.rmtree(subdir)
                        except:
                            pass  # Ignore cleanup errors

                        return str(new_path)

                print(f"  ⚠️  gallery-dl completed but no media file found")
                return None

            else:
                print(f"  ⚠️  gallery-dl failed with code {result.returncode}")
                if result.stderr:
                    print(f"  Error: {result.stderr[:200]}")
                return None

        except subprocess.TimeoutExpired:
            print(f"  ⚠️  gallery-dl timed out after {self.config['download_timeout']}s")
            return None
        except Exception as e:
            print(f"  ⚠️  gallery-dl error: {e}")
            return None

    def _download_direct(self, tweet: Dict) -> Optional[str]:
        """
        Download media directly from URLs in tweet data (fallback method).

        Args:
            tweet: Tweet data containing media URLs

        Returns:
            Local file path if successful, None otherwise
        """
        tweet_id = tweet.get("id")

        # Try to get video first, then photos
        media_url = None
        extension = None

        if tweet.get("videos"):
            # Get highest quality video variant
            videos = tweet["videos"]
            if videos:
                video = videos[0]
                variants = video.get("variants", [])
                if variants:
                    # Sort by bitrate (if available) or just take first
                    variants.sort(key=lambda x: x.get("bitrate", 0), reverse=True)
                    media_url = variants[0].get("url")
                    extension = ".mp4"

        elif tweet.get("photos"):
            photos = tweet["photos"]
            if photos:
                media_url = photos[0].get("url")
                extension = ".jpg"

        if not media_url:
            print(f"  ⚠️  No direct media URL available in tweet data")
            return None

        # Download with retries
        for attempt in range(self.config['max_retries']):
            try:
                print(f"  Attempt {attempt + 1}/{self.config['max_retries']}: Downloading from {media_url[:50]}...")

                response = requests.get(media_url, timeout=30, stream=True)
                response.raise_for_status()

                # Save file
                filename = f"{tweet_id}{extension}"
                filepath = self.media_dir / filename

                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                file_size = filepath.stat().st_size / (1024 * 1024)  # MB
                print(f"  ✅ Successfully downloaded via direct method: {filename} ({file_size:.2f} MB)")

                return str(filepath)

            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {e}")
                if attempt < self.config['max_retries'] - 1:
                    time.sleep(2)
                    continue
                else:
                    print(f"  ❌ Failed to download media after {self.config['max_retries']} attempts")
                    return None

        return None

    def download_media(self, tweet: Dict) -> Optional[str]:
        """
        Download media from a tweet using multiple strategies.

        Strategy order:
        1. gallery-dl (if enabled) - Most reliable for X/Twitter videos
        2. Direct download from Apify URLs (fallback)
        3. Manual download notification (if all else fails)

        Args:
            tweet: Tweet data containing media URLs and tweet URL

        Returns:
            Local file path if successful, None otherwise
        """
        tweet_id = tweet.get("id")
        tweet_url = tweet.get("url", "")

        print(f"\nAttempting to download media for tweet {tweet_id}...")

        # Strategy 1: Try gallery-dl first (preferred)
        if self.config.get('use_gallery_dl', True) and tweet_url:
            media_path = self._download_with_gallery_dl(tweet_url, str(tweet_id))
            if media_path:
                return media_path
            print(f"  gallery-dl failed, trying direct download...")

        # Strategy 2: Try direct download from Apify URLs
        media_path = self._download_direct(tweet)
        if media_path:
            return media_path

        # Strategy 3: All automated methods failed
        print(f"  ⚠️  All automated download methods failed")
        print(f"  Tweet URL: {tweet_url if tweet_url else 'N/A'}")
        print(f"  You can manually download media from the tweet URL")
        return None

    async def generate_commentary(self, tweet: Dict) -> str:
        """
        Generate Min Choi style commentary for a tweet using GPT-4o.

        Args:
            tweet: Original tweet data

        Returns:
            Generated commentary with attribution
        """
        original_text = tweet.get("text", "")
        original_author = tweet.get("author", {}).get("userName", "unknown")

        print(f"\nGenerating Min Choi style commentary...")
        print(f"Original author: @{original_author}")

        # Create agent with Min Choi style instructions
        agent = Agent(
            name="Min Choi Commentary Generator",
            model=self.model,
            instructions=f"""
            You are writing viral X posts about AI in Min Choi's style.

            ORIGINAL TWEET: {original_text}
            ORIGINAL AUTHOR: @{original_author}

            Write a SHORT reaction (max 200 characters for main text, not counting attribution).

            MUST START WITH one of these hooks (choose the most appropriate):
            - "This is wild."
            - "We are cooked >/"
            - "[Tool/Company] just dropped [feature]"
            - "[Tool] absolutely cooked with [feature]"
            - "Wow [Tool] continue to impress."

            STYLE RULES:
            - Excited educator, never corporate
            - Genuine enthusiasm, not cynical
            - Short and punchy (max 200 chars for main text)
            - Use "wild", "insane", "crazy", "cooked", "100% AI", "not real" appropriately
            - Add >/ emoji ONLY if genuinely mind-blowing (max 1-2 emojis total)
            - MUST be completely different from original text (don't copy)
            - Focus on WHY it matters, not just WHAT it is

            AVOID:
            - Corporate jargon
            - Being negative or cynical
            - Multiple emojis in a row
            - "Check this out" / "Link in bio"
            - Copying exact text from original
            - Excessive hashtags

            FORMAT:
            [Your commentary - max 200 chars]

            via @{original_author}

            OUTPUT ONLY THE COMPLETE TEXT (commentary + attribution). NO QUOTES OR EXPLANATION.
            The attribution line "via @{original_author}" MUST be included at the end.
            """,
        )

        result = await Runner.run(
            agent,
            f"Generate a Min Choi style commentary for this tweet. Return the complete text including attribution."
        )

        commentary = result.final_output.strip()

        # Ensure attribution is included
        if f"via @{original_author}" not in commentary:
            commentary += f"\n\nvia @{original_author}"

        print(f"\nGenerated commentary ({len(commentary)} chars):")
        print(f"  {commentary}")

        return commentary

    async def curate_content(self, limit: int = 1) -> List[Dict]:
        """
        Main curation workflow: search, filter, download, and generate commentary.

        Args:
            limit: Number of posts to curate (default: 1)

        Returns:
            List of curated content dictionaries with text and media paths
        """
        # Step 1: Search for viral content (defaults to config max_tweets_per_search = 20)
        tweets = await self.search_viral_content()

        if not tweets:
            print("\nNo tweets found matching criteria")
            return []

        # Step 2: Filter content
        filtered_tweets = self.filter_content(tweets)

        if not filtered_tweets:
            print("\nNo tweets passed filtering criteria")
            return []

        # Step 3: Process top tweets
        curated = []

        for tweet in filtered_tweets[:limit]:
            print(f"\n{'='*60}")
            print(f"Processing tweet from @{tweet['author']['userName']}")
            print(
                f"Likes: {tweet['likeCount']} | Retweets: {tweet['retweetCount']}")
            print(f"Original: {tweet.get('text', '')[:100]}...")

            # Attempt to download media (may not be available via Apify)
            media_path = self.download_media(tweet)

            # Generate commentary regardless of media download status
            commentary = await self.generate_commentary(tweet)

            # Prepare result
            result = {
                "commentary": commentary,
                "media_path": media_path if media_path else None,
                "original_tweet_id": tweet["id"],
                "original_author": tweet["author"]["userName"],
                "original_url": tweet.get("url", ""),
                "tweet_url": tweet.get("url", ""),  # For manual media download
                "engagement": {
                    "likes": tweet.get("likeCount", 0),
                    "retweets": tweet.get("retweetCount", 0),
                    "replies": tweet.get("replyCount", 0),
                },
                "curated_at": datetime.now().isoformat()
            }

            # Track in database
            tweet["media_url"] = media_path if media_path else "manual_download_required"
            tweet["our_commentary"] = commentary
            self._track_reposted_content(tweet)

            curated.append(result)

            if media_path:
                print(f"  ✅ Successfully curated with media!")
            else:
                print(f"  ✅ Successfully curated (manual media download required)")
                print(f"     Download from: {tweet.get('url', '')}")

        return curated

    async def run(self, limit: int = 1):
        """
        Main execution method - curate viral AI content.

        Args:
            limit: Number of posts to curate (default: 1)

        Returns:
            List of curated content
        """
        print(f"Content Curator Agent initializing...")
        print(f"Using model: {self.model}")
        print(f"Target: {limit} curated post(s)")
        print(f"Media directory: {self.media_dir}")
        print(f"Database: {self.db_file}\n")

        start_time = time.time()

        try:
            curated = await self.curate_content(limit=limit)

            print(f"\n{'='*60}")
            print(f"CURATION COMPLETE")
            print(f"{'='*60}")
            print(f"Successfully curated: {len(curated)} post(s)")
            print(f"Duration: {time.time() - start_time:.2f}s\n")

            for idx, item in enumerate(curated, 1):
                print(f"\n--- Curated Post #{idx} ---")
                print(f"Commentary:\n{item['commentary']}\n")
                print(f"Media: {item['media_path']}")
                print(f"Original: @{item['original_author']}")
                print(f"Engagement: {item['engagement']['likes']} likes")

            return curated

        except Exception as e:
            print(f"\nERROR: Curation failed: {e}")
            import traceback
            traceback.print_exc()
            return []

    def cleanup_old_media(self, days: int = 7):
        """
        Clean up media files older than specified days.

        Args:
            days: Number of days to keep files
        """
        cutoff_time = time.time() - (days * 86400)
        cleaned = 0

        for file_path in self.media_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                cleaned += 1

        if cleaned > 0:
            print(f"Cleaned up {cleaned} old media file(s)")


async def main():
    """
    Example usage of the Content Curator agent.

    You can specify a different model:
    - agent = ContentCuratorAgent(model="gpt-4o")  # Best quality (recommended)
    - agent = ContentCuratorAgent(model="gpt-5")
    - agent = ContentCuratorAgent(model="gpt-5-mini")
    """
    agent = ContentCuratorAgent(model="gpt-5-mini")

    # Curate 1 viral post (conservative to save quota)
    curated = await agent.run(limit=1)

    # Optional: Clean up old media files
    # agent.cleanup_old_media(days=7)

    return curated


if __name__ == "__main__":
    asyncio.run(main())
