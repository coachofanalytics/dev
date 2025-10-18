#!/bin/bash

# Local Development Server (HTTP)
# For local development with SQLite database

echo "🚀 Starting CODA Local Development Server"
echo "=========================================="
echo ""

# Kill any existing server on port 8000
echo "📋 Checking for existing server..."
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Found existing server on port 8000. Killing it..."
    lsof -ti :8000 | xargs kill -9 2>/dev/null
    sleep 2
    echo "✅ Old server stopped"
else
    echo "✅ Port 8000 is available"
fi

echo ""
echo "🔧 Configuration:"
echo "   Settings: coda_project.coda_settings.local_settings"
echo "   Database: SQLite (db.sqlite3)"
echo "   Protocol: HTTP (use http:// not https://)"
echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ ERROR: Virtual environment not found at venv/"
    exit 1
fi

echo ""
echo "🚀 Starting HTTP server..."
echo "=========================================="
echo ""
echo "Access your site at:"
echo "  👉 http://localhost:8000/"
echo "  👉 http://localhost:8000/portfolio/"
echo "  👉 http://localhost:8000/interview/"
echo "  👉 http://localhost:8000/dashboard/"
echo ""
echo "⚠️  NOTE: Use HTTP (not HTTPS) for local development"
echo "   If you see SSL errors, make sure you're using http://"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

# Change to coda directory
cd coda

# Run HTTP server with explicit settings module
DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runserver 0.0.0.0:8000

