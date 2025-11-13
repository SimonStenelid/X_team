# Orchestrator Agent - User Guide

## Overview

The Orchestrator Agent is the brain of your automated X posting system. It coordinates all sub-agents, manages content variety, prevents duplicates, and ensures a consistent posting schedule.

## Features Implemented

✅ **Agent Coordination** - Manages News Hunter, Meme Lord, Image Generator, and Content Curator
✅ **Smart Scheduling** - Posts once per day at varied times (Stockholm timezone)
✅ **Content Variety** - Weighted probability system with penalties and boosts
✅ **Duplicate Detection** - 3-layer system (exact match, semantic similarity, topic overlap)
✅ **Quality Control** - Validates content before posting
✅ **X Integration** - Full Tweepy support for posting with media
✅ **State Management** - Tracks history, engagement, and scheduling
✅ **Learning System** - Weekly analysis and weight optimization
✅ **Error Handling** - Retry logic and backup content strategies

## Installation

1. **Install dependencies:**
```bash
cd /Users/simonstenelid/Desktop/X_team
uv sync
```

This will install the new dependencies:
- `pytz` - For Stockholm timezone handling
- `requests` - For HTTP requests (if not already installed)

2. **Configure X API credentials in `.env`:**
```bash
# X/Twitter API credentials
X_API_KEY=your_api_key
X_API_SECRET=your_api_secret
X_ACCESS_TOKEN=your_access_token
X_ACCESS_TOKEN_SECRET=your_access_token_secret
X_BEARER_TOKEN=your_bearer_token
```

## Usage

### Testing (Dry-Run Mode)

Run the orchestrator WITHOUT actually posting to X:

```bash
python test_orchestrator.py
```

This will:
- Show you a test menu
- Default to dry-run mode (safe)
- Let you test individual components

Or run directly:

```python
from Agentos.orchestrator import OrchestratorAgent
import asyncio

async def main():
    orchestrator = OrchestratorAgent(dry_run=True)
    await orchestrator.run_daily()

asyncio.run(main())
```

### Production Mode

When you're ready to post for real:

```python
from Agentos.orchestrator import OrchestratorAgent
import asyncio

async def main():
    # dry_run=False means it WILL post to X
    orchestrator = OrchestratorAgent(dry_run=False)
    await orchestrator.run_daily()

asyncio.run(main())
```

### Scheduling with Cron

To run daily automatically, add to your crontab:

```bash
# Run orchestrator every hour (it will only post when scheduled)
0 * * * * cd /Users/simonstenelid/Desktop/X_team && /Users/simonstenelid/Desktop/X_team/.venv/bin/python -c "from Agentos.orchestrator import OrchestratorAgent; import asyncio; asyncio.run(OrchestratorAgent(dry_run=False).run_daily())"
```

Or create a dedicated script:

```bash
# daily_post.py
import asyncio
from Agentos.orchestrator import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent(dry_run=False)
    await orchestrator.run_daily()

if __name__ == "__main__":
    asyncio.run(main())
```

Then cron:
```bash
0 * * * * cd /Users/simonstenelid/Desktop/X_team && /Users/simonstenelid/Desktop/X_team/.venv/bin/python daily_post.py >> /Users/simonstenelid/Desktop/X_team/Agentos/logs/cron.log 2>&1
```

## How It Works

### Daily Workflow

```
1. Check if it's time to post
   ├─ No → Exit
   └─ Yes → Continue

2. Load state (history, counters, schedule)

3. Select content type (weighted random)
   ├─ News: 35% base probability
   ├─ Curator: 30%
   ├─ Meme: 20%
   └─ Image: 15%
   (Adjusted by penalties/boosts)

4. Call selected agent
   ├─ Generate content
   └─ Apply retries if needed

5. Validate content
   ├─ Check character limit
   ├─ Check media validity
   └─ Score quality (min 6/10)

6. Check for duplicates
   ├─ Layer 1: Exact text match
   ├─ Layer 2: Semantic similarity
   └─ Layer 3: Topic overlap

7. Post to X
   ├─ Upload media if present
   └─ Create tweet

8. Update state & database
   ├─ Save post to database
   ├─ Update history
   ├─ Increment counters
   └─ Schedule next post (24h + variance)
```

### Content Type Selection Algorithm

**Base Weights:**
- News: 35%
- Curator: 30%
- Meme: 20%
- Image: 15%

**Adjustment Rules:**

1. **Recency Penalty**: Posted yesterday → weight × 0.3
2. **Repetition Penalty**: Posted 2 days in row → weight = 0
3. **Boost Underused**: Not posted in 4+ days → weight × 1.5
4. **Weekly Balance**: Over quota for week → weight × 0.5

**Example:**
```
Day 1: Posted News
Day 2 Selection:
  - News: 0.35 × 0.3 = 0.105 (recency penalty)
  - Curator: 0.30 × 1.0 = 0.300 (normal)
  - Meme: 0.20 × 1.0 = 0.200 (normal)
  - Image: 0.15 × 1.0 = 0.150 (normal)

Result: Curator has highest probability
```

### Scheduling System

**Time Windows (Stockholm timezone):**

| Window | Hours | Probability |
|--------|-------|-------------|
| Morning | 08:00-10:00 | 30% |
| Lunch | 12:00-13:00 | 20% |
| Afternoon | 15:00-17:00 | 10% |
| Evening | 18:00-20:00 | 30% |
| Night | 21:00-22:00 | 10% |

**Variance:** ±30 minutes added for human-like behavior

**Example Schedule:**
```
Monday:    09:23 (Morning)
Tuesday:   19:47 (Evening)
Wednesday: 12:18 (Lunch)
Thursday:  20:35 (Evening)
Friday:    08:51 (Morning)
```

## Database Structure

### State Database (`orchestrator_state.json`)

```json
{
  "last_post_time": "2024-01-15T09:23:00+01:00",
  "last_7_days_posts": [
    {"type": "news", "date": "2024-01-15", "tweet_id": "123..."},
    {"type": "curator", "date": "2024-01-14", "tweet_id": "456..."}
  ],
  "week_counts": {
    "news": 2,
    "curator": 2,
    "meme": 1,
    "image": 0
  },
  "recent_topics": ["GPT-5", "Veo2", "Claude"],
  "curated_tweet_ids": ["1234567890"],
  "engagement_by_type": {
    "news": {"avg_likes": 45, "avg_rt": 12, "count": 5}
  },
  "next_post_scheduled": "2024-01-16T19:47:00+01:00",
  "week_start_date": "2024-01-15"
}
```

### Posts Database (`posts_database.json`)

```json
{
  "posts": [
    {
      "post_id": "tweet_id_123",
      "posted_at": "2024-01-15T09:23:00+01:00",
      "content_type": "news",
      "text": "This is wild. OpenAI just...",
      "text_hash": "abc123...",
      "embedding": [0.123, 0.456, ...],
      "media_url": "path/to/media.mp4",
      "agent_used": "news_hunter",
      "metadata": {...},
      "quality_score": 8.5,
      "engagement": {
        "likes": 0,
        "retweets": 0,
        "views": 0
      }
    }
  ]
}
```

## Duplicate Detection

### Layer 1: Exact Match
- Computes SHA256 hash of text
- Checks against all previous posts
- Catches identical reposts

### Layer 2: Semantic Similarity
- Uses OpenAI embeddings (`text-embedding-3-small`)
- Computes cosine similarity
- Threshold: 0.85 (85% similarity = duplicate)
- Checks last 30 days of posts

### Layer 3: Topic Overlap
- For curated content only
- Checks if same source tweet already posted
- Prevents reposting same viral content

## Configuration

All configuration is in the `OrchestratorAgent.__init__()` method:

```python
self.config = {
    # Posting
    "posts_per_day": 1,
    "time_variance_minutes": 30,

    # Content Mix
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
```

## Error Handling

### Content Generation Failures

1. **First attempt fails** → Retry with same agent (up to 2 retries)
2. **All retries fail** → Use backup content
3. **Backup fails** → Abort, log error, try next scheduled time

### Duplicate Detection

- If duplicate detected on first attempt → Regenerate
- If duplicate on all attempts → Abort, don't post
- Prevents accidental reposts

### API Failures

- Twitter API errors are logged
- Post attempt fails gracefully
- Next scheduled time remains
- Can retry on next hourly check

## Backup Content

Located at: `/Users/simonstenelid/Desktop/X_team/Agentos/backup_content.json`

```json
{
  "news": [
    "AI agents are transforming how we work...",
    "New AI models dropping every week..."
  ],
  "meme": [
    "me: automates everything\nalso me: debugs for 10 hours",
    "AI in 2025: generates movies\nAlso AI: can't count Rs"
  ],
  "curator": [],
  "image": []
}
```

**Add your own backup content** to ensure posting continues even if all agents fail.

## Weekly Analysis

Run weekly to optimize performance:

```python
await orchestrator.run_weekly_analysis()
```

This:
- Analyzes engagement by content type
- Updates average likes/retweets
- Helps identify best-performing content
- Can be used to manually adjust weights

## Logs

Logs are saved to: `/Users/simonstenelid/Desktop/X_team/Agentos/logs/`

Format: `orchestrator_YYYYMMDD.log`

Each log contains:
- Timestamp
- Content type selection decisions
- Agent calls and responses
- Validation results
- Duplicate checks
- Posting success/failure
- State updates

## Monitoring

### Daily Health Checks

✅ Post went out successfully
✅ No errors in logs
✅ State file updated
✅ All agents responding
✅ Database size reasonable

### Alert Triggers

⚠️ Failed to post 2 days in a row
⚠️ Same content type 3 days straight
⚠️ Duplicate posted (shouldn't happen)
⚠️ API errors repeatedly

## Troubleshooting

### Orchestrator not posting

1. Check if it's the scheduled time:
   ```python
   state = orchestrator.load_state()
   print(state["next_post_scheduled"])
   ```

2. Check logs for errors
3. Verify X API credentials
4. Run in dry-run mode to test logic

### Content quality issues

1. Increase `min_quality_score` threshold
2. Check individual agent outputs
3. Review recent posts in database

### Too many duplicates detected

1. Lower `duplicate_similarity_threshold` (currently 0.85)
2. Check if embeddings are being generated
3. Review semantic similarity scores in logs

### Wrong content mix

1. Check `week_counts` in state
2. Verify weight adjustment logic is working
3. Manually adjust `base_weights` if needed

## Advanced Usage

### Custom Time Windows

Edit `posting_times` in config:

```python
"posting_times": {
    "morning": {"hours": (7, 9), "probability": 0.40},
    "evening": {"hours": (19, 21), "probability": 0.60}
}
```

### Adjust Content Mix

Change `base_weights`:

```python
"base_weights": {
    "news": 0.40,     # More news
    "curator": 0.35,  # More curated
    "meme": 0.15,     # Less memes
    "image": 0.10     # Less images
}
```

### Manual Posting

Force a specific content type:

```python
orchestrator = OrchestratorAgent(dry_run=True)
state = orchestrator.load_state()

# Override selection
content = await orchestrator.call_agent("news", state)
# ... validate, check duplicates, post
```

## Integration with Sub-Agents

The orchestrator seamlessly integrates with existing agents:

- **News Hunter** (`news_hunter.py`) - No changes needed
- **Meme Lord** (`meme_lord.py`) - No changes needed
- **Image Generator** (`image_generator.py`) - No changes needed
- **Content Curator** (`content_curator.py`) - Shares duplicate tracking

All agents are lazy-loaded (created on first use) to minimize initialization overhead.

## Success Metrics

Track these weekly:

📊 Total posts: 7 per week
📊 Content variety: No more than 2 same type in row
📊 Duplicate rate: 0%
📊 Average engagement per post
📊 Follower growth
📊 Best performing content type
📊 Optimal posting times

## Next Steps

1. **Test in dry-run mode** extensively
2. **Add your X API credentials** to `.env`
3. **Customize backup content** for your niche
4. **Run first production post** manually
5. **Set up cron job** for automation
6. **Monitor logs** daily for first week
7. **Run weekly analysis** to optimize
8. **Adjust weights** based on engagement

---

## Quick Start Checklist

- [ ] Install dependencies (`uv sync`)
- [ ] Add X API credentials to `.env`
- [ ] Test with `python test_orchestrator.py`
- [ ] Review generated state/database files
- [ ] Customize backup content if desired
- [ ] Run first production post
- [ ] Set up cron job for daily automation
- [ ] Monitor for first week

---

**Questions or Issues?** Check the logs first, then review this guide. The orchestrator is designed to be self-healing and will gracefully handle most errors.
