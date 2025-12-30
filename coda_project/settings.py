import os
import sys
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ["*"]

# ==================== APPS & AUTH ====================
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
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
]

AUTH_USER_MODEL = "accounts.CustomerUser"
AUTHENTICATION_BACKENDS = (
    "accounts.custom_backend.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# ==================== MIDDLEWARE ====================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Must be after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "Middleware.MiddlewareFile.MailMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

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

WSGI_APPLICATION = "coda_project.wsgi.application"

# ==================== DATABASE ====================
# Default PK type to BigAutoField (Fixes models.W042 warnings)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Apply Heroku database configuration
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

# ==================== STATIC & MEDIA ====================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# FIXED: Plural STATICFILES_DIRS is required for Django to find your static folder
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# FIXED: Prevents "MissingFileError" from crashing the Heroku build
WHITENOISE_MANIFEST_STRICT = False

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# ==================== ENVIRONMENT LOGIC ====================
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
    # Local Development
    SITEURL = "http://127.0.0.1:8000"
    DEBUG = True
    STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# ==================== REMAINING CONFIG ====================
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True
SITE_ID = 1

# Email, Celery, and other settings follow as per your requirements...