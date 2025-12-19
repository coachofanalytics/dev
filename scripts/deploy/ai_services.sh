#!/bin/bash

# AI Services Deployment Script for Heroku (codamakutano app)
# This script automates the deployment process

echo "🚀 Starting AI Services deployment to Heroku (codamakutano app)..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Not in Django project directory"
    exit 1
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "📝 Staging changes..."
    git add .
    echo "💾 Committing changes..."
    git commit -m "Deploy AI Services updates - $(date '+%Y-%m-%d %H:%M:%S')"
fi

# Get current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Deploy to Heroku
echo "🚀 Deploying to Heroku (codamakutano app)..."
git push heroku $CURRENT_BRANCH:main

# Check deployment status
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo "🌐 App URL: https://codamakutano.herokuapp.com/ai_services/diaspora/"
    echo "📊 Analytics: https://codamakutano.herokuapp.com/ai_services/diaspora/analytics/"
    
    # Run migrations if needed
    echo "🔄 Running database migrations..."
    heroku run python manage.py migrate --app codamakutano
    
    # Check app status
    echo "🔍 Checking app status..."
    heroku ps --app codamakutano
    
    echo "🎉 AI Services deployment completed successfully!"
else
    echo "❌ Deployment failed!"
    echo "📋 Check logs with: heroku logs --tail --app codamakutano"
    exit 1
fi
