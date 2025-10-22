#!/bin/bash

# Run local development server connected to UAT (Heroku staging) database
# Requires UAT database credentials in environment variables

echo "🚀 Starting Local Server with UAT Database"
echo "=========================================="
echo ""

# Check for UAT credentials
if [ -z "$HEROKU_DEV_HOST" ] || [ -z "$HEROKU_DEV_NAME" ]; then
    echo "❌ ERROR: UAT database credentials not found!"
    echo ""
    echo "Set environment variables:"
    echo "  export HEROKU_DEV_HOST='your-uat-host.amazonaws.com'"
    echo "  export HEROKU_DEV_NAME='your-uat-database'"
    echo "  export HEROKU_DEV_USER='your-uat-user'"
    echo "  export HEROKU_DEV_PASS='your-uat-password'"
    echo ""
    echo "Or load from .env file"
    exit 1
fi

# Kill existing server
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Killing existing server..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ ERROR: Virtual environment not found"
    exit 1
fi

echo "🔧 Configuration:"
echo "   Database: UAT (Heroku staging)"
echo "   Host: $HEROKU_DEV_HOST"
echo "   Database: $HEROKU_DEV_NAME"
echo ""
echo "⚠️  WARNING: You're connected to UAT database!"
echo "   Changes will affect UAT environment"
echo ""
echo "Access at: http://localhost:8000/"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

cd coda

# Run with LOCAL_DB=uat
LOCAL_DB=uat \
DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runserver 0.0.0.0:8000

