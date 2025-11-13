# Deploy to Render.com - Complete Guide

This guide will help you deploy your X Agent Team orchestrator to Render.com for **100% autonomous operation** (FREE tier).

---

## 🎯 What You'll Get

✅ **Fully automated posting** - Posts once per day without any intervention
✅ **Free hosting** - Render's free tier (750 hours/month cron jobs)
✅ **Persistent storage** - State and databases preserved between runs
✅ **Auto-deployment** - Push to GitHub, automatically deploys
✅ **Environment variables** - Secure API key management
✅ **Logs & monitoring** - View all orchestrator activity

---

## 📋 Prerequisites

1. **GitHub account** (to host your code)
2. **Render.com account** (free) - Sign up at https://render.com
3. **API keys** ready:
   - OpenAI API key
   - X/Twitter API credentials (5 keys)
   - Serper API key (for news agent)
   - Apify API key (for content curator)
   - WaveSpeed AI API key (for image generator)

---

## 🚀 Deployment Steps

### Step 1: Push to GitHub

1. **Initialize git repository** (if not already done):
```bash
cd /Users/simonstenelid/Desktop/X_team
git init
git add .
git commit -m "Initial commit - X Agent Team orchestrator"
```

2. **Create GitHub repository**:
   - Go to https://github.com/new
   - Name: `x-agent-team`
   - Make it **Private** (recommended - contains your logic)
   - Don't initialize with README (you already have files)

3. **Push to GitHub**:
```bash
git remote add origin https://github.com/YOUR_USERNAME/x-agent-team.git
git branch -M main
git push -u origin main
```

---

### Step 2: Deploy to Render

1. **Go to Render Dashboard**:
   - Visit https://dashboard.render.com
   - Click **"New +"** → **"Blueprint"**

2. **Connect GitHub Repository**:
   - Select your `x-agent-team` repository
   - Render will detect the `render.yaml` file

3. **Configure Blueprint**:
   - Click **"Apply"**
   - Render will create the cron job service automatically

---

### Step 3: Add Environment Variables

In the Render dashboard, go to your cron job service and add these environment variables:

#### Required API Keys:

```bash
# OpenAI
OPENAI_API_KEY=sk-proj-your-key-here

# X/Twitter API
X_API_KEY=your-api-key
X_API_SECRET=your-api-secret
X_ACCESS_TOKEN=your-access-token
X_ACCESS_TOKEN_SECRET=your-access-token-secret
X_BEARER_TOKEN=your-bearer-token

# Serper (News Agent)
SERPER_API_KEY=your-serper-key

# Apify (Content Curator)
APIFY_API_KEY=your-apify-key

# WaveSpeed AI (Image Generator)
WAVESPEED_API_KEY=your-wavespeed-key
```

**To add each:**
1. Click **"Environment"** tab
2. Click **"Add Environment Variable"**
3. Enter key name and value
4. Click **"Save Changes"**

---

### Step 4: Configure Persistent Storage

1. **Go to your cron job service**
2. Click **"Disks"** tab
3. Click **"Add Disk"**:
   - **Name:** `orchestrator-data`
   - **Mount Path:** `/opt/render/project/src/Agentos/orchestrator_db`
   - **Size:** 1 GB (free tier)
4. Click **"Save"**

This ensures your state and posts database persist between runs.

---

### Step 5: Deploy!

1. **Manual Deploy** (first time):
   - Click **"Manual Deploy"** → **"Deploy latest commit"**
   - Wait for build to complete (~2-3 minutes)

2. **Check Logs**:
   - Click **"Logs"** tab
   - You should see: "Orchestrator Agent initialized"

3. **Verify Schedule**:
   - Go to **"Cron"** tab
   - Should show: "0 * * * *" (every hour)

---

## ✅ Verification

### Test the Deployment

After deployment, check:

1. **Logs show initialization**:
```
Orchestrator Agent initialized
Dry run mode: False
Timezone: Europe/Stockholm
```

2. **First run happens on schedule**:
   - Check logs at the top of next hour
   - Should see orchestrator run

3. **State persists**:
   - After first run, check logs for "State updated successfully"
   - Database files are saved to persistent disk

---

## 📊 How It Works

### Automatic Posting Flow:

```
Every Hour (Render Cron):
  ↓
Run render_job.py
  ↓
Orchestrator checks: "Is it time to post?"
  ├─ No → Exit (nothing happens)
  └─ Yes → Continue
      ↓
  Select content type (news/curator/meme/image)
      ↓
  Call appropriate agent
      ↓
  Validate & check duplicates
      ↓
  Post to X
      ↓
  Update state & database
      ↓
  Schedule next post (24h + variance)
```

**Result:** Posts once per day at varied times, 100% autonomously!

---

## 🔧 Configuration

### Change Posting Schedule

Edit `render.yaml`:
```yaml
schedule: "0 * * * *"  # Every hour (recommended)
# or
schedule: "0 */2 * * *"  # Every 2 hours
# or
schedule: "0 8,12,16,20 * * *"  # 4 times per day
```

### Adjust Content Mix

Edit `Agentos/orchestrator.py`:
```python
"base_weights": {
    "news": 0.40,     # More news
    "curator": 0.35,  # More curated
    "meme": 0.15,     # Less memes
    "image": 0.10     # Less images
}
```

Then push changes:
```bash
git add .
git commit -m "Adjust content weights"
git push
```

Render will auto-deploy!

---

## 📈 Monitoring

### View Logs

1. Go to Render dashboard
2. Click your cron job service
3. Click **"Logs"** tab
4. Filter by:
   - "ORCHESTRATOR DAILY RUN STARTING" - When it runs
   - "Posted:" - What was posted
   - "Tweet ID:" - Link to tweet
   - "ERROR" - Any failures

### Check State

SSH into Render (or use logs):
```bash
# State file location on Render:
/opt/render/project/src/Agentos/orchestrator_db/orchestrator_state.json
```

### Download Database

In Render dashboard:
1. Click **"Shell"** tab
2. Run: `cat Agentos/orchestrator_db/orchestrator_state.json`
3. Copy and save locally

---

## 🚨 Troubleshooting

### "Module not found" errors
- Check `requirements.txt` has all dependencies
- Redeploy: **"Manual Deploy"** → **"Clear build cache & deploy"**

### "No such file or directory" for database
- Ensure persistent disk is mounted at correct path
- Check disk is created and attached

### Posts not happening
- Check logs for "Not time to post yet"
- Verify `next_post_scheduled` in state file
- Ensure cron schedule is correct

### API errors (403 Forbidden)
- Check all environment variables are set
- Verify X API has Read & Write permissions
- Test API keys locally first

### Out of free tier hours
- Render free tier: 750 hours/month for cron jobs
- Hourly runs = 24 × 30 = 720 hours (safe)
- If exceeded, upgrade to $7/month plan

---

## 💰 Cost Breakdown

### Render.com Free Tier:
- ✅ 750 cron job hours/month (more than enough)
- ✅ 1GB persistent disk
- ✅ Auto-deployments unlimited
- **Cost:** $0/month

### API Costs (Pay-per-use):
- OpenAI API: ~$1-3/month (depends on usage)
- X API: Free (organic posting)
- Serper: ~$0-1/month (100 free searches/month)
- Apify: Free tier available
- WaveSpeed AI: Pay per image generated

**Total:** ~$1-5/month (mostly API costs, hosting is FREE)

---

## 🔐 Security Best Practices

### Never Commit API Keys
- ✅ `.env` is in `.gitignore`
- ✅ Use Render environment variables
- ✅ Keep repository private

### Review Code Before Deploying
- Check orchestrator logic
- Verify agent behaviors
- Test locally first with `dry_run=True`

### Monitor Regularly
- Check logs weekly
- Review posted content
- Verify engagement metrics

---

## 🎉 Success!

Once deployed, your orchestrator will:

✅ Run every hour automatically
✅ Post once per day at varied times
✅ Select content type intelligently
✅ Generate unique content with agents
✅ Prevent duplicates
✅ Track all metrics
✅ Operate 100% autonomously

**Your X account is now fully automated!** 🤖

---

## 🆘 Support

**Issues with deployment?**
1. Check Render logs first
2. Review this guide step-by-step
3. Test locally with `test_orchestrator.py`
4. Check Render documentation: https://render.com/docs

**Ready to deploy?** Follow the steps above!
