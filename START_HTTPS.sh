#!/bin/bash
# Start HTTPS development server

cd coda
source ../venv/bin/activate

echo "🔒 Starting HTTPS Development Server..."
echo "Using settings: coda_project.coda_settings.local_settings"
echo ""

DJANGO_SETTINGS_MODULE=coda_project.coda_settings.local_settings \
python manage.py runsslserver \
  --certificate certs/cert.pem \
  --key certs/key.pem \
  0.0.0.0:8000

