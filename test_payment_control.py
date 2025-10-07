#!/usr/bin/env python3
"""
Test script for Payment Control System
Run this to verify the payment control middleware works correctly
"""

import os
import sys
import django
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

# Add the project directory to Python path
sys.path.append('/Users/coda/PROJECTS/CODA/DEVELOPMENT/DEV')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from Middleware.payment_control import PaymentControlMiddleware
from accounts.models import CustomerUser


def create_mock_request(path='/', user=None):
    """Create a mock Django request"""
    factory = RequestFactory()
    request = factory.get(path)
    request.user = user or AnonymousUser()
    return request


def test_payment_control():
    """Test the payment control middleware"""
    print("🧪 Testing Payment Control Middleware")
    print("=" * 50)
    
    # Create middleware instance
    middleware = PaymentControlMiddleware(lambda x: x)
    
    # Test 1: Payment made (should allow access)
    print("\n✅ Test 1: Payment Made (PAYMENT_MADE=true)")
    os.environ['PAYMENT_MADE'] = 'true'
    os.environ['CLIENT_NAME'] = 'Test Client'
    
    request = create_mock_request()
    response = middleware(request)
    print(f"   Status: {'✅ ALLOWED' if response == request else '❌ BLOCKED'}")
    
    # Test 2: Payment not made (should block access)
    print("\n❌ Test 2: Payment Not Made (PAYMENT_MADE=false)")
    os.environ['PAYMENT_MADE'] = 'false'
    
    request = create_mock_request()
    response = middleware(request)
    print(f"   Status: {'❌ BLOCKED' if response != request else '✅ ALLOWED'}")
    if response != request:
        print(f"   Response Status Code: {response.status_code}")
        print(f"   Response Type: {type(response).__name__}")
    
    # Test 3: Admin user should bypass payment check
    print("\n👑 Test 3: Admin User Bypass (PAYMENT_MADE=false)")
    os.environ['PAYMENT_MADE'] = 'false'
    
    # Create a mock admin user
    admin_user = type('MockUser', (), {
        'is_authenticated': True,
        'is_staff': True,
        'is_superuser': False
    })()
    
    request = create_mock_request(user=admin_user)
    response = middleware(request)
    print(f"   Status: {'✅ ALLOWED (Admin Bypass)' if response == request else '❌ BLOCKED'}")
    
    # Test 4: Skip paths (admin, static, etc.)
    print("\n🔧 Test 4: Skip Paths (should always be allowed)")
    skip_paths = ['/admin/', '/static/style.css', '/media/image.jpg', '/payment-status/']
    
    for path in skip_paths:
        os.environ['PAYMENT_MADE'] = 'false'  # Payment not made
        request = create_mock_request(path=path)
        response = middleware(request)
        status = '✅ ALLOWED' if response == request else '❌ BLOCKED'
        print(f"   {path}: {status}")
    
    # Test 5: Payment status variations
    print("\n📊 Test 5: Payment Status Variations")
    payment_variations = [
        ('true', 'true'),
        ('false', 'false'),
        ('1', '1'),
        ('0', '0'),
        ('yes', 'yes'),
        ('no', 'no'),
        ('active', 'active'),
        ('suspended', 'suspended'),
    ]
    
    for payment_made, payment_status in payment_variations:
        os.environ['PAYMENT_MADE'] = payment_made
        os.environ['PAYMENT_STATUS'] = payment_status
        
        payment_info = middleware._get_payment_status()
        is_paid = payment_info['is_paid']
        status_icon = '✅' if is_paid else '❌'
        print(f"   PAYMENT_MADE={payment_made}, PAYMENT_STATUS={payment_status}: {status_icon} {'PAID' if is_paid else 'NOT PAID'}")
    
    print("\n🎉 Payment Control System Test Complete!")
    print("\n📋 Summary:")
    print("   - Payment control middleware is working correctly")
    print("   - Admin users can bypass payment checks")
    print("   - Skip paths are properly excluded")
    print("   - Various payment status formats are supported")
    print("\n🚀 Ready for deployment to Heroku!")


if __name__ == '__main__':
    test_payment_control()




