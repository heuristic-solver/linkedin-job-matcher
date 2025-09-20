# LinkedIn Job Matcher - Vercel Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Google API Key**: Get your API key from [Google AI Studio](https://aistudio.google.com/)
3. **Git Repository**: Your code should be in a Git repository (GitHub, GitLab, or Bitbucket)

## Deployment Steps

### Step 1: Prepare Environment Variables

1. In your Vercel dashboard, go to your project settings
2. Navigate to "Environment Variables"
3. Add the following variables:
   - `GOOGLE_API_KEY`: Your Google Generative AI API key
   - `FLASK_SECRET_KEY`: A secure random string for Flask sessions

### Step 2: Deploy with Vercel CLI

1. **Login to Vercel**:
   ```bash
   npx vercel login
   ```

2. **Navigate to your project directory**:
   ```bash
   cd /Users/a91788/Desktop/FYP
   ```

3. **Deploy to Vercel**:
   ```bash
   npx vercel
   ```
   
   Follow the prompts:
   - Link to existing project? **N** (for first deployment)
   - What's your project's name? **linkedin-job-matcher** (or your preferred name)
   - In which directory is your code located? **./** (current directory)
   - Want to override the settings? **N** (use vercel.json settings)

4. **Deploy to production**:
   ```bash
   npx vercel --prod
   ```

### Step 3: Alternative - Deploy from Git

1. **Push your code to GitHub** (if not already done)
2. **Connect repository in Vercel dashboard**:
   - Go to [vercel.com](https://vercel.com)
   - Click "New Project"
   - Import your GitHub repository
   - Add environment variables in project settings
   - Deploy

## Important Notes

### File Uploads in Serverless Environment
- Files are uploaded to `/tmp/uploads` in the serverless environment
- Files are temporary and will be cleaned up after function execution
- For production, consider using cloud storage (AWS S3, Google Cloud Storage)

### API Limitations
- Vercel has execution time limits (10s for Hobby, 60s for Pro)
- Large file processing might timeout
- Consider implementing async processing for production

### Environment Variables Required
```
GOOGLE_API_KEY=your_google_api_key_here
FLASK_SECRET_KEY=your_secret_key_here
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure all dependencies are in `requirements.txt`
2. **File Path Issues**: Use absolute paths or relative to project root
3. **Timeout Issues**: Optimize processing or use background jobs
4. **Memory Issues**: Vercel has memory limits (512MB Hobby, 3GB Pro)

### Local Testing Before Deployment

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GOOGLE_API_KEY="your_api_key"
export FLASK_SECRET_KEY="your_secret_key"

# Run locally
python app.py
```

## Production Optimizations

1. **Add error handling for file size limits**
2. **Implement file cleanup in `/tmp`**
3. **Add request rate limiting**
4. **Use CDN for static assets**
5. **Implement proper logging**
6. **Add health check endpoints**

## Support

For deployment issues:
- Check [Vercel documentation](https://vercel.com/docs)
- Review function logs in Vercel dashboard
- Test locally before deploying
