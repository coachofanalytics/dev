#!/usr/bin/env python3
"""
CODA Local Server Startup Script

This script starts the CODA application server with local settings
to bypass Redis dependencies for local testing.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start the development server with local settings."""
    print("🚀 Starting CODA Local Development Server")
    print("=" * 50)
    
    # Set Django settings module to local settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.local_settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django setup complete with local settings")
    print("💾 Using local memory cache (no Redis required)")
    print("🗄️ Using SQLite database")
    print("🌐 Server starting at: http://localhost:8000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the development server
    try:
        execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

