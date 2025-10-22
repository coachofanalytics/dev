#!/bin/bash

# HTTPS Development Server for Local Development
# Uses local_settings.py with SQLite database

echo "🔒 Starting CODA Local HTTPS Development Server"
echo "================================================"
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
echo "   SSL Cert: coda/certs/cert.pem"
echo "   SSL Key:  coda/certs/key.pem"
echo ""

# Check for SSL certificates
if [ ! -f "coda/certs/cert.pem" ] || [ ! -f "coda/certs/key.pem" ]; then
    echo "❌ ERROR: SSL certificates not found!"
    echo ""
    echo "Generate them with:"
    echo "  cd coda/certs"
    echo "  openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj \"/C=KE/ST=Nairobi/L=Nairobi/O=CODA/CN=localhost\""
    exit 1
fi

echo "✅ SSL certificates found"
echo ""

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "❌ ERROR: Virtual environment not found at venv/"
    exit 1
fi

# Check if django-sslserver is installed
if ! python -c "import sslserver" 2>/dev/null; then
    echo "⚠️  django-sslserver not installed. Installing..."
    pip install django-sslserver
    echo "✅ django-sslserver installed"
fi

echo ""
echo "🚀 Starting HTTPS server..."
echo "================================================"
echo ""
echo "Access your site at:"
echo "  👉 https://localhost:8000/"
echo "  👉 https://localhost:8000/portfolio/"
echo "  👉 https://localhost:8000/interview/"
echo ""
echo "⚠️  Browser Security Warning (Expected):"
echo "   Your browser will show a warning about self-signed certificate"
echo "   This is NORMAL and SAFE for local development"
echo "   Click: Advanced → Proceed to localhost"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================================"
echo ""

# Change to coda directory
cd coda

# Run HTTPS server with explicit settings module
DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runsslserver \
  --certificate certs/cert.pem \
  --key certs/key.pem \
  0.0.0.0:8000

