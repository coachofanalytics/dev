#!/usr/bin/env python3
"""
CODA Server Startup Script

This script starts the CODA application server directly,
bypassing migration issues for local testing.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start the development server."""
    print("🚀 Starting CODA Development Server")
    print("=" * 50)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.local_settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django setup complete with local settings")
    print("💾 Using local memory cache (no Redis required)")
    print("🗄️ Using SQLite database")
    print("🌐 Server starting at: http://localhost:8000")
    print()
    
    # Start the development server
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")
        sys.exit(0)

if __name__ == "__main__":
    main()


