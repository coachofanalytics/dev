# settings
"""
Django settings for coda_project project.
"""
import os
import os
from dotenv import load_dotenv

load_dotenv()  # Load .env file

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============ENVIRONMENT CONFIGURATION=====================================
def get_environment_config():
    """Centralized environment configuration similar to database configuration"""
    environment = os.environ.get('ENVIRONMENT', 'local')

    print(environment)
    
    config = {
        'environment': environment,
        'is_development': environment in ['local', 'development'],
        'is_testing': environment == 'testing',
        'is_production': environment == 'production',
        'is_heroku_uat': environment == 'testing',  # Heroku UAT is testing environment
    }
    
    # Email verification settings based on environment
    if config['is_development']:
        config['email_verification'] = {
            'required': False,
            'bypass_in_views': True,
            'auto_verify_on_registration': True,
            'auto_activate_on_registration': True,
        }

    elif config['is_testing']:
        config['email_verification'] = {
            'required': False,
            'bypass_in_views': True,
            'auto_verify_on_registration': True,
            'auto_activate_on_registration': True,
        }

    else:  # production
        config['email_verification'] = {
            'required': True,
            'bypass_in_views': False,
            'auto_verify_on_registration': False,
            'auto_activate_on_registration': False,
        }
    
    # Debug settings based on environment
    if config['is_development']:
        config['debug'] = True
        config['secure_ssl_redirect'] = False
    elif config['is_testing']:
        config['debug'] = True  # Keep True for Heroku UAT debugging
        config['secure_ssl_redirect'] = False
    else:  # production
        config['debug'] = False
        config['secure_ssl_redirect'] = True
    
    return config

# Get environment configuration
ENV_CONFIG = get_environment_config()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-o0nex4pd=)4xw07ww5w5a_gwz1pvavrs=vmd8!5^xg1f5ol*$!')

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = ["*"]

# Force disable SSL redirect for local development
SECURE_SSL_REDIRECT = False
AUTH_USER_MODEL = "accounts.CustomerUser"
AUTHENTICATION_BACKENDS = (("accounts.custom_backend.EmailOrUsernameModelBackend"), ("django.contrib.auth.backends.ModelBackend"))

# Application definition
INSTALLED_APPS = [
    "main.apps.MainConfig",
    "accounts.apps.AccountsConfig",
    "application.apps.ApplicationConfig",
    "professional_services.apps.ProfessionalServicesConfig",
    "ai_services.apps.AiServicesConfig",
    "investing.apps.InvestingConfig",
    "management.apps.ManagementConfig",
    "finance.apps.FinanceConfig",
    "marketing.apps.MarketingConfig",
    "unified_dashboard.apps.UnifiedDashboardConfig",
    "crispy_forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    "django_countries",
    "mathfilters",
    "mptt",
    "django_filters",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook"
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CRONJOBS = [
    # ("*/1 * * * *", "coda_project.cron.my_backup"),
    ("* * * * *", "application.msg_send_cron.SendMsgApplicatUser"),
    ("*/5 * * * *", "management.cron.advertisement"),
]

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

CSRF_COOKIE_SECURE = True  # Changed from False to True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
# SECURE_HSTS_SECONDS = 31536000
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True
# SECURE_HSTS_PRELOAD = True

# Additional security settings
SESSION_COOKIE_SECURE = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

ROOT_URLCONF = "coda_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            # os.path.join(BASE_DIR, 'templates')
            "templates"
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.images",
                "main.context_processors.googledriveurl",
                "main.context_processors.departments",
                "management.context_processors.categories",
                "management.context_processors.departments",
                "professional_services.context_processors.roles",
                "professional_services.context_processors.categories",
                "professional_services.context_processors.subcategories",
                "main.context_processors.services",
                "coda_project.url_config.url_context_processor",
                "main.context_processors.notifications",
            ],
            'libraries': {
                'customfilters': 'application.templatetags.customfilters',
            }
        },
    },
]


#  ==============DBFUNCTIONS=====================================
def dba_values():
    if os.environ.get('ENVIRONMENT') == 'production':
        host = os.environ.get('HEROKU_PROD_HOST')
        dbname = os.environ.get('HEROKU_PROD_NAME')
        user = os.environ.get('HEROKU_PROD_USER')
        password = os.environ.get('HEROKU_PROD_PASS')
    elif os.environ.get('ENVIRONMENT') == 'testing':
        # In Heroku/Postgres it is Heroku_UAT
        host = os.environ.get('HEROKU_DEV_HOST')
        dbname = os.environ.get('HEROKU_DEV_NAME')
        user = os.environ.get('HEROKU_DEV_USER')
        password = os.environ.get('HEROKU_DEV_PASS')
    else:
        host = os.environ.get('POSTGRES_DB_HOST')
        dbname = os.environ.get('POSTGRES_DB_NAME')
        user = os.environ.get('POSTGRES_DB_USER')
        password = os.environ.get('POSTGRES_DB_PASS')

    return host,dbname,user,password  

WSGI_APPLICATION = "coda_project.wsgi.application"
import dj_database_url

host,dbname,user,password=dba_values() #herokuprod() #herokudev() #dblocal()  #herokudev(),

# print(host,dbname,user,password)

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# Environment-based database configuration
if ENV_CONFIG['is_development']:
    # Use SQLite for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'coda_dev.db'),
            'OPTIONS': {
                'timeout': 20,  # 20 seconds timeout
            },
            'ATOMIC_REQUESTS': False,  # Disable atomic requests for SQLite
        }
    }
else:
    # Use PostgreSQL for testing and production
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": dbname,
            "USER": user,
            "PASSWORD": password,
            "HOST": host
        }
    }

# Database

# Default SQLite configuration for local development
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'coda_dev.db'),
#         'OPTIONS': {
#             'timeout': 20,  # 20 seconds timeout
#         },
#         'ATOMIC_REQUESTS': False,  # Disable atomic requests for SQLite
#     }
# }

# Add this for better concurrency
CONN_MAX_AGE = 0  # Close connections after each request

'''=========== Heroku DB ================'''
# Parse DATABASE_URL and completely replace database config for Heroku
db_from_env = dj_database_url.config(conn_max_age=600)
if db_from_env:
    # Create a clean database configuration for PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_from_env.get('NAME'),
            'USER': db_from_env.get('USER'),
            'PASSWORD': db_from_env.get('PASSWORD'),
            'HOST': db_from_env.get('HOST'),
            'PORT': db_from_env.get('PORT'),
            'CONN_MAX_AGE': 600,
        }
    }

import sys
# Use existing DB for tests and skip test DB creation
# TEST_RUNNER = 'coda_project.test_runner.NoDbTestRunner'  # Commented out - file doesn't exist
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Internationalization

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIR = os.path.join(BASE_DIR, "static")


CRISPY_TEMPLATE_PACK = "bootstrap4"

LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"


# private email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS')
EMAIL_PORT = os.environ.get('EMAIL_PORT')
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
EMAIL_FILE_PATH = BASE_DIR + "/emails"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

EMAIL_INFO = {
    'USER': os.environ.get('EMAIL_INFO_USER'),
    'PASS': os.environ.get('EMAIL_INFO_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': os.environ.get('EMAIL_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_USE_SSL'),
}

EMAIL_FIN = {
    'USER': os.environ.get('EMAIL_FIN_USER'),
    'PASS': os.environ.get('EMAIL_FIN_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': os.environ.get('EMAIL_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_USE_SSL'),
}

EMAIL_HR = {
    'USER': os.environ.get('EMAIL_HR_USER'),
    'PASS': os.environ.get('EMAIL_HR_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': os.environ.get('EMAIL_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_USE_SSL'),
}

AWS_S3_REGION_NAME = "us-east-2"  # change to your region
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

#==================PAYMENT SETTINGS=================
# Testing Payment methods

def payment_details(request):
    # ================MPESA/CASHAPP/VENMO========================
    phone_number = os.environ.get('MPESA_PHONE_NUMBER')
    email_info = os.environ.get('EMAIL_INFO_USER')
    cashapp = os.environ.get('CASHAPP')
    venmo = os.environ.get('VENMO')
    account_no = os.environ.get('STANBIC_ACCOUNT_NO')
    return phone_number, email_info, cashapp, venmo, account_no

# Environment-based settings (using centralized configuration)
if ENV_CONFIG['is_production']:
    SITEURL = "https://www.codanalytics.net"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
elif ENV_CONFIG['is_testing']:
    SITEURL = "https://codamakutano.herokuapp.com"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
else:  # development/local
    SITEURL = "http://127.0.0.1:8000"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedStaticFilesStorage"
    SECURE_HSTS_SECONDS = 0  # Disable HSTS for local development
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False

# Apply centralized configuration
DEBUG = ENV_CONFIG['debug']
SECURE_SSL_REDIRECT = ENV_CONFIG['secure_ssl_redirect']

# -----------------------------------------
def source_target():
    # Source
    source_host = os.environ.get('HEROKU_DEV_HOST')
    source_dbname = os.environ.get('HEROKU_DEV_NAME')
    source_user = os.environ.get('HEROKU_DEV_USER')
    source_password = os.environ.get('HEROKU_DEV_PASS')
    #Target                     
    target_db_path=os.environ.get('TARGET_PATH_PROD')
    return (source_host,source_dbname,source_user,source_password,target_db_path)

#######################################
# DAJNGO SOCIAL ALL AUTH LOGIN SETTING
#######################################

SITE_ID = 1
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'accounts.views.CustomSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email"
        ],
        "AUTH_PARAMS": {"access_type": "online"}
    },
    "facebook": {
        "SCOPE": [
            "public_profile",
            "email"
        ],
        "AUTH_PARAMS": {"access_type": "online"}
    },
}

#==================PAYMENT SETTINGS=================
# Testing Payment methods
PAYMENT_API_KEY = os.environ.get('PAYMENT_API_KEY')
PAYMENT_PROVIDER_ID = os.environ.get('PAYMENT_PROVIDER_ID')
PAYMENT_PROVIDER_SECRET = os.environ.get('PAYMENT_PROVIDER_SECRET')

PAYPAL_CLIENT_ID = os.environ.get('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.environ.get('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = os.environ.get('PAYPAL_MODE', 'sandbox')

STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY')
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY')

# settings.py
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_PASSWORD = os.environ.get('MPESA_PASSWORD')
MPESA_TIMESTAMP = os.environ.get('MPESA_TIMESTAMP')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')

ZEROBOUNCE_API_KEY = os.environ.get('ZEROBOUNCE_API_KEY')

# Environment variable validation
def validate_environment():
    """Validate that all required environment variables are set"""
    required_vars = [
        'ENVIRONMENT',  # Always required
    ]
    
    # Add environment-specific required variables
    if os.environ.get('ENVIRONMENT') == 'production':
        required_vars.extend([
            'HEROKU_PROD_HOST',
            'HEROKU_PROD_NAME', 
            'HEROKU_PROD_USER',
            'HEROKU_PROD_PASS',
        ])
    elif os.environ.get('ENVIRONMENT') == 'testing':
        required_vars.extend([
            'HEROKU_DEV_HOST',
            'HEROKU_DEV_NAME',
            'HEROKU_DEV_USER', 
            'HEROKU_DEV_PASS',
        ])
    
    # Add common required variables
    required_vars.extend([
        'EMAIL_HOST',
        'EMAIL_USER',
        'EMAIL_PASS',
    ])
    
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(f"WARNING: Missing required environment variables: {missing_vars}")
        print("Please check env_example.txt for required variables")
    
    return len(missing_vars) == 0

# Validate environment at startup
validate_environment()
# Allauth Configuration
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_AUTO_SIGNUP = True
ACCOUNT_SESSION_REMEMBER = True
ACCOUNT_SIGNUP_PASSWORD_ENTER_TWICE = True
ACCOUNT_USERNAME_BLACKLIST = []
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_USER_MODEL_REQUIRED_FIELDS = ['email']

# Allauth settings based on environment
if ENV_CONFIG['is_development'] or ENV_CONFIG['is_testing']:
    # Development/testing: auto-verify users
    ACCOUNT_EMAIL_VERIFICATION = 'none'
    ACCOUNT_EMAIL_REQUIRED = True  # Must be True when using email authentication
else:
    # Production: require email verification
    ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
    ACCOUNT_EMAIL_REQUIRED = True

LOGIN_URL = '/social_accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Force disable SSL redirect for local development (must be at the end)
SECURE_SSL_REDIRECT = False
