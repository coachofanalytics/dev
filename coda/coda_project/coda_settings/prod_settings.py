"""
Production settings for coda_project.
Production-specific configurations that override base_settings.
Note: base_settings is imported in the main settings.py file
"""

from .base_settings import *

# Override environment for production
ENV_CONFIG['environment'] = 'production'
ENV_CONFIG['is_development'] = False
ENV_CONFIG['is_testing'] = False
ENV_CONFIG['is_production'] = True

# Production specific settings
DEBUG = False
SECURE_SSL_REDIRECT = True

# Database configuration for production
def dba_values():
    """Get database values for production environment"""
    host = os.environ.get('HEROKU_PROD_HOST')
    dbname = os.environ.get('HEROKU_PROD_NAME')
    user = os.environ.get('HEROKU_PROD_USER')
    password = os.environ.get('HEROKU_PROD_PASS')
    return host, dbname, user, password

host, dbname, user, password = dba_values()

# Database - Use PostgreSQL for production
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": dbname,
        "USER": user,
        "PASSWORD": password,
        "HOST": host,
        "CONN_MAX_AGE": 600,
    }
}

# Email settings for production
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")

# Allauth settings for production - require email verification
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTO_SIGNUP = False

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Production URLs
SITEURL = "https://www.codanalytics.net"

# Static files for production
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Logging for production (Heroku-compatible)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Production-specific settings
ALLOWED_HOSTS = [
    'www.codanalytics.net',
    'codanalytics.net',
    'codatrainingapp.herokuapp.com',
    'localhost',
    '127.0.0.1',
]

# Cache settings for production
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email settings for production
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_USER", 'noreply@codanalytics.net')
SERVER_EMAIL = os.environ.get("EMAIL_USER", 'noreply@codanalytics.net')

# Performance settings for production
CONN_MAX_AGE = 600

# Security middleware for production
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'Middleware.MiddlewareFile.MailMiddleware',
    "allauth.account.middleware.AccountMiddleware",
]

# Production settings loaded - configuration complete