"""
Local Development Settings
Supports multiple database configurations via environment variable

Set LOCAL_DB environment variable to choose database:
- LOCAL_DB=sqlite (default) - Use local SQLite database
- LOCAL_DB=uat - Connect to UAT/Heroku staging database
- LOCAL_DB=prod - Connect to production Heroku database

Example:
    LOCAL_DB=uat ./runserver_local.sh
    LOCAL_DB=prod python manage.py shell
"""

from .base_settings import *

# Debug mode ON for local development
DEBUG = True

# Local development hosts
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']

# ============================================
# DATABASE CONFIGURATION (Conditional)
# ============================================

# Get database choice from environment variable (default: sqlite)
LOCAL_DB = os.environ.get('LOCAL_DB', 'sqlite').lower()

print(f"🗄️  Database mode: {LOCAL_DB.upper()}")

if LOCAL_DB == 'sqlite':
    # ========== SQLITE (Default) ==========
    # Local SQLite database - no external dependencies
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    SITEURL = "http://localhost:8000"
    
    # Database helper functions (compatibility with ai_services)
    def dba_values():
        """Returns None values for SQLite"""
        return None, None, None, None
    
    def source_target():
        """Returns None values for SQLite"""
        return None, None, None, None, None
    
    print("   Using local SQLite database: db.sqlite3")

elif LOCAL_DB == 'uat' or LOCAL_DB == 'staging' or LOCAL_DB == 'heroku':
    # ========== UAT/STAGING (Heroku) ==========
    # Connect to UAT database on Heroku
    def dba_values():
        """Get UAT/staging database credentials from environment"""
        host = os.environ.get('HEROKU_DEV_HOST')
        dbname = os.environ.get('HEROKU_DEV_NAME')
        user = os.environ.get('HEROKU_DEV_USER')
        password = os.environ.get('HEROKU_DEV_PASS')
        return host, dbname, user, password
    
    def source_target():
        """Returns UAT database info"""
        host, dbname, user, password = dba_values()
        return host, dbname, user, password, None
    
    host, dbname, user, password = dba_values()
    
    if not all([host, dbname, user, password]):
        print("   ⚠️  WARNING: UAT database credentials not found in environment!")
        print("   Set: HEROKU_DEV_HOST, HEROKU_DEV_NAME, HEROKU_DEV_USER, HEROKU_DEV_PASS")
        print("   Falling back to SQLite...")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': dbname,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': '5432',
                'CONN_MAX_AGE': 600,
            }
        }
        print(f"   Connected to UAT database: {dbname} on {host}")
    
    SITEURL = "https://codamakutano.herokuapp.com"

elif LOCAL_DB == 'prod' or LOCAL_DB == 'production':
    # ========== PRODUCTION (Heroku) ==========
    # Connect to production database on Heroku
    def dba_values():
        """Get production database credentials from environment"""
        host = os.environ.get('HEROKU_PROD_HOST')
        dbname = os.environ.get('HEROKU_PROD_NAME')
        user = os.environ.get('HEROKU_PROD_USER')
        password = os.environ.get('HEROKU_PROD_PASS')
        return host, dbname, user, password
    
    def source_target():
        """Returns production database info"""
        host, dbname, user, password = dba_values()
        return host, dbname, user, password, None
    
    host, dbname, user, password = dba_values()
    
    if not all([host, dbname, user, password]):
        print("   ⚠️  WARNING: Production database credentials not found in environment!")
        print("   Set: HEROKU_PROD_HOST, HEROKU_PROD_NAME, HEROKU_PROD_USER, HEROKU_PROD_PASS")
        print("   Falling back to SQLite...")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': dbname,
                'USER': user,
                'PASSWORD': password,
                'HOST': host,
                'PORT': '5432',
                'CONN_MAX_AGE': 600,
                'OPTIONS': {
                    'sslmode': 'require',  # Required for Heroku PostgreSQL
                }
            }
        }
        print(f"   ⚠️  Connected to PRODUCTION database: {dbname} on {host}")
        print(f"   ⚠️  USE WITH CAUTION - You're modifying production data!")
    
    SITEURL = "https://codatrainingapp.herokuapp.com"

else:
    print(f"   ⚠️  Unknown LOCAL_DB value: {LOCAL_DB}")
    print("   Valid options: sqlite, uat, prod")
    print("   Falling back to SQLite...")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
        }
    }
    SITEURL = "http://localhost:8000"
    
    def dba_values():
        return None, None, None, None
    
    def source_target():
        return None, None, None, None, None

# ============================================
# COMMON SETTINGS (All Modes)
# ============================================

# Email backend for local development (console output)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Allauth configuration fixes for local development
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

# Django Debug Toolbar (optional)
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

# ============================================
# TESTING CONFIGURATION
# ============================================

if 'test' in sys.argv or 'test_coverage' in sys.argv:
    print("🧪 Running in TEST mode - using in-memory SQLite database")
    
    # Always use in-memory SQLite for tests (regardless of LOCAL_DB)
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

# ============================================
# STARTUP SUMMARY
# ============================================

print("✅ Local settings loaded for development")
print(f"   Database Engine: {DATABASES['default']['ENGINE']}")
if DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3':
    print(f"   Database File: {DATABASES['default']['NAME']}")
else:
    print(f"   Database Name: {DATABASES['default'].get('NAME', 'N/A')}")
    print(f"   Database Host: {DATABASES['default'].get('HOST', 'N/A')}")
print(f"   Debug Mode: {DEBUG}")
print(f"   Site URL: {SITEURL}")
print(f"   Allowed Hosts: {ALLOWED_HOSTS}")
print("")
