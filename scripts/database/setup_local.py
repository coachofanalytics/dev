#!/usr/bin/env python3
"""
CODA Local Development Setup Script

This script sets up the local development environment
with database migrations and initial data.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

def main():
    """Setup local development environment."""
    print("🚀 Setting up CODA Local Development Environment")
    print("=" * 60)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.local_settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django setup complete with local settings")
    print("💾 Using local memory cache (no Redis required)")
    print("🗄️ Using SQLite database")
    print()
    
    try:
        # Run database migrations
        print("📊 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--settings=coda_project.local_settings'])
        print("✅ Database migrations completed")
        
        # Collect static files
        print("📁 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--settings=coda_project.local_settings'])
        print("✅ Static files collected")
        
        # Create superuser (optional)
        print("👤 Creating superuser...")
        print("You can skip this by pressing Ctrl+C")
        try:
            execute_from_command_line(['manage.py', 'createsuperuser', '--settings=coda_project.local_settings'])
            print("✅ Superuser created")
        except KeyboardInterrupt:
            print("⏭️ Superuser creation skipped")
        
        print("\n🎉 Local development environment setup complete!")
        print("=" * 60)
        print("🚀 To start the development server:")
        print("   python3 run_local.py")
        print()
        print("🧪 To run tests:")
        print("   python3 test_local.py")
        print()
        print("🌐 Application will be available at:")
        print("   http://localhost:8000")
        print("   http://localhost:8000/admin/")
        print("   http://localhost:8000/api/v1/schema/swagger-ui/")
        
    except Exception as e:
        print(f"❌ Setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()


