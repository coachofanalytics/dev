#!/usr/bin/env python3
"""
CODA Minimal Server Startup Script

This script starts the CODA application server with minimal settings
for basic local testing.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Start the development server with minimal settings."""
    print("🚀 Starting CODA Minimal Development Server")
    print("=" * 50)
    
    # Set Django settings module to minimal settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.minimal_settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django setup complete with minimal settings")
    print("💾 Using local memory cache (no Redis required)")
    print("🗄️ Using SQLite database")
    print("🌐 Server starting at: http://127.0.0.1:8000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Start the development server
    try:
        execute_from_command_line(['manage.py', 'runserver', '127.0.0.1:8000'])
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

