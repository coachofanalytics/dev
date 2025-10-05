#!/usr/bin/env python3
"""
CODA Local Development Server - Simple Version

This script provides a simple way to start the local development server
using the standard Django management approach.
"""

import os
import sys
import subprocess

def main():
    """Start the local development server."""
    print("🚀 Starting CODA Local Development Server")
    print("=" * 50)
    
    # Get the app directory (parent of scripts/server)
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Change to the app directory
    os.chdir(app_dir)
    
    print(f"📁 Working directory: {app_dir}")
    print("📧 Email backend: Console (check terminal output)")
    print("🗄️ Database: SQLite (db.sqlite3)")
    print("💾 Cache: Local memory cache")
    print("🌐 Server will start at: http://localhost:8000")
    print()
    
    try:
        # Run Django development server
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ], check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down local development server...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

