"""
Django settings for coda_project
"""
import os
import sys
from pathlib import Path
import dj_database_url
from celery.schedules import crontab

# -------------------------------------------------------------------
# BASE
# -------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "unsafe-dev-key")
DEBUG = os.environ.get("DEBUG", "True") == "True"
ALLOWED_HOSTS = ["*"]

# -------------------------------------------------------------------
# AUTH
# -------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.CustomerUser"

AUTHENTICATION_BACKENDS = (
    "accounts.custom_backend.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

# -------------------------------------------------------------------
# APPS
# -------------------------------------------------------------------
INSTALLED_APPS = [
    "main.apps.MainConfig",
    "accounts.apps.AccountsConfig",
    "application.apps.ApplicationConfig",
    "finance",
    "investments",
    "django.contrib.humanize",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "crispy_forms",
    "django_filters",
    "django_countries",
    "mathfilters",
    "mptt",
    "storages",

    "django_celery_beat",
    "django_celery_results",
    "django_crontab",

    "django.contrib.sites",
    "allauth",
]

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

SITE_ID = 1

# -------------------------------------------------------------------
# MIDDLEWARE
# -------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # MUST be here
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

# -------------------------------------------------------------------
# TEMPLATES
# -------------------------------------------------------------------
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.images",
                "main.context_processors.googledriveurl",
                "main.context_processors.services",
            ],
        },
    },
]

ROOT_URLCONF = "coda_project.urls"
WSGI_APPLICATION = "coda_project.wsgi.application"

# -------------------------------------------------------------------
# DATABASE
# -------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=False,
    )
}

if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",
    }

# -------------------------------------------------------------------
# PASSWORDS
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# -------------------------------------------------------------------
# I18N
# -------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# STATIC / MEDIA (FIXED)
# -------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

STATICFILES_DIRS = [
    BASE_DIR / "main" / "static",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

WHITENOISE_MANIFEST_STRICT = False

# -------------------------------------------------------------------
# LOGIN
# -------------------------------------------------------------------
LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"

CRISPY_TEMPLATE_PACK = "bootstrap4"

# -------------------------------------------------------------------
# EMAIL
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = "smtp.privateemail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# -------------------------------------------------------------------
# CELERY
# -------------------------------------------------------------------
CELERY_BROKER_URL = os.environ.get("REDIS_URL")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"

CELERYBEAT_SCHEDULE = {
    "monthly_advertisement": {
        "task": "advertisement",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
}

# -------------------------------------------------------------------
# SECURITY (ENV BASED)
# -------------------------------------------------------------------
ENV = os.environ.get("ENVIRONMENT", "local")

if ENV == "production":
    DEBUG = False
    SECURE_SSL_REDIRECT = True
    SITEURL = "https://www.codanalytics.net"
else:
    DEBUG = True
    SECURE_SSL_REDIRECT = False
    SITEURL = "http://127.0.0.1:8000"
