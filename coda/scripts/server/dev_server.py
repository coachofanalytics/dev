#!/usr/bin/env python3
"""
CODA Development Server - Ultra Minimal Version

This script starts the development server using the standard Django approach
with minimal configuration to avoid dependency issues.
"""

import os
import sys
import subprocess

def main():
    """Start the development server."""
    print("🚀 Starting CODA Development Server")
    print("=" * 50)
    
    # Get the app directory
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # Change to the app directory
    os.chdir(app_dir)
    
    print(f"📁 Working directory: {app_dir}")
    print("🌐 Server will start at: http://localhost:8000")
    print("📧 Email: Console backend")
    print("🗄️ Database: SQLite")
    print()
    
    try:
        # Set environment variable for ultra minimal settings
        env = os.environ.copy()
        env['DJANGO_SETTINGS_MODULE'] = 'coda_project.ultra_minimal_settings'
        
        # Run Django development server
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down development server...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error starting server: {e}")
        print("\n💡 Try running: python manage.py runserver 0.0.0.0:8000")
        sys.exit(1)

if __name__ == "__main__":
    main()
