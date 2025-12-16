# Render Deployment Guide

## Prerequisites
1. GitHub repository with your code pushed
2. Render account (sign up at https://render.com)
3. Google AI API key (for Gemini API)

## Step-by-Step Deployment Instructions

### 1. Push Code to GitHub

```bash
# Add all changes
git add .

# Commit changes
git commit -m "Production-ready: ATS checker, multi-platform jobs, improved matching"

# Push to GitHub
git push origin main
```

### 2. Create Render Web Service

1. **Go to Render Dashboard**
   - Visit https://dashboard.render.com
   - Click "New +" → "Web Service"

2. **Connect Repository**
   - Click "Connect GitHub" or "Connect GitLab"
   - Authorize Render to access your repositories
   - Select your repository: `linkedin-job-matcher`

3. **Configure Service**
   - **Name**: `ai-resume-matcher` (or your preferred name)
   - **Region**: Choose closest to your users (e.g., `Oregon (US West)`)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or `.` if needed)
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`

### 3. Configure Environment Variables

In Render dashboard, go to your service → "Environment" tab, add:

| Key | Value | Notes |
|-----|-------|-------|
| `GOOGLE_AI_API_KEY` | `your-api-key-here` | Your Google Gemini API key |
| `FLASK_SECRET_KEY` | `generate-random-string` | Use: `python -c "import secrets; print(secrets.token_hex(32))"` |
| `USE_EXTERNAL_FEEDS` | `true` | Enable external job feeds |
| `PORT` | `10000` | Render sets this automatically, but include for safety |

### 4. Update app.py for Render

The app should already be configured to use `PORT` environment variable. Verify:

```python
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
```

### 5. Deploy

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Install dependencies
   - Build your application
   - Start the service

### 6. Monitor Deployment

- Watch the build logs in real-time
- Check for any errors
- Once deployed, your app will be available at: `https://your-service-name.onrender.com`

### 7. Post-Deployment Checklist

- [ ] Test the health endpoint: `https://your-service-name.onrender.com/health`
- [ ] Upload a test resume
- [ ] Test job search functionality
- [ ] Verify ATS checker works
- [ ] Check that external job feeds are working

## Troubleshooting

### Common Issues

1. **Build Fails**
   - Check `requirements.txt` for all dependencies
   - Verify Python version compatibility
   - Check build logs for specific errors

2. **App Crashes on Start**
   - Verify all environment variables are set
   - Check that `PORT` is being used correctly
   - Review application logs

3. **File Upload Issues**
   - Ensure `uploads/` directory is writable
   - Check file size limits (16MB max)

4. **API Errors**
   - Verify `GOOGLE_AI_API_KEY` is correct
   - Check API quota limits
   - Review error logs

### Viewing Logs

- Go to your service → "Logs" tab
- Real-time logs are available
- Use logs to debug issues

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `GOOGLE_AI_API_KEY` | Yes | Google Gemini API key |
| `FLASK_SECRET_KEY` | Yes | Secret key for Flask sessions |
| `USE_EXTERNAL_FEEDS` | No | Enable external job feeds (default: false) |
| `PORT` | Auto | Port number (set by Render) |

## Updating Your Deployment

1. Push changes to GitHub
2. Render automatically detects changes
3. Triggers new deployment
4. Monitor build logs

## Cost Considerations

- **Free Tier**: 
  - Services spin down after 15 minutes of inactivity
  - First request after spin-down takes ~30 seconds
  - 750 hours/month free

- **Starter Plan** ($7/month):
  - Always-on service
   - No spin-down delays
   - Better performance

## Security Notes

- Never commit `.env` file
- Use Render's environment variables for secrets
- Enable HTTPS (automatic on Render)
- Keep dependencies updated

## Support

- Render Docs: https://render.com/docs
- Render Community: https://community.render.com
- Check application logs for debugging

