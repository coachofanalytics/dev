"""
WSGI config for coda_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

# Check if we're running on Heroku
if 'DYNO' in os.environ:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.coda_settings.heroku_settings')
else:
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'coda_project.settings')

application = get_wsgi_application()
