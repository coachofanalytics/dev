import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

username = 'fadhir'
email = 'ndegeyafadhiri@gmail.com'
password = 'Biashara123'

u = User.objects.filter(username=username).first()
if u:
    print('User already exists:', u.username)
else:
    u = User.objects.create_user(username, email, password)
    u.first_name = 'Fadhir'
    u.last_name = 'Ndegeya'
    u.is_active = True
    u.save()
    # Populate profile if available (UserProfile is auto-created via signal)
    profile = getattr(u, 'profile', None)
    if profile:
        profile.company_name = 'Biashara Bridges'
        profile.job_title = 'Founder'
        profile.country = 'Kenya'
        profile.phone = '+2547000000'
        profile.location = 'Nairobi, Kenya'
        profile.bio = 'Auto-created account for testing.'
        profile.save()
    print('Created user:', u.username)
