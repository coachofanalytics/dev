"""
Django settings for coda_project project.
"""
import os
import sys
import dj_database_url

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = os.environ.get('SECRET_KEY')
ALLOWED_HOSTS = ["*"]

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

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Whitenoise MUST be here
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

# ==================== DATABASE CONFIGURATION ====================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

# Heroku Database update
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

# Test environment database
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'coda_analytics'
    }

# ==================== STATIC & MEDIA FILES ====================
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# FIXED: Plural name and list format
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# WhiteNoise settings to prevent deployment failure
WHITENOISE_MANIFEST_STRICT = False

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

# ==================== AUTH & EMAIL ====================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.privateemail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ==================== OTHER SETTINGS ====================
SITE_ID = 1
CRISPY_TEMPLATE_PACK = "bootstrap4"
LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"

# (Celery and Social Auth settings remain at the bottom as per your original file)