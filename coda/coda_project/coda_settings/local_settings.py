"""
Local Development Settings
For running the application locally and for testing
"""

from .base_settings import *

# Debug mode ON for local development
DEBUG = True

# Local development hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# Use SQLite for local development (easier setup, no PostgreSQL required)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Or use PostgreSQL if you have it set up locally:
# Uncomment and configure if you want to use local PostgreSQL
"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'coda_dev',
        'USER': 'postgres',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
"""

# Email backend for local development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allauth configuration fixes for local development
# Override base_settings to avoid assertion errors
ACCOUNT_EMAIL_VERIFICATION = 'none'  # Skip email verification locally
ACCOUNT_EMAIL_REQUIRED = True  # Required by allauth
SOCIALACCOUNT_EMAIL_REQUIRED = False

# Disable HTTPS redirects for local development
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Static files (for local development)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Django SSL Server for local HTTPS development
INSTALLED_APPS = INSTALLED_APPS + ['sslserver']

# SSL Certificate paths
SSL_CERTIFICATE = os.path.join(BASE_DIR, 'certs', 'cert.pem')
SSL_KEY = os.path.join(BASE_DIR, 'certs', 'key.pem')

# Django Debug Toolbar (optional - install with pip install django-debug-toolbar)
try:
    import debug_toolbar
    INSTALLED_APPS = INSTALLED_APPS + ['debug_toolbar']
    MIDDLEWARE = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE
    INTERNAL_IPS = ['127.0.0.1', 'localhost']
except ImportError:
    pass

# Celery settings for local development (synchronous execution)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Logging configuration for local development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs.log'),
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
        'finance': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
        'management': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        },
    },
}

# Testing settings
if 'test' in sys.argv or 'test_coverage' in sys.argv:
    print("🧪 Running in TEST mode - using in-memory SQLite database")
    
    # Use in-memory SQLite for faster tests
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    
    # Disable migrations for faster tests
    class DisableMigrations:
        def __contains__(self, item):
            return True
        def __getitem__(self, item):
            return None
    
    MIGRATION_MODULES = DisableMigrations()
    
    # Speed up password hashing in tests
    PASSWORD_HASHERS = [
        'django.contrib.auth.hashers.MD5PasswordHasher',
    ]
    
    # Disable debug toolbar in tests
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: False,
    }
    
    # Test-specific logging (less verbose)
    LOGGING['loggers']['django']['level'] = 'WARNING'
    LOGGING['loggers']['finance']['level'] = 'WARNING'

print("✅ Local settings loaded for development")
print(f"   Database: {DATABASES['default']['ENGINE']}")
print(f"   Debug: {DEBUG}")
print(f"   Allowed Hosts: {ALLOWED_HOSTS}")

