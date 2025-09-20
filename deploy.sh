#!/bin/bash

# LinkedIn Job Matcher - Vercel Deployment Script

echo "🚀 LinkedIn Job Matcher - Vercel Deployment"
echo "=========================================="

# Check if user is logged into Vercel
echo "📋 Checking Vercel authentication..."
if ! npx vercel whoami > /dev/null 2>&1; then
    echo "❌ Not logged into Vercel. Please login first:"
    echo "   npx vercel login"
    exit 1
fi

echo "✅ Vercel authentication verified"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found. Make sure to set environment variables in Vercel dashboard:"
    echo "   - GOOGLE_API_KEY"
    echo "   - FLASK_SECRET_KEY"
    echo ""
fi

# Check required files
echo "📁 Checking required files..."
required_files=("app.py" "vercel.json" "requirements.txt" "api/index.py")

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Missing required file: $file"
        exit 1
    fi
done

echo "✅ All required files present"

# Deploy to preview first
echo "🔍 Deploying to preview environment..."
npx vercel

if [ $? -ne 0 ]; then
    echo "❌ Preview deployment failed"
    exit 1
fi

echo "✅ Preview deployment successful"

# Ask if user wants to deploy to production
read -p "🎯 Deploy to production? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Deploying to production..."
    npx vercel --prod
    
    if [ $? -eq 0 ]; then
        echo "🎉 Production deployment successful!"
        echo "📝 Don't forget to:"
        echo "   1. Set environment variables in Vercel dashboard"
        echo "   2. Test your deployment URL"
        echo "   3. Monitor function logs for any issues"
    else
        echo "❌ Production deployment failed"
        exit 1
    fi
else
    echo "⏭️  Skipped production deployment"
    echo "💡 You can deploy to production later with: npx vercel --prod"
fi

echo ""
echo "✨ Deployment complete!"
