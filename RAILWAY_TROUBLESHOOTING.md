# 🔧 Railway Deployment Troubleshooting

## Health Check Failed - Service Unavailable

### Issue: Health check fails with "service unavailable"

### ✅ Fix Applied:
The app was crashing on startup because `GOOGLE_AI_API_KEY` was required but the LLM features are disabled.

**Fixed in `linkedin_job_matcher.py`:**
- Changed API key check from `raise ValueError` to a warning
- App now starts even without the API key (uses structured extraction only)

### 🔍 Common Issues & Solutions

#### 1. Health Check Timeout
**Problem:** Health check times out before app starts

**Solution:** 
- Increase timeout in `railway.toml`: `healthcheckTimeout = 200`
- Or disable health check temporarily to debug

#### 2. Missing Environment Variables
**Problem:** App crashes on startup

**Check these variables are set in Railway:**
- `FLASK_SECRET_KEY` (required)
- `GOOGLE_AI_API_KEY` (optional - app works without it now)
- `USE_EXTERNAL_FEEDS` (optional)

#### 3. Import Errors
**Problem:** Module not found errors

**Solution:**
- Check `requirements.txt` has all dependencies
- Check build logs in Railway dashboard
- Ensure all files are committed to git

#### 4. Port Issues
**Problem:** Port already in use

**Solution:**
- Always use `$PORT` in start command (Railway sets it automatically)
- Don't hardcode port numbers
- Start command: `gunicorn app:app --bind 0.0.0.0:$PORT`

#### 5. Gunicorn Not Starting
**Problem:** Gunicorn command fails

**Check:**
- Start command is correct: `gunicorn app:app --bind 0.0.0.0:$PORT --workers 2`
- Gunicorn is in `requirements.txt`: `gunicorn>=21.2.0`
- App instance is named `app` in `app.py`

### 📋 Debugging Steps

1. **Check Railway Logs:**
   - Go to Railway dashboard
   - Click on your service
   - View "Deployments" → Click latest deployment
   - Check build logs and runtime logs

2. **Test Locally First:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export FLASK_SECRET_KEY="test-key"
   export PORT=8000
   
   # Test with gunicorn
   gunicorn app:app --bind 0.0.0.0:8000 --workers 2
   
   # Test health endpoint
   curl http://localhost:8000/health
   ```

3. **Verify Health Endpoint:**
   ```bash
   # Should return: {"status": "healthy", "timestamp": ...}
   curl https://your-app.railway.app/health
   ```

4. **Check Environment Variables:**
   - Railway Dashboard → Your Service → Variables tab
   - Ensure all required variables are set
   - No typos in variable names

### 🚨 Latest Fix Summary

**Issue:** App crashed on startup due to missing `GOOGLE_AI_API_KEY`

**Fix:** Made API key optional (line 31-33 in `linkedin_job_matcher.py`)

**Before:**
```python
if not api_key:
    raise ValueError("GOOGLE_AI_API_KEY environment variable is required.")
```

**After:**
```python
if not api_key:
    print("Warning: GOOGLE_AI_API_KEY not set. LLM features disabled - using structured extraction only.")
```

**Result:** App now starts successfully even without the API key!

### 📝 Next Steps After Fix

1. **Commit and push the fix:**
   ```bash
   git add linkedin_job_matcher.py railway.toml
   git commit -m "Fix: Make GOOGLE_AI_API_KEY optional for Railway deployment"
   git push origin main
   ```

2. **Railway will auto-deploy** the fix

3. **Monitor the deployment** in Railway dashboard

4. **Test the health endpoint** after deployment completes

### ✅ Verification Checklist

After deploying, verify:
- [ ] Build completes successfully
- [ ] Health check passes
- [ ] Homepage loads: `https://your-app.railway.app/`
- [ ] Health endpoint works: `https://your-app.railway.app/health`
- [ ] File upload works
- [ ] Job search works

### 🆘 Still Having Issues?

1. **Check Railway logs** for specific error messages
2. **Verify environment variables** are set correctly
3. **Test locally** with same configuration
4. **Check Railway status**: [status.railway.app](https://status.railway.app)
5. **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)

