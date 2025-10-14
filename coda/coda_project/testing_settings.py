"""
Heroku/UAT settings for coda_project.
Extends base_settings with Heroku and UAT-specific configurations.
"""

from .base_settings import *
import dj_database_url

# Override environment for Heroku/UAT
ENV_CONFIG['environment'] = 'staging'
ENV_CONFIG['is_development'] = False
ENV_CONFIG['is_testing'] = False
ENV_CONFIG['is_production'] = False

# Heroku specific settings
DEBUG = True
SECURE_SSL_REDIRECT = False

# Database configuration for Heroku
def dba_values():
    """Get database values for Heroku environment"""
    host = os.environ.get('HEROKU_STG_HOST')
    dbname = os.environ.get('HEROKU_STG_NAME')
    user = os.environ.get('HEROKU_STG_USER')
    password = os.environ.get('HEROKU_STG_PASS')
    return host, dbname, user, password

host, dbname, user, password = dba_values()
print(f"Database values: {host}, {dbname}, {user}, {password}")
# Database - Use Heroku PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=True
    )
}

# Email settings for Heroku
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")

# Allauth settings for Heroku - require email verification
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTO_SIGNUP = False

# Disable security features for local development
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = False
SECURE_CONTENT_TYPE_NOSNIFF = False
X_FRAME_OPTIONS = 'SAMEORIGIN'
SECURE_REFERRER_POLICY = None

# Local development URLs
SITEURL = "http://127.0.0.1:8000"


# Static files for Heroku
STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"

# Logging for Heroku
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

# Heroku-specific settings
ALLOWED_HOSTS = [
    'codamakutano.herokuapp.com',
    'www.codanalytics.net',
    'codanalytics.net',
    'localhost',
    '127.0.0.1',
]

# Cache settings for Heroku
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email settings for Heroku
DEFAULT_FROM_EMAIL = os.environ.get("EMAIL_USER", 'noreply@codamakutano.herokuapp.com')
SERVER_EMAIL = os.environ.get("EMAIL_USER", 'noreply@codamakutano.herokuapp.com')

# Performance settings for Heroku
CONN_MAX_AGE = 600

# Security middleware for Heroku
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

print("=" * 50)
print("HEROKU SETTINGS LOADED")
print("=" * 50)
print(f"Environment: {ENV_CONFIG['environment']}")
print(f"Debug: {DEBUG}")
print(f"Database: Heroku PostgreSQL")
print(f"Email Backend: SMTP")
print(f"Email Verification: Required")
print(f"Site URL: {SITEURL}")
print(f"SSL Redirect: {SECURE_SSL_REDIRECT}")
print("=" * 50)