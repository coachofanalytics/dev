"""Minimal Django settings used only for running unit tests.

This file is intentionally isolated under dev/test so tests run without touching
the project's runtime settings and without requiring external services.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.environ.get('TEST_SECRET_KEY', 'test-secret-key-for-ci')
DEBUG = False

ALLOWED_HOSTS = ['localhost']

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
]

MIDDLEWARE = []

ROOT_URLCONF = None

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# Celery test-friendly config
CELERY_TASK_ALWAYS_EAGER = True
