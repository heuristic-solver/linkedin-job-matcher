# 🚂 Railway Deployment Guide - LinkedIn Job Matcher

Complete step-by-step guide to deploy your Flask job matching application on Railway.

---

## 📋 Prerequisites

1. ✅ **GitHub Account** - Your code should be in a GitHub repository
2. ✅ **Railway Account** - Sign up at [railway.app](https://railway.app) (free)
3. ✅ **Google API Key** - Get from [Google AI Studio](https://aistudio.google.com/)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Sign Up for Railway

1. Go to [railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Sign in with **GitHub** (recommended) or email
4. Authorize Railway to access your GitHub repositories

### Step 2: Create New Project

1. In Railway dashboard, click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository (`linkedin-job-matcher` or your repo name)
4. Railway will automatically:
   - Detect Python
   - Find `requirements.txt`
   - Configure the build process

### Step 3: Configure Environment Variables

1. Click on your service (should auto-appear)
2. Go to **"Variables"** tab
3. Add these environment variables:

```bash
FLASK_SECRET_KEY=your-secret-key-here
GOOGLE_AI_API_KEY=your-google-api-key
USE_EXTERNAL_FEEDS=true
```

**Generate a secure FLASK_SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output and use it as `FLASK_SECRET_KEY`.

### Step 4: Configure Start Command

1. In your service settings, go to **"Settings"** tab
2. Find **"Start Command"**
3. Set it to:
   ```bash
   gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```

**OR** if you prefer using the config file:
```bash
gunicorn app:app --config gunicorn_config.py
```

### Step 5: Deploy!

1. Railway automatically deploys when you push to the main branch
2. Click **"Deploy"** or push a commit to trigger deployment
3. Wait 2-3 minutes for build to complete
4. Click **"Generate Domain"** to get your live URL
5. Your app will be live at: `your-app.railway.app`

---

## 🔧 Advanced Configuration

### Using railway.toml (Optional)

Create a `railway.toml` file in your repo root for advanced configuration:

```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120"
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

This file is optional - Railway works great without it!

### Custom Build Command (If Needed)

If Railway doesn't auto-detect correctly, you can set a custom build command:

```bash
pip install -r requirements.txt
```

---

## 🌐 Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `FLASK_SECRET_KEY` | ✅ Yes | Secret key for Flask sessions | Generated token |
| `GOOGLE_AI_API_KEY` | ✅ Yes | Google Generative AI API key | `AIza...` |
| `USE_EXTERNAL_FEEDS` | ❌ No | Enable external job feeds | `true` or `false` |
| `PORT` | ❌ No | Server port (Railway sets automatically) | `8000` |

---

## 📁 Project Structure Railway Expects

Your project should have this structure:

```
FYP/
├── app.py                 # Main Flask application ✅
├── requirements.txt       # Python dependencies ✅
├── templates/            # HTML templates ✅
├── static/               # CSS/JS files ✅
├── linkedin_job_matcher.py
├── matching/
├── extraction/
├── intelligence/
└── railway.toml          # Optional config
```

Railway will automatically:
- ✅ Detect Python from `requirements.txt`
- ✅ Install dependencies with `pip install -r requirements.txt`
- ✅ Find your Flask app in `app.py`
- ✅ Use Gunicorn to run the app

---

## 🧪 Testing Your Deployment

After deployment, test these endpoints:

### 1. Homepage
```bash
curl https://your-app.railway.app/
```
Should return HTML.

### 2. Health Check
```bash
curl https://your-app.railway.app/health
```
Should return: `{"status": "healthy"}`

### 3. File Upload
Test via the web interface at `https://your-app.railway.app`

---

## 🔍 Monitoring & Logs

### View Logs

1. In Railway dashboard, click on your service
2. Go to **"Deployments"** tab
3. Click on a deployment to see logs
4. Or use **"View Logs"** button for real-time logs

### Common Log Messages

**Success:**
```
[INFO] Starting gunicorn
[INFO] Listening at: http://0.0.0.0:8000
[INFO] Application startup complete
```

**Issues:**
- `ModuleNotFoundError` → Check `requirements.txt`
- `Port already in use` → Railway sets PORT automatically, don't hardcode it
- `ImportError` → Check file structure and imports

---

## 🐛 Troubleshooting

### Issue: Build Fails

**Problem:** Railway can't build your app

**Solutions:**
1. Check `requirements.txt` has all dependencies
2. Verify Python version (Railway uses 3.11 by default)
3. Check build logs for specific errors
4. Ensure all files are committed to Git

### Issue: App Crashes on Startup

**Problem:** App starts but immediately crashes

**Solutions:**
1. Check environment variables are set correctly
2. Verify start command uses `$PORT` (not hardcoded port)
3. Check logs for import errors
4. Ensure `app.py` has the Flask app instance named `app`

### Issue: File Uploads Not Working

**Problem:** Uploads fail or files disappear

**Solutions:**
1. ✅ **Railway supports persistent storage** - files in `uploads/` directory persist
2. Files are stored in Railway's filesystem (ephemeral storage)
3. For production, consider cloud storage (S3) if you need long-term storage
4. For Railway, the `uploads/` directory works fine for temporary files

### Issue: Background Threading Not Working

**Problem:** Background job matching doesn't work

**Solutions:**
1. ✅ Railway fully supports Python threading
2. Your `threading.Thread` code works perfectly on Railway
3. Check logs to see if threads are starting
4. Verify `progress_store` is being updated

### Issue: Port Errors

**Problem:** `Address already in use` or port conflicts

**Solutions:**
1. ✅ **Never hardcode ports** - always use `$PORT` environment variable
2. Railway automatically sets `PORT` - your code already handles this correctly
3. Use: `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Your `app.py` already uses `os.environ.get('PORT', 5003)` ✅

---

## 💰 Pricing & Limits

### Free Tier (Hobby Plan)
- ✅ **$5 credit/month** (usually enough for small apps)
- ✅ **500 hours runtime/month**
- ✅ **100GB bandwidth**
- ✅ **512MB RAM** (enough for Flask apps)
- ✅ **1GB storage**

### When to Upgrade
- Your app uses more than $5/month
- Need more RAM (your app is fine with 512MB)
- Need custom domains
- Need more bandwidth

### Cost Estimate
- Small Flask app: **$0-5/month** (usually free!)
- Medium traffic: **$5-20/month**
- High traffic: **$20+/month**

---

## 🔄 Continuous Deployment

Railway automatically deploys when you push to GitHub!

### Setup Auto-Deploy

1. ✅ Already enabled by default
2. Pushes to `main` branch trigger deployments
3. Can configure branch in **Settings** → **Source**

### Manual Deploy

1. Go to **Deployments** tab
2. Click **"Redeploy"** on any deployment
3. Or push a commit to trigger new deployment

### Deploy Specific Branch

1. In **Settings** → **Source**
2. Select branch: `main`, `develop`, etc.
3. Railway will deploy that branch

---

## 🔐 Security Best Practices

### 1. Environment Variables
- ✅ Never commit secrets to Git
- ✅ Use Railway's Variables tab
- ✅ Rotate keys regularly

### 2. Flask Secret Key
- ✅ Use strong random key (32+ characters)
- ✅ Generate: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### 3. API Keys
- ✅ Store in Railway Variables (not code)
- ✅ Restrict API key permissions
- ✅ Use separate keys for dev/prod

### 4. File Uploads
- ✅ Already limited to 16MB (good!)
- ✅ File type validation (good!)
- ✅ Consider adding virus scanning for production

---

## 📊 Performance Optimization

### Gunicorn Workers

Current config uses `--workers 2` which is good for Railway's free tier.

For more traffic, increase workers:
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 4
```

Formula: `workers = (2 × CPU cores) + 1`

### Caching

Consider adding:
- Redis for session storage
- CDN for static assets (Railway has built-in CDN)
- Database for job results (if needed)

### Monitoring

Railway provides:
- ✅ Real-time logs
- ✅ Deployment history
- ✅ Resource usage metrics
- ✅ Error tracking

---

## 🎯 Next Steps After Deployment

1. ✅ **Test all features** - Upload resume, search jobs, check analytics
2. ✅ **Set up custom domain** - In Railway Settings → Domains
3. ✅ **Enable HTTPS** - Automatic with Railway (free!)
4. ✅ **Monitor logs** - Check for errors in first few days
5. ✅ **Set up alerts** - Railway can notify on crashes
6. ✅ **Add database** - If you need persistent job storage (optional)

---

## 🆘 Getting Help

### Railway Resources
- 📚 [Railway Docs](https://docs.railway.app)
- 💬 [Railway Discord](https://discord.gg/railway)
- 🐦 [Railway Twitter](https://twitter.com/railway)

### Common Questions

**Q: How do I update my app?**
A: Just push to GitHub - Railway auto-deploys!

**Q: Can I use a custom domain?**
A: Yes! Settings → Domains → Add Custom Domain

**Q: How do I rollback?**
A: Deployments → Click previous deployment → Redeploy

**Q: How much does it cost?**
A: Usually free for small apps! Check usage in dashboard.

---

## ✅ Deployment Checklist

Before going live, verify:

- [ ] Environment variables set (FLASK_SECRET_KEY, GOOGLE_AI_API_KEY)
- [ ] Start command configured (gunicorn with $PORT)
- [ ] Health check endpoint works (`/health`)
- [ ] File uploads work
- [ ] Job search works
- [ ] Background threading works (progress updates)
- [ ] Logs show no errors
- [ ] App responds at Railway URL
- [ ] HTTPS enabled (automatic)

---

## 🎉 You're Live!

Your app is now deployed at: `https://your-app.railway.app`

Share the link and start matching jobs! 🚀

---

**Need help?** Check the [Railway docs](https://docs.railway.app) or reach out in their Discord community.

