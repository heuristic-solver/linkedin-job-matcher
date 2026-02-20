# 🚀 Deployment Guide - LinkedIn Job Matcher

## Recommended Platform: Railway 🚂

**Railway is the best choice** for this Flask application because it:
- ✅ Supports background threading (your job matching requires this)
- ✅ Provides persistent file storage (for resume uploads)
- ✅ Offers generous free tier (500 hours/month, $5 credit)
- ✅ Auto-detects Python/Flask (zero configuration)
- ✅ Simple setup (5 minutes to deploy)

---

## 📖 Quick Start

See the complete guide: **[RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)**

### TL;DR - Deploy to Railway in 5 Minutes:

1. **Sign up**: [railway.app](https://railway.app) → Sign in with GitHub
2. **Create project**: New Project → Deploy from GitHub repo → Select your repo
3. **Add environment variables**:
   - `FLASK_SECRET_KEY` (generate with: `python3 -c "import secrets; print(secrets.token_hex(32))"`)
   - `GOOGLE_AI_API_KEY` (from [Google AI Studio](https://aistudio.google.com/))
   - `USE_EXTERNAL_FEEDS=true` (optional)
4. **Set start command**: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120`
5. **Deploy**: Railway auto-deploys on git push! 🎉

Your app will be live at: `https://your-app.railway.app`

---

## 🔄 Platform Comparison

For a detailed comparison of all platforms, see: **[DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md)**

### Quick Comparison

| Platform | Suitability | Background Threading | Free Tier | Setup Time |
|----------|-------------|---------------------|-----------|------------|
| **Railway** ⭐ | ⭐⭐⭐⭐⭐ | ✅ Yes | 500 hrs/month | 5 min |
| **Render** | ⭐⭐⭐⭐ | ✅ Yes | 750 hrs/month | 10 min |
| **Fly.io** | ⭐⭐⭐⭐ | ✅ Yes | Limited | 15 min |
| **Vercel** ❌ | ⭐ | ❌ No | Yes | N/A (requires refactor) |

---

## 📚 Detailed Guides

- **[RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)** - Complete Railway deployment guide
- **[DEPLOYMENT_COMPARISON.md](./DEPLOYMENT_COMPARISON.md)** - Platform comparison and alternatives

---

## 🔧 Environment Variables

All platforms require these environment variables:

```bash
FLASK_SECRET_KEY=your-secret-key-here        # Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
GOOGLE_AI_API_KEY=your-google-api-key        # From Google AI Studio
USE_EXTERNAL_FEEDS=true                      # Optional: Enable external job feeds
PORT=8000                                     # Usually auto-set by platform
```

---

## ✅ Pre-Deployment Checklist

- [ ] Code is pushed to GitHub
- [ ] `requirements.txt` includes all dependencies
- [ ] Environment variables ready
- [ ] Health check endpoint works (`/health`)
- [ ] Start command uses `$PORT` (not hardcoded)
- [ ] App runs locally with `gunicorn`

---

## 🆘 Need Help?

- **Railway**: [docs.railway.app](https://docs.railway.app) | [Discord](https://discord.gg/railway)
- **Render**: [render.com/docs](https://render.com/docs)
- **Fly.io**: [fly.io/docs](https://fly.io/docs)

---

## 📝 Legacy: Vercel Deployment (Not Recommended)

⚠️ **Vercel is NOT recommended** for this app because:
- ❌ No background threading support (your app needs this)
- ❌ Strict timeout limits (10-60s)
- ❌ No persistent file storage
- ❌ Would require major refactoring

If you still want Vercel deployment instructions, they were moved to a separate file. However, **Railway is strongly recommended** for this application.

---

**Ready to deploy?** Follow the **[Railway Deployment Guide](./RAILWAY_DEPLOYMENT.md)** 🚀
