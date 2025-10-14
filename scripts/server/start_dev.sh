#!/bin/bash

# CODA Development Server Startup Script
echo "🚀 Starting CODA Development Server"
echo "=================================================="

# Get the app directory
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "📁 Working directory: $APP_DIR"

# Change to app directory
cd "$APP_DIR"

# Set Django settings module
export DJANGO_SETTINGS_MODULE="coda_project.ultra_minimal_settings"

echo "📧 Email backend: Console"
echo "🗄️ Database: SQLite"
echo "💾 Cache: Local memory"
echo "🌐 Server will start at: http://localhost:8000"
echo ""

# Run Django development server
python manage.py runserver 0.0.0.0:8000

