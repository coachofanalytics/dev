"""
Django settings for coda_project project.
"""
import os
import sys
import dj_database_url
from celery.schedules import crontab

# FIXED: BASE_DIR now points to the project root (where manage.py is)
# This prevents the FileNotFoundError on Heroku
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ["*"]

AUTH_USER_MODEL = "accounts.CustomerUser"

AUTHENTICATION_BACKENDS = (
    "accounts.custom_backend.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# Application definition
INSTALLED_APPS = [
    "main.apps.MainConfig",
    "departments",
    "accounts.apps.AccountsConfig",
    "finance",
    "investments",
    "application.apps.ApplicationConfig",
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
    "django_celery_beat",
    "django_celery_results",
    "django_crontab",
    "django.contrib.sites",
    "allauth",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

CRONJOBS = [
    ("* * * * *", "application.msg_send_cron.SendMsgApplicatUser"),
    ("*/5 * * * *", "management.cron.advertisement"),
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # ✅ Corrected Position for Heroku
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "Middleware.MiddlewareFile.MailMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

CSRF_COOKIE_SECURE = False
ROOT_URLCONF = "coda_project.urls"

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ============== DB FUNCTIONS =====================================
def dba_values():
    env = os.environ.get('ENVIRONMENT')
    if env == 'production':
        return os.environ.get('HEROKU_PROD_HOST'), os.environ.get('HEROKU_PROD_NAME'), os.environ.get('HEROKU_PROD_USER'), os.environ.get('HEROKU_PROD_PASS')
    return os.environ.get('STG_DB_HOST'), os.environ.get('STG_DB_NAME'), os.environ.get('STG_DB_USER'), os.environ.get('STG_DB_PASSWORD')

WSGI_APPLICATION = "coda_project.wsgi.application"

host, dbname, user, password = dba_values()

# Database Configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'coda_dev'
    }

# Heroku DB override
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

# Password Validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ==================== STATIC FILES CONFIGURATION ====================
STATIC_URL = "/static/"

# Points to the folder Heroku will create during 'collectstatic'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# FIXED: Points to your source 'static' folder in the root directory
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Prevents build failure if CSS references missing images/files
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
# ====================================================================

CRISPY_TEMPLATE_PACK = "bootstrap4"
LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = "smtp.privateemail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "emails")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# AWS S3 Settings
AWS_S3_REGION_NAME = "us-east-2"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

# Celery Settings
CELERY_BROKER_URL = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
CELERY_RESULT_BACKEND = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_IMPORTS = "coda_project.task"

CELERYBEAT_SCHEDULE = {
    "task_history_1st": {
        "task": "task_history",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
    "advertisement_1st": {
        "task": "advertisement",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
}

# ================== ENVIRONMENT & STORAGE LOGIC ==================
ENV = os.environ.get('ENVIRONMENT')

if ENV == 'production':
    SITEURL = "https://www.codanalytics.net"
    SECURE_SSL_REDIRECT = True
    DEBUG = False
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
elif ENV == 'testing':
    SITEURL = "https://codamakutano.herokuapp.com"
    SECURE_SSL_REDIRECT = True
    DEBUG = True
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
else:
    SITEURL = "http://127.0.0.1:8000"
    DEBUG = True
    # Standard storage for local development
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Social Auth Settings
SITE_ID = 1
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = 'accounts.views.CustomSocialAccountAdapter'
SOCIALACCOUNT_PROVIDERS = {
    "google": {"SCOPE": ["profile", "email"], "AUTH_PARAMS": {"access_type": "online"}},
    "facebook": {"SCOPE": ["public_profile", "email"], "AUTH_PARAMS": {"access_type": "online"}},
}

# Mpesa Settings
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_PASSWORD = os.environ.get('MPESA_PASSWORD')
MPESA_TIMESTAMP = os.environ.get('MPESA_TIMESTAMP')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')