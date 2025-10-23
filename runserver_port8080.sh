#!/bin/bash

# Run local development server on port 8080
# Use this if port 8000 has HTTPS cached in browser

echo "🚀 Starting CODA Local Development Server on Port 8080"
echo "======================================================"
echo ""
echo "Using port 8080 to avoid browser HTTPS cache issues"
echo ""

# Kill any existing server on port 8080
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Killing existing server on port 8080..."
    lsof -ti :8080 | xargs kill -9 2>/dev/null
    sleep 2
fi

# Activate venv
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "❌ ERROR: Virtual environment not found"
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""
echo "🔧 Configuration:"
echo "   Settings: local_settings (SQLite)"
echo "   Port: 8080 (avoiding cached HTTPS)"
echo "   Protocol: HTTP"
echo ""
echo "🚀 Access your site at:"
echo "   👉 http://localhost:8080/"
echo "   👉 http://localhost:8080/portfolio/"
echo "   👉 http://localhost:8080/interview/"
echo "   👉 http://localhost:8080/dashboard/"
echo ""
echo "✅ No HTTPS redirect on this port!"
echo ""
echo "Press Ctrl+C to stop"
echo "======================================================"
echo ""

cd coda

DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runserver 0.0.0.0:8080



