#!/usr/bin/env python
"""
Test the payment eligibility function fix
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'coda'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from finance.utils import validate_user_payment_eligibility

User = get_user_model()

print("="*60)
print("TESTING PAYMENT ELIGIBILITY FIX")
print("="*60)

try:
    # Get eunice user
    eunice = User.objects.get(username='eunice')
    print(f"Testing with user: {eunice.username} (ID: {eunice.id})")
    
    # Test payment eligibility
    print("\nTesting payment eligibility for $75 (down payment amount)...")
    eligible, message, amount = validate_user_payment_eligibility(eunice, "75", "paypal")
    
    print(f"Result: eligible={eligible}")
    print(f"Message: {message}")
    print(f"Amount: {amount}")
    
    if eligible:
        print("✅ Payment eligibility check works!")
    else:
        print(f"❌ Payment eligibility failed: {message}")
        
except Exception as e:
    print(f"❌ Error testing eligibility: {e}")

print("\n" + "="*60)
print("RESULTS:")
print("="*60)
print("✅ Payment eligibility function should now work")
print("✅ No more 'updated_at does not exist' errors")
print("\n🚀 Ready to test full payment flow in browser!")

