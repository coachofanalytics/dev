"""
Heroku/UAT settings for coda_project.
Extends base_settings with Heroku and UAT-specific configurations.
"""

from .base_settings import *
import dj_database_url

# Override environment for Heroku/UAT
# ENV_CONFIG['environment'] = 'heroku'
ENV_CONFIG['is_development'] = False
ENV_CONFIG['is_testing'] = False
ENV_CONFIG['is_production'] = True

# Heroku specific settings
DEBUG = True  # Temporarily enabled for UAT debugging
SECURE_SSL_REDIRECT = True

# Database configuration for Heroku
def dba_values():
    """Get database values for Heroku environment"""
    host = os.environ.get('HEROKU_DEV_HOST')
    dbname = os.environ.get('HEROKU_DEV_NAME')
    user = os.environ.get('HEROKU_DEV_USER')
    password = os.environ.get('HEROKU_DEV_PASS')
    return host, dbname, user, password

host, dbname, user, password = dba_values()
print(f"Database values: {host}, {dbname}, {user}, {password}")
# Database - Use Heroku PostgreSQL
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('UAT_DATABASE_URL'),
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

# Security settings for Heroku/UAT
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

# Heroku URLs
SITEURL = os.environ.get('SITE_URL', 'https://codamakutano.herokuapp.com')

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
        'level': 'INFO',  # Changed from WARNING for UAT debugging
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',  # Changed from WARNING for UAT debugging
            'propagate': False,
        },
    },
}

# ====================================
# PAYMENT GATEWAY SETTINGS
# ====================================

# Stripe Configuration
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# PayPal Configuration
PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID', '')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET', '')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')  # 'sandbox' or 'live'

# Payment Gateway Details (for manual payments fallback)
PAYPAL_EMAIL = os.environ.get('PAYPAL_EMAIL', 'payments@codanalytics.net')
MPESA_PHONE_NUMBER = os.environ.get('MPESA_PHONE_NUMBER', '')
MPESA_PAYBILL = os.environ.get('MPESA_PAYBILL', '')
CASHAPP_USERNAME = os.environ.get('CASHAPP_USERNAME', '$codanalytics')
VENMO_USERNAME = os.environ.get('VENMO_USERNAME', '@codanalytics')
STANBIC_ACCOUNT_NO = os.environ.get('STANBIC_ACCOUNT_NO', '')
STANBIC_ROUTING = os.environ.get('STANBIC_ROUTING', '')
SWIFT_CODE = os.environ.get('SWIFT_CODE', '')

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

# Heroku settings loaded - configuration complete