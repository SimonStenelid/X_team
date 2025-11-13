# Orchestrator Agent

## Overview
The Orchestrator Agent is the brain of your automated X account system. It coordinates all sub-agents (News Agent, Meme Lord, Image Generator, Content Curator), makes intelligent decisions about what to post when, ensures content variety, prevents duplicates, and maintains a consistent once-per-day posting schedule.

## Core Responsibilities

### 1. Agent Coordination
- Decide which agent to activate based on strategy
- Pass instructions to sub-agents
- Receive content from sub-agents
- Approve or reject generated content

### 2. Scheduling
- Post exactly once per day
- Vary posting times (appear human)
- Choose optimal time slots for engagement
- Track last post time

### 3. Content Variety Management
- Prevent posting same content type repeatedly
- Balance content mix across the week
- Track content history
- Ensure diverse posting pattern

### 4. Duplicate Prevention
- Check if content already posted
- Detect similar topics/themes
- Prevent reposting scraped content
- Maintain content database

### 5. Quality Control
- Validate generated content
- Ensure posts meet quality standards
- Check character limits
- Verify media attachments

## Decision-Making Framework

### Daily Content Selection Process
```
START: Every day at random time (8am-10pm)
  ↓
Check: What did we post yesterday?
  ↓
Calculate: Content type probabilities
  ↓
Roll: Select content type for today
  ↓
Call: Appropriate agent
  ↓
Review: Generated content
  ↓
Check: Duplicates & quality
  ↓
Approve: Post or regenerate
  ↓
Post: Upload to X
  ↓
Log: Store in database
  ↓
END: Schedule next post (24h + variance)
```

## Content Mix Strategy

### Target Distribution (Weekly)
```
News Posts:     35%  (2-3 per week)
Curated Posts:  30%  (2-3 per week)
Meme Posts:     20%  (1-2 per week)
Image Posts:    15%  (1 per week)
```

### Daily Decision Algorithm

**Base Probabilities:**
```python
base_weights = {
    "news": 0.35,
    "curator": 0.30,
    "meme": 0.20,
    "image": 0.15
}
```

**Adjustment Rules:**
1. **Recency Penalty**: If content type posted yesterday → reduce weight by 70%
2. **Repetition Penalty**: If content type posted 2 days in a row → weight = 0
3. **Boost Underused**: If content type not posted in 4+ days → increase weight by 50%
4. **Weekly Balance**: If over quota for week → reduce weight by 50%

**Example:**
```
Day 1: Posted News
Day 2 probabilities:
  - News: 0.35 × 0.3 = 0.105 (posted yesterday)
  - Curator: 0.30 × 1.0 = 0.300 (normal)
  - Meme: 0.20 × 1.0 = 0.200 (normal)
  - Image: 0.15 × 1.0 = 0.150 (normal)
  
Normalize and select → Curator has highest probability
```

## Posting Schedule

### Time Selection

**Optimal Time Windows (Stockholm timezone):**
```
Morning:    08:00 - 10:00  (30% chance)
Lunch:      12:00 - 13:00  (20% chance)
Afternoon:  15:00 - 17:00  (10% chance)
Evening:    18:00 - 20:00  (30% chance)
Night:      21:00 - 22:00  (10% chance)
```

**Randomization:**
- Pick time window based on probabilities above
- Add random variance: ± 15-30 minutes
- Never post at exact same time two days in row
- Track posting patterns to appear human

**Example Schedule:**
```
Monday:    09:23  (Morning)
Tuesday:   19:47  (Evening)
Wednesday: 12:18  (Lunch)
Thursday:  20:35  (Evening)
Friday:    08:51  (Morning)
Saturday:  14:22  (Afternoon)
Sunday:    21:09  (Night)
```

## Duplicate Detection System

### Three-Layer Check

**Layer 1: Exact Match**
- Compare text content with all previous posts
- Hash comparison for exact duplicates
- Check media URLs/hashes

**Layer 2: Semantic Similarity**
- Use embeddings to detect similar content
- Threshold: >85% similarity = duplicate
- Compare last 30 days of posts

**Layer 3: Topic Overlap**
- Extract key entities (tool names, companies)
- If same entities + same day = potential duplicate
- Example: Two posts about "Veo 2" on same day

### Duplicate Database Schema
```python
{
  "post_id": "uuid",
  "posted_at": "2024-01-15T09:23:00Z",
  "content_type": "news",
  "text": "This is wild. Veo 2...",
  "text_hash": "abc123...",
  "embedding": [0.123, 0.456, ...],
  "entities": ["Veo 2", "Google", "AI video"],
  "media_url": "https://...",
  "media_hash": "def456...",
  "agent_used": "curator",
  "engagement": {
    "likes": 0,
    "retweets": 0,
    "views": 0
  }
}
```

## Agent Interaction Protocols

### 1. News Agent

**When to Call:**
- Content type selected: "news"
- Last news post >2 days ago (optional boost)

**Instructions to Send:**
```python
{
  "task": "find_and_post_news",
  "requirements": {
    "recency": "last 48 hours",
    "min_relevance": "high",
    "avoid_topics": recent_topics_list,
    "style": "min_choi"
  }
}
```

**Expected Response:**
```python
{
  "success": true,
  "content": {
    "text": "This is wild. OpenAI just...",
    "media": null,
    "source_url": "https://...",
    "topic": "OpenAI GPT-5"
  }
}
```

### 2. Meme Lord Agent

**When to Call:**
- Content type selected: "meme"
- Need lighter content (after 2 news posts)

**Instructions to Send:**
```python
{
  "task": "generate_meme",
  "requirements": {
    "topic": "AI",
    "max_length": 200,
    "style": "funny_relatable",
    "avoid": recent_meme_topics
  }
}
```

**Expected Response:**
```python
{
  "success": true,
  "content": {
    "text": "AI in 2025: generates entire movies\nAlso AI: can't count the Rs in strawberry",
    "media": null
  }
}
```

### 3. Image Generator Agent

**When to Call:**
- Content type selected: "image"
- Not posted image in 5+ days

**Instructions to Send:**
```python
{
  "task": "generate_image_post",
  "requirements": {
    "theme": "AI_futuristic",
    "style": "3D_render",
    "caption_length": 50,
    "avoid_styles": recent_image_styles
  }
}
```

**Expected Response:**
```python
{
  "success": true,
  "content": {
    "text": "The future of AI agents 🤖",
    "media": "path/to/image.png",
    "media_type": "image"
  }
}
```

### 4. Content Curator Agent

**When to Call:**
- Content type selected: "curator"
- Viral content available (check first)

**Instructions to Send:**
```python
{
  "task": "find_and_curate",
  "requirements": {
    "min_engagement": 1000,
    "max_age_hours": 24,
    "avoid_sources": already_curated_ids,
    "content_types": ["video"]
  }
}
```

**Expected Response:**
```python
{
  "success": true,
  "content": {
    "text": "This is wild. Veo 2 dance videos...\n\nvia @minchoi",
    "media": "path/to/video.mp4",
    "media_type": "video",
    "original_tweet_id": "1234567890"
  }
}
```

## Quality Control Checks

### Before Posting, Validate:

**Content Validation:**
- [ ] Text length: 1-280 characters
- [ ] No broken formatting
- [ ] Proper grammar and spelling
- [ ] Contains required elements (hook, content, credit if curated)
- [ ] Style matches Min Choi guidelines

**Media Validation:**
- [ ] File exists and readable
- [ ] File size < 512MB (X limit)
- [ ] Video length < 2:20 (X free tier limit)
- [ ] Image dimensions acceptable (min 600px width)
- [ ] No corruption or errors

**Duplicate Check:**
- [ ] Not exact match with previous posts
- [ ] Not semantically similar (>85%)
- [ ] Not same topic as yesterday
- [ ] Not curated from already-posted source

**Engagement Prediction:**
- [ ] Has viral potential (score >6/10)
- [ ] Fits current trends
- [ ] Appropriate for time of day
- [ ] Aligns with account theme

### If Validation Fails:
1. **First attempt**: Ask agent to regenerate
2. **Second attempt**: Try different content type
3. **Third attempt**: Use backup content (pre-generated)
4. **Last resort**: Skip today, post tomorrow

## Error Handling

### Common Scenarios

**1. Agent Returns Low-Quality Content**
```
→ Request regeneration (max 2 retries)
→ If still poor, switch to backup agent
→ Log quality issue for review
```

**2. No Viral Content Available (Curator)**
```
→ Switch to News Agent instead
→ Log: "No viral content found"
→ Adjust curator parameters for next time
```

**3. API Rate Limits Hit**
```
→ Wait and retry after cooldown
→ If urgent, use backup content
→ Reschedule post for later time window
```

**4. Duplicate Detected Late**
```
→ Abort post immediately
→ Generate new content
→ Update duplicate database
→ Log incident
```

**5. Media Download Fails (Curator)**
```
→ Retry download 3x
→ If fails, skip this content
→ Move to next viral post
→ Or switch to different agent
```

## State Management

### Track These Variables:
```python
orchestrator_state = {
    # History
    "last_post_time": "2024-01-15T09:23:00Z",
    "last_7_days_posts": [
        {"type": "news", "date": "2024-01-15"},
        {"type": "curator", "date": "2024-01-14"},
        {"type": "meme", "date": "2024-01-13"},
        # ...
    ],
    
    # Weekly counters
    "week_counts": {
        "news": 2,
        "curator": 2,
        "meme": 1,
        "image": 0
    },
    
    # Recent topics (avoid repetition)
    "recent_topics": [
        "Veo 2",
        "GPT-5",
        "Claude Sonnet"
    ],
    
    # Recent sources (for curator)
    "curated_tweet_ids": [
        "1234567890",
        "0987654321"
    ],
    
    # Performance tracking
    "engagement_by_type": {
        "news": {"avg_likes": 45, "avg_rt": 12},
        "curator": {"avg_likes": 123, "avg_rt": 34},
        "meme": {"avg_likes": 67, "avg_rt": 18},
        "image": {"avg_likes": 89, "avg_rt": 22}
    },
    
    # Scheduling
    "next_post_scheduled": "2024-01-16T19:47:00Z",
    "preferred_time_windows": ["morning", "evening"]
}
```

### State Persistence
- Save state to JSON file after each post
- Load state on startup
- Backup state daily
- Clear old data (>30 days) weekly

## Decision Tree
```
┌─────────────────────┐
│  Time to Post?      │
│  (Check schedule)   │
└──────────┬──────────┘
           │
     ┌─────▼─────┐
     │ Load State│
     │ & History │
     └─────┬─────┘
           │
     ┌─────▼──────────┐
     │ Calculate      │
     │ Content Type   │
     │ Probabilities  │
     └─────┬──────────┘
           │
     ┌─────▼─────┐
     │  Roll Dice │
     │  (Weighted)│
     └─────┬─────┘
           │
    ┌──────┴──────┬──────────┬──────────┐
    │             │          │          │
    v             v          v          v
┌───────┐   ┌─────────┐  ┌─────────┐  ┌──────────┐
│ News  │   │  Curator│  │  Meme   │  │  Image   │
│ Agent │   │  Agent  │  │  Lord   │  │ Generator│
└───┬───┘   └────┬────┘  └────┬────┘  └────┬─────┘
    │            │            │            │
    └────────────┴────────────┴────────────┘
                 │
           ┌─────▼─────┐
           │  Content  │
           │ Received  │
           └─────┬─────┘
                 │
           ┌─────▼──────┐
           │  Quality   │
           │  Control   │
           └─────┬──────┘
                 │
          ┌──────▼──────┐
          │ Duplicate?  │
          └─┬────────┬──┘
      Yes  │        │ No
           │        │
    ┌──────▼──┐     │
    │Regenerate│     │
    │or Skip   │     │
    └──────────┘     │
                     │
              ┌──────▼──────┐
              │  Post to X  │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  Log & Save │
              └──────┬──────┘
                     │
              ┌──────▼──────┐
              │  Schedule   │
              │  Next Post  │
              └─────────────┘
```

## Performance Optimization

### Weekly Review (Automatic)
Every Sunday, analyze:
- Which content type got most engagement?
- Which time slots performed best?
- Any patterns in viral posts?
- Adjust weights accordingly

**Example Adjustment:**
```python
# If curator posts consistently get 2x engagement
if curator_avg_engagement > (overall_avg * 2):
    base_weights["curator"] += 0.05
    base_weights["meme"] -= 0.05  # Rebalance
```

### Learning Loop
```
Post → Track Engagement → Analyze Pattern → 
Adjust Weights → Apply Next Week → Repeat
```

## Monitoring & Alerts

### Daily Health Checks
- [ ] Post went out successfully
- [ ] No errors in logs
- [ ] State file updated
- [ ] All agents responding
- [ ] Database size reasonable

### Alert Triggers
- ⚠️ Failed to post 2 days in a row
- ⚠️ Same content type 3 days straight
- ⚠️ Engagement dropped >50% for week
- ⚠️ Duplicate posted (shouldn't happen)
- ⚠️ API errors repeatedly

## Backup Strategies

### Content Backup
Keep 5-10 pre-generated posts ready:
- 2 news posts (evergreen AI topics)
- 2 memes (general AI humor)
- 1 image post
- Use if all agents fail

### Schedule Backup
If posting fails:
- Retry in 1 hour
- Then retry in 4 hours
- Then skip to next day
- Never spam retries

## Configuration

### Orchestrator Settings
```python
ORCHESTRATOR_CONFIG = {
    # Posting
    "posts_per_day": 1,
    "posting_times": {
        "morning": (8, 10),    # (start, end) hours
        "lunch": (12, 13),
        "afternoon": (15, 17),
        "evening": (18, 20),
        "night": (21, 22)
    },
    "time_variance_minutes": 30,
    
    # Content Mix
    "base_weights": {
        "news": 0.35,
        "curator": 0.30,
        "meme": 0.20,
        "image": 0.15
    },
    "max_same_type_streak": 2,  # Max same type in a row
    
    # Quality Control
    "min_quality_score": 6,      # Out of 10
    "max_regeneration_attempts": 2,
    "duplicate_similarity_threshold": 0.85,
    
    # History
    "track_days": 30,            # Days to keep in history
    "recent_topics_size": 10,    # Track last N topics
    
    # Error Handling
    "max_retries": 3,
    "retry_delay_minutes": 60,
    "use_backup_after_fails": 2
}
```

## Daily Workflow Example
```
Day 1 (Monday):
09:23 → News post about GPT-5 release
       (morning slot, news agent)
       
Day 2 (Tuesday):
19:47 → Curated Veo 2 video
       (evening slot, curator agent)
       (News posted yesterday, reduced weight)
       
Day 3 (Wednesday):
12:18 → Meme about AI training
       (lunch slot, meme lord)
       (Variety: last 2 posts serious)
       
Day 4 (Thursday):
20:35 → Curated Sora demo
       (evening slot, curator agent)
       
Day 5 (Friday):
08:51 → News about Claude update
       (morning slot, news agent)
       
Day 6 (Saturday):
14:22 → AI-generated image + caption
       (afternoon slot, image generator)
       (Haven't posted image all week)
       
Day 7 (Sunday):
21:09 → Meme about debugging AI
       (night slot, meme lord)
       
Weekly Analysis:
- News: 2/7 (28.5%) ✅ target 35%
- Curator: 2/7 (28.5%) ✅ target 30%
- Meme: 2/7 (28.5%) ⚠️ target 20% (slight over)
- Image: 1/7 (14.2%) ✅ target 15%

Adjustment: Slightly reduce meme weight next week
```

## Success Metrics

### Track Weekly:
- Total posts: 7
- Content variety: No more than 2 same type in row ✅
- Duplicate rate: 0% ✅
- Average engagement per post
- Follower growth
- Best performing content type
- Optimal posting times

### Monthly Goals:
- Follower growth: +5-10% per month
- Engagement rate: 5-10% (likes/followers)
- Zero duplicates posted
- 100% posting consistency (7 posts per week)

## Edge Cases

### Holidays / Special Events
- Adjust posting to relevant content
- Example: OpenAI Dev Day → prioritize news
- Override weights temporarily

### Viral Content Drought
- If curator finds nothing >3 days
- Increase news and meme weights
- Return to normal when viral content returns

### Engagement Spike
- If post goes viral (>1K likes)
- Analyze what worked
- Try similar content next week
- Don't force repetition

### Agent Downtime
- If agent consistently fails (>3 days)
- Redistribute weight to working agents
- Alert for manual intervention
- Use backup content if critical

## Maintenance Tasks

### Daily (Automated):
- Post content
- Update state
- Check agent health
- Log engagement

### Weekly (Automated):
- Analyze performance
- Adjust weights
- Clean old data
- Backup database

### Monthly (Manual Review):
- Review strategy effectiveness
- Update agent prompts if needed
- Check for emerging trends
- Adjust posting times if optimal slots changed

---

## Quick Reference: Orchestrator Checklist

Every time orchestrator runs:

1. [ ] Load current state and history
2. [ ] Calculate time to post
3. [ ] Determine content type (weighted random)
4. [ ] Call appropriate agent with context
5. [ ] Receive and validate content
6. [ ] Check for duplicates (3 layers)
7. [ ] Score content quality (>6/10)
8. [ ] Approve or regenerate
9. [ ] Post to X
10. [ ] Update database and state
11. [ ] Schedule next post (24h + variance)
12. [ ] Log everything

If ANY step fails → Use backup strategy → Never spam or break!