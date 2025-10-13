#!/bin/bash

# Local Development Server Script
# This script ensures the correct environment is set for local development

echo "🚀 Starting local development server..."

# Activate virtual environment
source ../venv/bin/activate

# Set environment to local
export ENVIRONMENT=local

# Start Django development server
python manage.py runserver

echo "✅ Local development server started at http://127.0.0.1:8000/"
