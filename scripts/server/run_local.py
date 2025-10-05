#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CODA Local Development Startup Script

This script starts the CODA application in local development mode
with Redis dependencies disabled for testing.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start the local development server."""
    print("Starting CODA Local Development Server")
    print("=" * 50)
    
    # Add the app directory to Python path
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if app_dir not in sys.path:
        sys.path.insert(0, app_dir)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.minimal_local_settings')
    
    # Change to the app directory
    os.chdir(app_dir)
    
    # Setup Django
    django.setup()
    
    print("Django setup complete")
    print("Email backend: Console (check terminal output)")
    print("Database: SQLite (db.sqlite3)")
    print("Cache: Local memory cache")
    print("Server will start at: http://localhost:8000")
    print()
    
    # Run the development server
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\nShutting down local development server...")
        sys.exit(0)

if __name__ == "__main__":
    main()