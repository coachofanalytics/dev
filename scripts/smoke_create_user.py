import os
import django
import sys
# Ensure project root is on sys.path so Django settings can be imported
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')
django.setup()
from accounts.models import CustomerUser
from django.contrib.auth import authenticate

# Create or get test user
username = 'smoke_test_user'
email = 'smoke_test_user@example.com'
password = 'TestPass123!'

user, created = CustomerUser.objects.get_or_create(username=username, defaults={
    'first_name': 'Smoke',
    'last_name': 'Tester',
    'email': email,
    'accepted_terms': True,
})
if created:
    user.set_password(password)
    user.save()
    print('User created:', user.username)
else:
    print('User exists:', user.username)

# Authenticate
user_auth = authenticate(username=username, password=password)
print('Authenticated:', bool(user_auth))
print('accepted_terms:', user.accepted_terms)
print('is_active:', user.is_active)
