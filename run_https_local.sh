#!/bin/bash

# Run Django development server with HTTPS/SSL
# This script runs the local development server with SSL certificates

echo "🔒 Starting Django HTTPS Development Server..."
echo "--------------------------------------------"

# Activate virtual environment
source venv/bin/activate

# Check if certificates exist
if [ ! -f "coda/certs/cert.pem" ] || [ ! -f "coda/certs/key.pem" ]; then
    echo "❌ SSL certificates not found!"
    echo "Run this command to generate them:"
    echo "cd coda/certs && openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes"
    exit 1
fi

# Change to coda directory
cd coda

# Set Django settings module for local development
export DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings

# Run SSL server
echo "✅ SSL certificates found"
echo "✅ Using local_settings.py"
echo "📡 Starting server on https://localhost:8000/"
echo "⚠️  Your browser will show a security warning (self-signed certificate)"
echo "   Click 'Advanced' -> 'Proceed to localhost' to continue"
echo ""
echo "Press Ctrl+C to stop the server"
echo "--------------------------------------------"

python manage.py runsslserver --certificate certs/cert.pem --key certs/key.pem 0.0.0.0:8000

