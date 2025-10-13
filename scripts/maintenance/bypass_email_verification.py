#!/usr/bin/env python3
"""
Email Verification Bypass Script

This script helps bypass email verification for testing and development.
It provides multiple methods to disable email verification requirements.
"""

import os
import sys
import django
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from accounts.models import CustomerUser
from django.contrib.auth import get_user_model

User = get_user_model()

def bypass_email_verification_for_user(username_or_email):
    """Bypass email verification for a specific user"""
    try:
        # Try to find user by username first, then email
        try:
            user = CustomerUser.objects.get(username=username_or_email)
        except CustomerUser.DoesNotExist:
            try:
                user = CustomerUser.objects.get(email=username_or_email)
            except CustomerUser.DoesNotExist:
                print(f"❌ User not found: {username_or_email}")
                return False
        
        # Bypass email verification
        user.email_verified = True
        user.is_active = True
        user.save()
        
        print(f"✅ Email verification bypassed for user: {user.username} ({user.email})")
        print(f"   - Email verified: {user.email_verified}")
        print(f"   - Account active: {user.is_active}")
        return True
        
    except Exception as e:
        print(f"❌ Error bypassing email verification: {e}")
        return False

def bypass_email_verification_for_all_users():
    """Bypass email verification for all users"""
    try:
        users = CustomerUser.objects.all()
        count = 0
        
        for user in users:
            if not user.email_verified:
                user.email_verified = True
                user.is_active = True
                user.save()
                count += 1
                print(f"✅ Bypassed verification for: {user.username} ({user.email})")
        
        print(f"\n📊 Summary: Bypassed email verification for {count} users")
        return True
        
    except Exception as e:
        print(f"❌ Error bypassing email verification for all users: {e}")
        return False

def create_test_user_without_verification(username, email, password, category=None):
    """Create a test user without email verification requirements"""
    try:
        # Check if user already exists
        if CustomerUser.objects.filter(username=username).exists():
            print(f"ℹ️  User already exists: {username}")
            return CustomerUser.objects.get(username=username)
        
        if CustomerUser.objects.filter(email=email).exists():
            print(f"ℹ️  Email already exists: {email}")
            return CustomerUser.objects.get(email=email)
        
        # Create user
        user = CustomerUser.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=username.title(),
            last_name='Test',
            email_verified=True,  # Skip verification
            is_active=True        # Activate immediately
        )
        
        # Set category if provided
        if category:
            user.category = category
            user.save()
        
        print(f"✅ Created test user: {username} ({email})")
        print(f"   - Email verified: {user.email_verified}")
        print(f"   - Account active: {user.is_active}")
        print(f"   - Category: {user.category if hasattr(user, 'category') else 'None'}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating test user: {e}")
        return None

def show_verification_status():
    """Show current email verification status for all users"""
    try:
        users = CustomerUser.objects.all()
        
        print("📊 Current Email Verification Status:")
        print("=" * 60)
        print(f"{'Username':<20} {'Email':<30} {'Verified':<10} {'Active':<10}")
        print("-" * 60)
        
        for user in users:
            print(f"{user.username:<20} {user.email:<30} {str(user.email_verified):<10} {str(user.is_active):<10}")
        
        print("=" * 60)
        
        # Summary statistics
        total_users = users.count()
        verified_users = users.filter(email_verified=True).count()
        active_users = users.filter(is_active=True).count()
        
        print(f"📈 Summary:")
        print(f"   Total users: {total_users}")
        print(f"   Verified users: {verified_users}")
        print(f"   Active users: {active_users}")
        print(f"   Unverified users: {total_users - verified_users}")
        
    except Exception as e:
        print(f"❌ Error showing verification status: {e}")

def update_settings_for_development():
    """Update Django settings to disable email verification"""
    print("🔧 To disable email verification in Django settings, add these lines to your settings.py:")
    print()
    print("# Email verification bypass for development")
    print("ACCOUNT_EMAIL_VERIFICATION = 'none'")
    print("ACCOUNT_EMAIL_REQUIRED = False")
    print("EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'")
    print()
    print("Or create a development settings file and use:")
    print("python manage.py runserver --settings=coda_project.settings_dev")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print("🚀 Email Verification Bypass Tool")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python bypass_email_verification.py <command> [arguments]")
        print()
        print("Commands:")
        print("  bypass <username_or_email>  - Bypass verification for specific user")
        print("  bypass-all                 - Bypass verification for all users")
        print("  create <username> <email> <password> [category] - Create test user")
        print("  status                     - Show verification status")
        print("  settings                   - Show settings instructions")
        print()
        print("Examples:")
        print("  python bypass_email_verification.py bypass admin_test")
        print("  python bypass_email_verification.py bypass-all")
        print("  python bypass_email_verification.py create testuser test@example.com password123 investor")
        print("  python bypass_email_verification.py status")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'bypass':
        if len(sys.argv) < 3:
            print("❌ Please provide username or email")
            return
        username_or_email = sys.argv[2]
        bypass_email_verification_for_user(username_or_email)
    
    elif command == 'bypass-all':
        bypass_email_verification_for_all_users()
    
    elif command == 'create':
        if len(sys.argv) < 5:
            print("❌ Please provide username, email, and password")
            return
        username = sys.argv[2]
        email = sys.argv[3]
        password = sys.argv[4]
        category = sys.argv[5] if len(sys.argv) > 5 else None
        create_test_user_without_verification(username, email, password, category)
    
    elif command == 'status':
        show_verification_status()
    
    elif command == 'settings':
        update_settings_for_development()
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == '__main__':
    main()



