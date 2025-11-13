# Orchestrator Quick Start Guide

## ✅ Installation Complete!

Dependencies have been installed successfully. The orchestrator is ready to use.

## 🧪 Testing (Completed)

The orchestrator has been tested and is working correctly:
- ✅ State management
- ✅ Content type selection
- ✅ Agent coordination
- ✅ Duplicate detection
- ✅ Quality validation
- ✅ Scheduling system

## 📂 Files Created

```
/Agentos/
├── orchestrator.py              # Main orchestrator agent
├── orchestrator_db/             # Databases
│   ├── orchestrator_state.json  # State tracking
│   └── posts_database.json      # Posts with embeddings
├── logs/                        # Daily logs
│   └── orchestrator_YYYYMMDD.log
└── backup_content.json          # Backup posts

/test_orchestrator.py            # Interactive test script
/ORCHESTRATOR_GUIDE.md           # Complete documentation
/QUICK_START.md                  # This file
```

## 🚀 How to Use

### 1. Test in Dry-Run Mode (Safe)

```bash
# Interactive test menu
/Users/simonstenelid/Desktop/X_team/.venv/bin/python test_orchestrator.py

# Or directly in Python
/Users/simonstenelid/Desktop/X_team/.venv/bin/python -c "
from Agentos.orchestrator import OrchestratorAgent
import asyncio
asyncio.run(OrchestratorAgent(dry_run=True).run_daily())
"
```

### 2. Add X API Credentials

Edit `/Users/simonstenelid/Desktop/X_team/.env`:

```bash
# Add these lines (or update existing):
X_API_KEY=your_api_key_here
X_API_SECRET=your_api_secret_here
X_ACCESS_TOKEN=your_access_token_here
X_ACCESS_TOKEN_SECRET=your_access_token_secret_here
X_BEARER_TOKEN=your_bearer_token_here
```

### 3. Run in Production (Posts to X)

```bash
# Create a production script
cat > run_orchestrator.py << 'EOF'
import asyncio
from Agentos.orchestrator import OrchestratorAgent

async def main():
    orchestrator = OrchestratorAgent(dry_run=False)
    await orchestrator.run_daily()

if __name__ == "__main__":
    asyncio.run(main())
EOF

# Run it
/Users/simonstenelid/Desktop/X_team/.venv/bin/python run_orchestrator.py
```

### 4. Automate with Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs every hour, posts when scheduled):
0 * * * * cd /Users/simonstenelid/Desktop/X_team && /Users/simonstenelid/Desktop/X_team/.venv/bin/python run_orchestrator.py >> /Users/simonstenelid/Desktop/X_team/Agentos/logs/cron.log 2>&1
```

## 📊 Current State

After the test run, your orchestrator:

- **Last post:** 2025-11-13 at 20:06 (dry-run)
- **Next scheduled:** 2025-11-14 at 13:06 (lunch window)
- **Content posted:** 1 meme
- **Posts tracked:** 1 in database

## 🎯 Content Type Distribution

The orchestrator will automatically balance:
- **News:** 35% (2-3 per week)
- **Curator:** 30% (2-3 per week)
- **Meme:** 20% (1-2 per week)
- **Image:** 15% (1 per week)

Penalties and boosts ensure variety:
- Won't repeat same type 2 days in a row
- Boosts underused content types
- Tracks weekly quotas

## 📝 Monitoring

### View Current State
```bash
cat /Users/simonstenelid/Desktop/X_team/Agentos/orchestrator_db/orchestrator_state.json
```

### View Logs
```bash
tail -f /Users/simonstenelid/Desktop/X_team/Agentos/logs/orchestrator_$(date +%Y%m%d).log
```

### View Posts Database
```bash
cat /Users/simonstenelid/Desktop/X_team/Agentos/orchestrator_db/posts_database.json | head -50
```

## 🔧 Common Tasks

### Force Next Post Now

Edit state file and set `next_post_scheduled` to past time:
```bash
# Edit orchestrator_state.json
# Set: "next_post_scheduled": "2025-11-13T00:00:00+01:00"
```

### Reset Weekly Counters

Edit state file:
```json
"week_counts": {
  "news": 0,
  "curator": 0,
  "meme": 0,
  "image": 0
}
```

### Add Custom Backup Content

Edit `/Users/simonstenelid/Desktop/X_team/Agentos/backup_content.json`:
```json
{
  "news": [
    "Your custom news post 1",
    "Your custom news post 2"
  ],
  "meme": [
    "Your custom meme 1",
    "Your custom meme 2"
  ]
}
```

### Run Weekly Analysis

```bash
/Users/simonstenelid/Desktop/X_team/.venv/bin/python -c "
from Agentos.orchestrator import OrchestratorAgent
import asyncio
asyncio.run(OrchestratorAgent(dry_run=True).run_weekly_analysis())
"
```

## ⚙️ Configuration

All settings are in `/Users/simonstenelid/Desktop/X_team/Agentos/orchestrator.py`:

```python
self.config = {
    "posts_per_day": 1,
    "time_variance_minutes": 30,
    "base_weights": {
        "news": 0.35,
        "curator": 0.30,
        "meme": 0.20,
        "image": 0.15
    },
    "min_quality_score": 6,
    "max_regeneration_attempts": 2,
    "duplicate_similarity_threshold": 0.85,
    # ... more settings
}
```

## 🐛 Troubleshooting

### "Not time to post yet"
- This is normal! Check `next_post_scheduled` in state
- Orchestrator posts once per day at scheduled time
- Run hourly with cron to catch scheduled time

### "Module not found" errors
```bash
# Reinstall dependencies
cd /Users/simonstenelid/Desktop/X_team
uv sync
```

### X API errors
- Check credentials in `.env`
- Verify Twitter Developer account is active
- Test with dry_run=True first

### Agent failures
- Check individual agent files work
- Review logs for specific errors
- Use backup content as fallback

## 📚 Full Documentation

See `ORCHESTRATOR_GUIDE.md` for:
- Complete API reference
- Database schema details
- Advanced customization
- Scheduling strategies
- Error handling guide

## 🎉 You're Ready!

The orchestrator is fully functional and tested. Next steps:

1. ✅ Test with dry-run (already done!)
2. ⏭️ Add X API credentials
3. ⏭️ Run first production post manually
4. ⏭️ Set up cron job for automation
5. ⏭️ Monitor logs for first week

**Questions?** Check `ORCHESTRATOR_GUIDE.md` or review the logs.
