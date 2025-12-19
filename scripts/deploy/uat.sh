#!/bin/bash

# Heroku UAT Deployment Script
# This script deploys the application to Heroku UAT environment

set -e  # Exit on any error

echo "🚀 Starting Heroku UAT Deployment..."

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: manage.py not found. Please run this script from the project root."
    exit 1
fi

# Check if git is clean
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  Warning: You have uncommitted changes. Please commit or stash them first."
    echo "Current git status:"
    git status --short
    read -p "Do you want to continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Error: Heroku CLI not found. Please install it first."
    exit 1
fi

# Check if we're logged into Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo "❌ Error: Not logged into Heroku. Please run 'heroku login' first."
    exit 1
fi

echo "✅ Pre-deployment checks passed"

# Add all changes
echo "📦 Adding changes to git..."
git add .

# Commit changes
echo "💾 Committing changes..."
git commit -m "Deploy to UAT: $(date '+%Y-%m-%d %H:%M:%S')" || echo "No changes to commit"

# Deploy to Heroku
echo "🚀 Deploying to Heroku UAT..."
git push heroku main

# Run migrations
echo "🗄️  Running database migrations..."
heroku run python manage.py migrate --app codamakutano

# Collect static files
echo "📁 Collecting static files..."
heroku run python manage.py collectstatic --noinput --app codamakutano

# Check app status
echo "📊 Checking app status..."
heroku ps --app codamakutano

echo "✅ Deployment completed successfully!"
echo "🌐 App URL: https://codamakutano.herokuapp.com"
echo "📋 To view logs: heroku logs --tail --app codamakutano"
echo "🔧 To open app: heroku open --app codamakutano"
