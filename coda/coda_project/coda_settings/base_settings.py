"""
Base Django settings for coda_project project.
Common settings shared across all environments.
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()  # Load .env file

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TEST_MODE = os.environ.get('TEST_MODE', 'False').lower() == 'true'

# ==============ENVIRONMENT CONFIGURATION=====================================
def get_environment_config():
    """Centralized environment configuration - basic environment detection only"""
    environment = os.environ.get('ENVIRONMENT', 'local')
    config = {
        'environment': environment,
        'is_development': environment in ['local', 'development'],
        'is_testing': environment == 'testing',
        'is_production': environment == 'production',
        'is_heroku_uat': environment == 'testing',  # Heroku UAT is testing environment
    }
    return config

# Get environment configuration
ENV_CONFIG = get_environment_config()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-o0nex4pd=)4xw07ww5w5a_gwz1pvavrs=vmd8!5^xg1f5ol*$!')

# SECURITY WARNING: don't run with debug turned on in production!
ALLOWED_HOSTS = ["*"]

# SSL redirect is now environment-specific
AUTH_USER_MODEL = "accounts.CustomerUser"
AUTHENTICATION_BACKENDS = (("accounts.custom_backend.EmailOrUsernameModelBackend"), ("django.contrib.auth.backends.ModelBackend"))

# Application definition
INSTALLED_APPS = [
    "shared_core.apps.SharedCoreConfig",  # Shared core package - must be first
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
    "portfolio.apps.PortfolioConfig",  # Professional presentations & portfolio
    "shareholders.apps.ShareholdersConfig",  # Shareholders Management System
    "crispy_forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
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
    "allauth.socialaccount.providers.facebook",
    "platform_services",
]


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CRONJOBS = [
    # ("*/1 * * * *", "coda_project.cron.my_backup"),
    ("* * * * *", "application.msg_send_cron.SendMsgApplicatUser"),
    ("*/5 * * * *", "management.cron.advertisement"),
]

# Silence known admin check pending cleanup in finance admin configuration
SILENCED_SYSTEM_CHECKS = [
    'admin.E109',
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
    "Middleware.track_user_middleware.TrackUserMiddleware",  # Track user for signals
]

# Security settings are now environment-specific
# See local_settings.py, prod_settings.py, and heroku_settings.py

ROOT_URLCONF = "coda_project.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
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

WSGI_APPLICATION = "coda_project.wsgi.application"

# Database configuration will be set in environment-specific settings
# Add this for better concurrency
CONN_MAX_AGE = 0  # Close connections after each request

import sys
# Use existing DB for tests and skip test DB creation
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
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATIC_URL = "/static/"

# Additional locations of static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# WhiteNoise configuration for serving static files in production
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

CRISPY_TEMPLATE_PACK = "bootstrap4"

LOGIN_REDIRECT_URL = "dashboard:unified_dashboard"
LOGIN_URL = "accounts:account-login"

# Email configuration
logger = logging.getLogger(__name__)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


_email_use_tls = _env_bool('EMAIL_USE_TLS')
_email_use_ssl = _env_bool('EMAIL_USE_SSL')

# Enforce mutual exclusivity; prefer TLS by default.
if _email_use_tls and _email_use_ssl:
    logger.warning("EMAIL_USE_TLS and EMAIL_USE_SSL were both truthy; disabling SSL to prefer TLS.")
    _email_use_ssl = False

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = _email_use_ssl
EMAIL_USE_TLS = _email_use_tls
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
    'USE_TLS': _email_use_tls,
    'USE_SSL': _email_use_ssl,
}

EMAIL_FIN = {
    'USER': os.environ.get('EMAIL_FIN_USER'),
    'PASS': os.environ.get('EMAIL_FIN_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': _email_use_tls,
    'USE_SSL': _email_use_ssl,
}

EMAIL_HR = {
    'USER': os.environ.get('EMAIL_HR_USER'),
    'PASS': os.environ.get('EMAIL_HR_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': _email_use_tls,
    'USE_SSL': _email_use_ssl,
}

# AWS S3 Configuration
AWS_S3_REGION_NAME = "us-east-2"  # change to your region
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

#==================PAYMENT SETTINGS=================
def payment_details(request):
    # ================MPESA/CASHAPP/VENMO========================
    phone_number = os.environ.get('MPESA_PHONE_NUMBER')
    email_info = os.environ.get('EMAIL_INFO_USER')
    cashapp = os.environ.get('CASHAPP')
    venmo = os.environ.get('VENMO')
    account_no = os.environ.get('STANBIC_ACCOUNT_NO')
    return phone_number, email_info, cashapp, venmo, account_no

# Environment-specific settings (SITEURL, DEBUG, SECURE_SSL_REDIRECT, etc.) 
# are now configured in their respective environment settings files

# -----------------------------------------
def source_target():
    """Get source and target database configuration for data migration"""
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
STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or os.environ.get('STRIPE_TEST_SECRET_KEY')
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET') or os.environ.get('STRIPE_TEST_WEBHOOK_SECRET')

def _mask_secret(value: str, label: str) -> None:
    """Print a masked version of sensitive keys for debugging in non-production environments."""
    try:
        if value:
            masked = f"{value[:6]}…{value[-4:]}" if len(value) > 10 else value
            print(f"[Stripe] Loaded {label}: {masked}")
        else:
            print(f"[Stripe] {label} not configured")
    except Exception:
        print(f"[Stripe] Unable to display {label}")

if os.environ.get('ENVIRONMENT', '').lower() != 'production':
    _mask_secret(STRIPE_SECRET_KEY, "secret key")
    _mask_secret(STRIPE_WEBHOOK_SECRET, "webhook secret")

# settings.py
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_PASSWORD = os.environ.get('MPESA_PASSWORD')
MPESA_TIMESTAMP = os.environ.get('MPESA_TIMESTAMP')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')

ZEROBOUNCE_API_KEY = os.environ.get('ZEROBOUNCE_API_KEY')

# Unusual Whales API Configuration (Investing App)
UNUSUAL_WHALES_API_KEY = os.environ.get('UNUSUAL_WHALES_API_KEY')
UNUSUAL_WHALES_ENABLED = os.environ.get('UNUSUAL_WHALES_ENABLED', 'False').lower() in ('true', '1', 'yes')
ZAPIER_POSITION_WEBHOOK = os.environ.get('ZAPIER_POSITION_WEBHOOK')
ZAPIER_ALERT_WEBHOOK = os.environ.get('ZAPIER_ALERT_WEBHOOK')
ZAPIER_WEBHOOK_TOKEN = os.environ.get('ZAPIER_WEBHOOK_TOKEN')
MANAGED_INCOME_DIGEST_GROUP = os.environ.get('MANAGED_INCOME_DIGEST_GROUP', 'Managed Income Digest')
SUGGESTED_POSITION_TTL_MINUTES = int(os.environ.get('SUGGESTED_POSITION_TTL_MINUTES', '90'))
SUGGESTED_POSITION_MIN_RATING = os.environ.get('SUGGESTED_POSITION_MIN_RATING', 'EXCELLENT')
BALANCED_TIER_MONTHLY_FEE = os.environ.get('BALANCED_TIER_MONTHLY_FEE', '249')
ELITE_TIER_MONTHLY_FEE = os.environ.get('ELITE_TIER_MONTHLY_FEE', '399')

# Environment variable validation is now handled in environment-specific settings files

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

# Allauth settings are now configured in environment-specific settings files

LOGIN_URL = '/social_accounts/login/'
LOGIN_REDIRECT_URL = 'dashboard:unified_dashboard'
LOGOUT_REDIRECT_URL = 'dashboard:unified_dashboard'

# SSL redirect is now environment-specific

# -----------------------------
# Twilio / Messaging configuration
# -----------------------------
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')

TRADER_ALERT_PHONES = os.environ.get('TRADER_ALERT_PHONES', '')
WHATSAPP_ENABLED = _env_bool('WHATSAPP_ENABLED', False)
