#!/usr/bin/env python3
"""
CODA Database Setup Script

This script sets up the database with migrations and initial data
for local testing.
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.contrib.auth import get_user_model

def main():
    """Setup database with migrations and initial data."""
    print("🗄️ Setting up CODA Database")
    print("=" * 50)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.local_settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django setup complete")
    print("💾 Using local memory cache (no Redis required)")
    print("🗄️ Using SQLite database")
    print()
    
    try:
        # Run database migrations
        print("📊 Running database migrations...")
        execute_from_command_line(['manage.py', 'migrate', '--settings=coda_project.local_settings'])
        print("✅ Database migrations completed")
        
        # Create superuser
        print("👤 Creating superuser...")
        User = get_user_model()
        
        # Check if superuser already exists
        if not User.objects.filter(is_superuser=True).exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin123',
                category=1  # Admin category
            )
            print("✅ Superuser created (username: admin, password: admin123)")
        else:
            print("✅ Superuser already exists")
        
        # Create test users for different categories
        print("👥 Creating test users...")
        
        test_users = [
            {'username': 'regular_user', 'email': 'regular@example.com', 'password': 'password123', 'category': 2},
            {'username': 'loan_officer', 'email': 'loan@example.com', 'password': 'password123', 'category': 3},
            {'username': 'financial_advisor', 'email': 'advisor@example.com', 'password': 'password123', 'category': 4},
            {'username': 'hr_manager', 'email': 'hr@example.com', 'password': 'password123', 'category': 5},
            {'username': 'analyst', 'email': 'analyst@example.com', 'password': 'password123', 'category': 6},
        ]
        
        for user_data in test_users:
            if not User.objects.filter(username=user_data['username']).exists():
                User.objects.create_user(**user_data)
                print(f"✅ Created {user_data['username']}")
            else:
                print(f"✅ {user_data['username']} already exists")
        
        # Collect static files
        print("📁 Collecting static files...")
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput', '--settings=coda_project.local_settings'])
        print("✅ Static files collected")
        
        print("\n🎉 Database setup complete!")
        print("=" * 50)
        print("🚀 To start the development server:")
        print("   python3 start_local_server.py")
        print()
        print("👤 Test users created:")
        print("   Admin: admin / admin123")
        print("   Regular User: regular_user / password123")
        print("   Loan Officer: loan_officer / password123")
        print("   Financial Advisor: financial_advisor / password123")
        print("   HR Manager: hr_manager / password123")
        print("   Analyst: analyst / password123")
        print()
        print("🌐 Application will be available at:")
        print("   http://127.0.0.1:8000")
        print("   http://127.0.0.1:8000/admin/")
        print("   http://127.0.0.1:8000/api/v1/schema/swagger-ui/")
        
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()

