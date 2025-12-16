# ⚡ Railway Quick Start - 5 Minute Deploy

## Step-by-Step (Copy & Paste)

### 1️⃣ Sign Up
👉 [railway.app](https://railway.app) → Sign in with GitHub

### 2️⃣ Create Project
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Choose your repository
4. Railway auto-detects Python ✅

### 3️⃣ Add Environment Variables
In Railway dashboard → Your Service → **Variables** tab:

```bash
FLASK_SECRET_KEY=your-secret-key-here
GOOGLE_AI_API_KEY=your-actual-google-api-key-here
USE_EXTERNAL_FEEDS=true
```

**Generate your own FLASK_SECRET_KEY:**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### 4️⃣ Set Start Command
In Railway dashboard → Your Service → **Settings** → **Start Command**:

```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### 5️⃣ Deploy
- Railway automatically deploys when you push to GitHub
- OR click **"Deploy"** button
- Wait 2-3 minutes
- Get your URL: **Settings** → **Generate Domain**

### 6️⃣ Test
Visit: `https://your-app.railway.app`
- ✅ Homepage loads
- ✅ `/health` endpoint works
- ✅ Upload resume works
- ✅ Job search works

---

## 🎉 Done!

Your app is live! Share the URL and start matching jobs.

---

## 📚 Need More Details?

- **Full Guide**: See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
- **Platform Comparison**: See [DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md)

---

## 🐛 Common Issues

**Build fails?**
- Check `requirements.txt` has all dependencies
- Check build logs in Railway dashboard

**App crashes?**
- Verify environment variables are set
- Check logs for errors
- Ensure start command uses `$PORT`

**File uploads not working?**
- Railway supports file storage - should work out of the box
- Check `uploads/` directory permissions (usually fine)

---

**Ready?** Start at [railway.app](https://railway.app) 🚀

