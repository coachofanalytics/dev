#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

if not User.objects.filter(username='biasharaadmin').exists():
    User.objects.create_superuser(
        username='biasharaadmin',
        email='admin@biasharabridges.com',
        password='=vkMSOAF+4Et#'
    )
    print('Superuser created successfully!')
else:
    print('Superuser already exists.')
