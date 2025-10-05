"""
Minimal Local Development Settings Configuration

This module contains minimal local development settings for the CODA application,
with all problematic dependencies disabled for basic testing.
"""

import os
from .settings import *

# ==============MINIMAL LOCAL DEVELOPMENT CONFIGURATION=====================================
# Minimal local development settings
DEBUG = True
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
    'testserver',  # For Django test client
]

# ==============MINIMAL DATABASE CONFIGURATION=====================================
# Minimal SQLite database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# ==============MINIMAL CACHE CONFIGURATION=====================================
# Minimal local memory cache configuration (no Redis required)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'TIMEOUT': 300,
    },
}

# ==============MINIMAL STATIC FILES CONFIGURATION=====================================
# Minimal static files configuration
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Minimal middleware (remove problematic middleware)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ==============MINIMAL EMAIL CONFIGURATION=====================================
# Minimal email configuration (console backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = 'noreply@localhost'

# ==============MINIMAL SECURITY CONFIGURATION=====================================
# Minimal security settings for local development
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# Session security (relaxed for local development)
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False
CSRF_COOKIE_HTTPONLY = True

# ==============MINIMAL LOGGING CONFIGURATION=====================================
# Minimal logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# ==============DISABLE PROBLEMATIC APPS=====================================
# Disable apps that might cause issues
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'accounts',
    'main',
    'finance',
    'investing',
    'management',
    'ai_services',
    'professional_services',
    'marketing',
    'unified_dashboard',
]

# ==============MINIMAL ENVIRONMENT VALIDATION=====================================
# Set default secret key for local development
if not os.environ.get('SECRET_KEY'):
    os.environ['SECRET_KEY'] = 'minimal-local-development-secret-key'

print("✅ Minimal local development settings loaded successfully!")
print("🚀 CODA application ready for minimal local testing!")
print("📧 Email will be sent to console (check terminal output)")
print("🗄️ Database: SQLite (db.sqlite3)")
print("💾 Cache: Local memory cache (no Redis required)")
print("🌐 Server: http://localhost:8000")

