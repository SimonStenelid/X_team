# 🚀 Render.com Deployment Checklist

Use this checklist to ensure your deployment is successful.

---

## ✅ Pre-Deployment

### 1. Local Testing
- [ ] All agents work locally
- [ ] Successfully posted test tweet
- [ ] State management working
- [ ] Duplicate detection tested
- [ ] `.env` file has all API keys

### 2. Code Review
- [ ] `.env` is in `.gitignore`
- [ ] No API keys in code files
- [ ] `requirements.txt` is up to date
- [ ] `render.yaml` is configured
- [ ] `render_job.py` exists

### 3. API Keys Ready
- [ ] OpenAI API key
- [ ] X API key (Consumer Key)
- [ ] X API secret (Consumer Secret)
- [ ] X Access Token
- [ ] X Access Token Secret
- [ ] X Bearer Token
- [ ] Serper API key (optional)
- [ ] Apify API key (optional)
- [ ] WaveSpeed API key (optional)

---

## 🔧 GitHub Setup

### 1. Initialize Git
```bash
cd /Users/simonstenelid/Desktop/X_team
git init
git add .
git commit -m "Initial commit - X Agent Team"
```

- [ ] Git repository initialized
- [ ] All files added
- [ ] Initial commit created

### 2. Create GitHub Repository
- [ ] Go to https://github.com/new
- [ ] Repository name: `x-agent-team`
- [ ] Visibility: Private (recommended)
- [ ] Don't initialize with README
- [ ] Repository created

### 3. Push to GitHub
```bash
git remote add origin https://github.com/YOUR_USERNAME/x-agent-team.git
git branch -M main
git push -u origin main
```

- [ ] Remote added
- [ ] Pushed to GitHub
- [ ] Repository shows all files

**Verify:**
- [ ] `.env` is NOT in GitHub (check repo)
- [ ] `render.yaml` IS in GitHub
- [ ] All Python files visible

---

## ☁️ Render.com Setup

### 1. Create Account
- [ ] Sign up at https://render.com
- [ ] Email verified
- [ ] Connected GitHub account

### 2. Deploy Blueprint
- [ ] Go to https://dashboard.render.com
- [ ] Click "New +" → "Blueprint"
- [ ] Select `x-agent-team` repository
- [ ] Click "Apply"
- [ ] Wait for service to be created

### 3. Configure Service
- [ ] Service name: `x-agent-orchestrator`
- [ ] Type: Cron Job
- [ ] Schedule: `0 * * * *` (every hour)
- [ ] Runtime: Python 3.12

---

## 🔐 Environment Variables

In Render dashboard → Your service → Environment tab:

### Required Variables
- [ ] `OPENAI_API_KEY` = your-openai-key
- [ ] `X_API_KEY` = your-x-api-key
- [ ] `X_API_SECRET` = your-x-api-secret
- [ ] `X_ACCESS_TOKEN` = your-x-access-token
- [ ] `X_ACCESS_TOKEN_SECRET` = your-x-access-token-secret
- [ ] `X_BEARER_TOKEN` = your-x-bearer-token

### Optional Variables (for specific agents)
- [ ] `SERPER_API_KEY` = your-serper-key (news agent)
- [ ] `APIFY_API_KEY` = your-apify-key (curator agent)
- [ ] `WAVESPEED_API_KEY` = your-wavespeed-key (image agent)

**After adding all, click "Save Changes"**

---

## 🚀 Deploy

### First Deployment
- [ ] Click "Manual Deploy"
- [ ] Select "Deploy latest commit"
- [ ] Wait for build (2-3 minutes)
- [ ] Build status: "Live"

### Check Logs
- [ ] Click "Logs" tab
- [ ] See: "Installing dependencies..."
- [ ] See: "Orchestrator Agent initialized"
- [ ] See: "Dry run mode: False"
- [ ] No errors in logs

---

## ✅ Verification

### 1. First Run
- [ ] Wait for next hour (top of hour)
- [ ] Check logs at :00 minutes
- [ ] See: "ORCHESTRATOR DAILY RUN STARTING"
- [ ] See: "Ready to post" OR "Not time to post yet"

### 2. State Persistence
After first successful run:
- [ ] See: "State updated successfully"
- [ ] See: "Posts database updated"
- [ ] See: "Next post scheduled for: ..."

### 3. Scheduled Post
Wait for scheduled time:
- [ ] Orchestrator posts to X
- [ ] Tweet appears on your X account
- [ ] Logs show: "Tweet posted successfully! ID: ..."
- [ ] State shows updated counts

### 4. Cron Schedule
- [ ] Go to "Cron" tab in Render
- [ ] See schedule: "0 * * * *"
- [ ] See next run time
- [ ] Status: "Active"

---

## 🎯 Success Criteria

Your deployment is successful when:

- [x] ✅ Service is "Live"
- [x] ✅ No errors in logs
- [x] ✅ Runs every hour automatically
- [x] ✅ Posts once per day at scheduled time
- [x] ✅ State persists between runs
- [x] ✅ Tweets appear on X account
- [x] ✅ No duplicate posts
- [x] ✅ Content variety maintained

---

## 🐛 Common Issues

### Build Fails
- **Check:** `requirements.txt` syntax
- **Fix:** Ensure all packages listed correctly
- **Retry:** "Clear build cache & deploy"

### "Module not found"
- **Check:** Package in `requirements.txt`
- **Fix:** Add missing package
- **Retry:** Deploy again

### "Environment variable not set"
- **Check:** All API keys added in Render
- **Fix:** Add missing variables
- **Retry:** Redeploy

### Disk not mounted
- **Check:** Disk mount path matches code
- **Fix:** Path should be `/opt/render/project/src/Agentos/orchestrator_db`
- **Verify:** Restart service

### Posts not happening
- **Check:** Logs for "Not time to post yet"
- **Normal:** Orchestrator only posts when scheduled
- **Wait:** Check `next_post_scheduled` in logs
- **Verify:** State file exists on disk

### X API errors
- **Check:** All 5 X API credentials added
- **Check:** X Developer Portal permissions (Read & Write)
- **Fix:** Regenerate tokens with correct permissions
- **Test:** Run locally first

---

## 📊 Monitoring (First Week)

### Daily Checks
- [ ] Check logs daily
- [ ] Verify post went out
- [ ] Check X account
- [ ] Review engagement

### Weekly Review
- [ ] 7 posts in 7 days
- [ ] Content variety (mix of types)
- [ ] No duplicates
- [ ] Engagement trends

### Monthly
- [ ] Render usage (should be under 750 hours)
- [ ] API costs (OpenAI, etc.)
- [ ] Follower growth
- [ ] Adjust strategy if needed

---

## 🎉 You're Done!

When all checkboxes are complete:

✅ Your X Agent Team is fully deployed
✅ Running 100% autonomously on Render
✅ Posting once per day automatically
✅ No maintenance required

**Next:** Monitor for a week, then let it run forever! 🚀

---

## 🆘 Need Help?

1. Check [RENDER_DEPLOYMENT.md](RENDER_DEPLOYMENT.md) for detailed steps
2. Review Render logs for errors
3. Test locally with `test_orchestrator.py`
4. Verify all environment variables
5. Check Render dashboard health

**Still stuck?** Review this checklist step-by-step.
