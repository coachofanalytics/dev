"""
Local development settings for coda_project.
Development-specific configurations that override base_settings.

DATABASE CONFIGURATION:
=======================

By default, this file uses a CLONED production database for safe local development.

USAGE OPTIONS:
--------------

1. **CLONED DATABASE (RECOMMENDED)** ⭐
   - Uses local PostgreSQL clone of production
   - Safe to test with real production data
   - Isolated from production (no risk!)
   
   Setup:
   ```powershell
   # Run once to clone production database
   .\scripts\clone_prod_database.ps1
   
   # Then just run Django normally (default behavior)
   cd coda
   python manage.py runserver
   ```
   
   Environment variable: DB_TYPE='clone' (default)

2. **SQLITE DATABASE**
   - Lightweight, file-based database
   - Good for quick testing without PostgreSQL
   
   Usage:
   ```powershell
   $env:DB_TYPE = 'sqlite'
   cd coda
   python manage.py runserver
   ```

3. **UAT DATABASE** (NOT recommended)
   - Connects to Heroku UAT database
   - Requires UAT_DATABASE_URL environment variable
   
   Usage:
   ```powershell
   $env:DB_TYPE = 'uat'
   $env:UAT_DATABASE_URL = 'postgres://...'
   cd coda
   python manage.py runserver
   ```

4. **PRODUCTION DATABASE** ⚠️ NEVER USE FOR TESTING!
   - Connects to real production database
   - DANGEROUS - test changes affect real users!
   
   To prevent accidents, we default to 'clone' now.
   
   Only use if you absolutely must:
   ```powershell
   $env:DB_TYPE = 'prod'
   $env:PROD_DATABASE_URL = 'postgres://...'
   cd coda
   python manage.py runserver
   ```

QUICK REFERENCE:
----------------
- Default: 'clone' (safe cloned production database)
- Switch: Set $env:DB_TYPE = 'sqlite' or 'uat' or 'prod'
- Verify: Check startup logs for database connection details

For complete guide: docs/LOCAL_DEVELOPMENT_WITH_PROD_DATA.md
"""


import os
import sys

from .base_settings import *


# Override environment for local development
ENV_CONFIG['environment'] = 'local'
ENV_CONFIG['is_development'] = True
ENV_CONFIG['is_testing'] = False
ENV_CONFIG['is_production'] = False


# Local development specific settings
DEBUG = True
SECURE_SSL_REDIRECT = False


# Enhanced Database Configuration for Local Development
# Supports multiple database backends with environment variable control


def get_database_config():
    """
    Get database configuration based on environment variables
    Supports: 
    - 'clone': Local PostgreSQL clone of production (RECOMMENDED for development)
    - 'sqlite': Local SQLite (default, lightweight)
    - 'uat': Heroku UAT database (NOT recommended for local dev)
    - 'prod': Heroku Production database (NEVER use for local dev!)
    - 'postgres': Custom local PostgreSQL
    """
    TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'
    db_type_env = os.environ.get('DB_TYPE', '').strip().lower()

    if TEST_MODE:
        print("   🧪 TEST_MODE detected — using in-memory SQLite database")
        return get_sqlite_config(memory=True)

    DB_TYPE = db_type_env or 'clone'
    print("🗄️  DB_TYPE: ", DB_TYPE)
    USE_POSTGRESQL = os.environ.get('USE_POSTGRESQL', 'False').lower() == 'true'
   
    # Database URLs from environment
    UAT_DATABASE_URL = os.environ.get('UAT_DATABASE_URL')  # Heroku UAT
    PROD_DATABASE_URL = os.environ.get('PROD_DATABASE_URL')  # Heroku Production
    LOCAL_POSTGRES_URL = os.environ.get('LOCAL_POSTGRES_URL')  # Local PostgreSQL
   
    print("🗄️ Database Configuration:")
    print(f"   DB_TYPE: {DB_TYPE}")
    print(f"   USE_POSTGRESQL: {USE_POSTGRESQL}")
   
    # RECOMMENDED: Use cloned production database
    if DB_TYPE == 'clone':
        print("   ✅ Using CLONED production database (safe for development)")
        return get_clone_config()
   
    # Determine which database to use
    if DB_TYPE in ['uat', 'prod', 'postgres'] or USE_POSTGRESQL:
        # PostgreSQL configuration
        if DB_TYPE == 'uat' and UAT_DATABASE_URL:
            db_url = UAT_DATABASE_URL
            db_name = "UAT (Heroku)"
        elif DB_TYPE == 'prod' and PROD_DATABASE_URL:
            db_url = PROD_DATABASE_URL
            db_name = "Production (Heroku)"
        elif DB_TYPE == 'postgres' and LOCAL_POSTGRES_URL:
            db_url = LOCAL_POSTGRES_URL
            db_name = "Local PostgreSQL"
        elif USE_POSTGRESQL and UAT_DATABASE_URL:
            # Fallback: USE_POSTGRESQL=true with UAT URL
            db_url = UAT_DATABASE_URL
            db_name = "UAT (Heroku) - Fallback"
        elif USE_POSTGRESQL and PROD_DATABASE_URL:
            # Fallback: USE_POSTGRESQL=true with Production URL
            db_url = PROD_DATABASE_URL
            db_name = "Production (Heroku) - Fallback"
        elif USE_POSTGRESQL and LOCAL_POSTGRES_URL:
            # Fallback: USE_POSTGRESQL=true with Local PostgreSQL URL
            db_url = LOCAL_POSTGRES_URL
            db_name = "Local PostgreSQL - Fallback"
        else:
            print("   ⚠️  No PostgreSQL URL found, falling back to SQLite")
            return get_sqlite_config()
       
        try:
            import dj_database_url
            db_config = dj_database_url.parse(db_url, conn_max_age=600, ssl_require=True)
            print(f"   ✅ Connected to {db_name}")
            print(f"   📍 Host: {db_config.get('HOST', 'Unknown')}")
            print(f"   📍 Database: {db_config.get('NAME', 'Unknown')}")
            return {
                'default': db_config
            }
        except ImportError:
            print("   ❌ dj_database_url not installed, falling back to SQLite")
            return get_sqlite_config()
        except Exception as e:
            print(f"   ❌ PostgreSQL connection failed: {e}")
            print("   🔄 Falling back to SQLite")
            return get_sqlite_config()
   
    else:
        # SQLite configuration (default)
        return get_sqlite_config()


def get_clone_config():
    """
    Get configuration for local cloned production database
    This is the RECOMMENDED setup for local development
    """
    print("   🎯 Using cloned production database")
    print("   📍 Database: coda_prod_clone")
    print("   📍 Host: localhost (PostgreSQL)")
    print("   ✅ Safe to test - isolated from production!")
    
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'coda_prod_clone',
            'USER': 'postgres',  # Default Windows PostgreSQL user
            'PASSWORD': 'MANAGER2030',  # Update if you set a password
            'HOST': 'localhost',
            'PORT': '5432',
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
            }
        }
    }


def get_sqlite_config(memory: bool = False):
    """Get SQLite database configuration"""
    print("   📁 Using SQLite database for local development")
    db_name = ':memory:' if memory else os.path.join(BASE_DIR, 'db.sqlite3')
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': db_name,
            'CONN_MAX_AGE': 0,
        }
    }


# Apply database configuration
DATABASES = get_database_config()

# For test runs, switch to in-memory SQLite to avoid Postgres permission issues
if 'test' in sys.argv:
    DATABASES = get_sqlite_config()

# Display database info
print("   " + "="*50)
print("   🗄️  Database Details:")
print(f"      Engine: {DATABASES['default']['ENGINE']}")
print(f"      Name: {DATABASES['default']['NAME']}")

if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    print(f"      Location: {DATABASES['default']['NAME']}")
else:
    # PostgreSQL database
    print(f"      Host: {DATABASES['default'].get('HOST', 'N/A')}")
    print(f"      Port: {DATABASES['default'].get('PORT', 'N/A')}")
    print(f"      User: {DATABASES['default'].get('USER', 'N/A')}")
    
    # Warn if using production database
    db_name = DATABASES['default']['NAME']
    if 'prod' in db_name.lower() or 'd5ts3j5r06arts' in db_name:
        print("   " + "="*50)
        print("   ⚠️  WARNING: Using PRODUCTION database!")
        print("   ⚠️  This is DANGEROUS - test changes will affect real users!")
        print("   ⚠️  RECOMMENDED: Use DB_TYPE='clone' instead")
        print("   " + "="*50)
    elif db_name == 'coda_prod_clone':
        print("      ✅ SAFE: Using cloned database (isolated from production)")

print("   " + "="*50)
# Email settings for local development
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"


# Allauth settings for local development - no email verification required
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_AUTO_SIGNUP = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_USERNAME_REQUIRED = False


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


# Static files for local development
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"


# Logging for local development
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Local development specific settings
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '0.0.0.0',
]


# Cache settings for local development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}


# Email settings for local development
DEFAULT_FROM_EMAIL = 'noreply@localhost'
SERVER_EMAIL = 'noreply@localhost'


# Performance settings for local development
CONN_MAX_AGE = 0


# Local development middleware
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


# Stripe Configuration for Local Development
# Note: You need BOTH publishable key (pk_test_) and secret key (sk_test_)
# Get both from: https://dashboard.stripe.com/test/apikeys
STRIPE_PUBLISHABLE_KEY="pk_test_51RcwhrFmZDMqLvNl5ygyIvt8p17GZdWi52WJku1ScwWyUpe3QwTfWErhqLXI6AHdxVtytJ7LKtJv3IKp2ewViJ9l00DDQ9p39l"
STRIPE_SECRET_KEY="sk_test_51RtbJqKUqxKl3Yd1NhS4QouYBhKWbogQiL0MgCNXukX7wyMY4hM7Ta7VQkJA3cTtK59oBTUMWsM4sbS347n6sIAt00Xu17hXyf"
STRIPE_WEBHOOK_SECRET="whsec_58c6ae18b2d10387771d5788818e91cb5e8ad0746f79714cfe78fbfb2b210b02"


# Stripe settings (will use environment variables if set)
# STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', '')
# STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY', '')
# STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')


print("💳 Stripe Configuration:")
print(f"   Publishable Key: {'Set' if STRIPE_PUBLISHABLE_KEY else 'Not Set'}")
print(f"   Secret Key: {'Set' if STRIPE_SECRET_KEY else 'Not Set'}")
print(f"   Webhook Secret: {'Set' if STRIPE_WEBHOOK_SECRET else 'Not Set'}")
if not STRIPE_PUBLISHABLE_KEY:
    print("   ⚠️  Set STRIPE_PUBLISHABLE_KEY environment variable for Stripe testing")


# Payment method configurations for testing
PAYMENT_METHODS = {
    'stripe': {
        'test_mode': True,
        'sandbox': True,
        'description': 'Test with Stripe sandbox - use test card numbers'
    }
}


# Test card numbers for Stripe sandbox
STRIPE_TEST_CARDS = {
    'visa': '4242424242424242',
    'visa_debit': '4000056655665556',
    'mastercard': '5555555555554444',
    'amex': '378282246310005',
    'declined': '4000000000000002',
    'insufficient_funds': '4000000000009995',
    'expired': '4000000000000069',
    'cvc_fail': '4000000000000127',
}


print("💳 Stripe Configuration:")
print(f"   Publishable Key: {'Set' if STRIPE_PUBLISHABLE_KEY else 'Not Set'}")
print(f"   Secret Key: {'Set' if STRIPE_SECRET_KEY else 'Not Set'}")
print(f"   Webhook Secret: {'Set' if STRIPE_WEBHOOK_SECRET else 'Not Set'}")
if not STRIPE_PUBLISHABLE_KEY:
    print("   ⚠️  Set STRIPE_PUBLISHABLE_KEY environment variable for Stripe testing")


# Local development settings loaded - configuration complete
