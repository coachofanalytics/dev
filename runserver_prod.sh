#!/bin/bash

# Run local development server connected to PRODUCTION database
# ⚠️  USE WITH EXTREME CAUTION ⚠️
# Requires production database credentials in environment variables

echo "⚠️  ⚠️  ⚠️  PRODUCTION DATABASE CONNECTION ⚠️  ⚠️  ⚠️"
echo "=========================================="
echo ""
echo "You are about to connect to the PRODUCTION database!"
echo "Any changes will affect LIVE data and REAL users!"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to proceed): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted. Good choice!"
    exit 0
fi

# Check for production credentials
if [ -z "$HEROKU_PROD_HOST" ] || [ -z "$HEROKU_PROD_NAME" ]; then
    echo "❌ ERROR: Production database credentials not found!"
    echo ""
    echo "Set environment variables:"
    echo "  export HEROKU_PROD_HOST='your-prod-host.amazonaws.com'"
    echo "  export HEROKU_PROD_NAME='your-prod-database'"
    echo "  export HEROKU_PROD_USER='your-prod-user'"
    echo "  export HEROKU_PROD_PASS='your-prod-password'"
    echo ""
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

echo ""
echo "🔧 Configuration:"
echo "   Database: PRODUCTION"
echo "   Host: $HEROKU_PROD_HOST"
echo "   Database: $HEROKU_PROD_NAME"
echo ""
echo "⚠️  ⚠️  ⚠️  PRODUCTION MODE ⚠️  ⚠️  ⚠️"
echo "   YOU ARE MODIFYING LIVE DATA!"
echo "   Use read-only operations when possible"
echo ""
echo "Access at: http://localhost:8000/"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

cd coda

# Run with LOCAL_DB=prod
LOCAL_DB=prod \
DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runserver 0.0.0.0:8000

