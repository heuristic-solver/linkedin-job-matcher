# Quick Deployment Guide - Render.com

## ✅ Code Pushed to GitHub
Repository: `https://github.com/athsxx/linkedin-job-matcher.git`

## 🚀 Deploy to Render in 5 Steps

### Step 1: Sign Up / Login
- Go to https://render.com
- Sign up or log in with GitHub

### Step 2: Create New Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account (if not already connected)
3. Select repository: **`linkedin-job-matcher`**

### Step 3: Configure Service
Use these settings:

| Field | Value |
|------|-------|
| **Name** | `ai-resume-matcher` |
| **Region** | `Oregon (US West)` or closest to users |
| **Branch** | `main` |
| **Root Directory** | (leave empty) |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `gunicorn app:app --bind 0.0.0.0:$PORT` |

### Step 4: Set Environment Variables
Go to **"Environment"** tab and add:

```
GOOGLE_AI_API_KEY = your-google-gemini-api-key
FLASK_SECRET_KEY = (click "Generate" or use: python -c "import secrets; print(secrets.token_hex(32))")
USE_EXTERNAL_FEEDS = true
```

### Step 5: Deploy
1. Click **"Create Web Service"**
2. Wait for build to complete (~2-3 minutes)
3. Your app will be live at: `https://ai-resume-matcher.onrender.com`

## 📋 Post-Deployment Checklist

- [ ] Test health endpoint: `https://your-app.onrender.com/health`
- [ ] Upload a test resume
- [ ] Test job search
- [ ] Verify ATS checker works
- [ ] Check job links are working

## 🔧 Troubleshooting

**Build fails?**
- Check build logs in Render dashboard
- Verify all dependencies in `requirements.txt`

**App crashes?**
- Check environment variables are set
- Review application logs

**Slow first request?**
- Free tier spins down after 15 min inactivity
- First request after spin-down takes ~30 seconds
- Upgrade to Starter ($7/month) for always-on

## 📚 Full Documentation
See `RENDER_DEPLOYMENT.md` for detailed instructions.

## 🔗 Useful Links
- Render Dashboard: https://dashboard.render.com
- Your Repository: https://github.com/athsxx/linkedin-job-matcher
- Render Docs: https://render.com/docs

