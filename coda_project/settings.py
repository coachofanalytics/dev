import os
import sys
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
# print(BASE_DIR)

SECRET_KEY = os.environ.get("SECRET_KEY") or "!cxl7yhjsl00964n=#e-=xblp4u!hbajo2k8u#$v9&s6__5=xf"
# <<<<<<< HEAD
DEBUG = os.environ.get("DEBUG", "True") == "True"

ALLOWED_HOSTS = ["*"]
SECURE_SSL_REDIRECT = False
CSRF_COOKIE_SECURE = False

# =======

# Default to False unless explicitly enabled via environment variable.
DEBUG = os.environ.get("DEBUG", "False") == "True"
DEBUG = True

SECURE_SSL_REDIRECT = False

ALLOWED_HOSTS = ["*"]
# ALLOWED_HOSTS = ['127.0.0.1','localhost','codatrainingapp.herokuapp.com','www.codanalytics.net','codanalytics.net']
# ALLOWED_HOSTS = []

# AUTH_USER_MODEL = "accounts.User"
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
AUTH_USER_MODEL = "accounts.CustomerUser"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

INSTALLED_APPS = [
# <<<<<<< HEAD
    "document_portal",
    "healthcare_services",

# =======
    'document_processing',
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
    "main.apps.MainConfig",
    "accounts.apps.AccountsConfig",
    "finance.apps.FinanceConfig",

    "crispy_forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",

    "storages",
    "django_countries",
    "mathfilters",
    "mptt",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
# <<<<<<< HEAD

# =======
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.facebook",
# <<<<<<< HEAD

    # "django_crontab",
# =======
    "django_crontab",
    # 'memberjoin',
    # 'communities',
    #'debug_toolbar',

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
    'allauth.account.middleware.AccountMiddleware',
    # 'Middleware.MiddlewareFile.MailMiddleware'
    #'debug_toolbar.middleware.DebugToolbarMiddleware',

]

if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ['debug_toolbar']
        MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
    except ImportError:
        pass # If it's not installed, just don't use it


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Static files configuration
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'main/static'),
]

CRONJOBS = [
    # ("*/1 * * * *", "coda_project.cron.my_backup"),
    ("* * * * *", "application.msg_send_cron.SendMsgApplicatUser"),
    ("*/5 * * * *", "management.cron.advertisement"),
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
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
# <<<<<<< HEAD
    "allauth.account.middleware.AccountMiddleware",
# =======
    'allauth.account.middleware.AccountMiddleware',
    # 'Middleware.MiddlewareFile.MailMiddleware'
    #'debug_toolbar.middleware.DebugToolbarMiddleware',

# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
]

if DEBUG:
    try:
        import debug_toolbar
        INSTALLED_APPS += ["debug_toolbar"]
        MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
    except ImportError:
        pass

ROOT_URLCONF = "coda_project.urls"
WSGI_APPLICATION = "coda_project.wsgi.application"

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
# <<<<<<< HEAD
        "DIRS": ["templates"],
# =======
        "DIRS": [
            # os.path.join(BASE_DIR, 'templates')
            "templates"
        ],
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.images",
                "main.context_processors.googledriveurl",
                # "main.context_processors.services",
                # "main.context_processors.healthcare_images",
            ],
        },
    },
]

# <<<<<<< HEAD
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

if "test" in sys.argv:
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": "coda_dev",
    }
# =======
#  ==============DBFUNCTIONS=====================================
def dba_values():
    if os.environ.get('ENVIRONMENT') == 'production':
        host = os.environ.get('HEROKU_DYCPROD_HOST')
        dbname = os.environ.get('HEROKU_DYCPROD_NAME')
        user = os.environ.get('HEROKU_DYCPROD_USER')
        password = os.environ.get('HEROKU_DYCPROD_PASS')
    elif os.environ.get('ENVIRONMENT') == 'staging':
        # In Heroku/Postgres it is Heroku_UAT
        host = os.environ.get('HEROKU_DYCDEV_HOST')
        dbname = os.environ.get('HEROKU_DYCDEV_NAME')
        user = os.environ.get('HEROKU_DYCDEV_USER')
        password = os.environ.get('HEROKU_DYCDEV_PASS')
    else:
        host = os.environ.get('HEROKU_DEV_HOST')
        dbname = os.environ.get('HEROKU_DEV_NAME')
        user = os.environ.get('HEROKU_DEV_USER')
        password = os.environ.get('HEROKU_DEV_PASS')
        # host = os.environ.get('POSTGRES_DB_NAME')
        # dbname = "CODA_PRACTICE" #os.environ.get('POSTGRES_DB_NAME') 
        # user = os.environ.get('POSTGRESDB_USER')
        # password = os.environ.get('POSTGRESSPASS') 
    return host,dbname,user,password  

WSGI_APPLICATION = "coda_project.wsgi.application"
import dj_database_url

host,dbname,user,password=dba_values() #herokuprod() #herokudev() #dblocal()  #herokudev(),
# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": dbname,
#         "USER":user,
#         "PASSWORD":password,
#         "HOST": host
#     }
# }

# Local DB
# DATABASES = {
#     'default': {
#         "ENGINE": 'django.db.backends.postgresql',
#         "NAME": 'd2l066ajig78uh',
#         "USER": 'uf4o5nponalopo',
#         "PASSWORD": 'p2f315d6b9430b965799ae1813941756fa47e03c99328df5d063d7049455884a1',
#         "HOST": 'ce0lkuo944ch99.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com',  
#     }
# }
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR,"db.sqlite3"),
    
    }
}
import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'coda_dev'
    }

# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1

db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
# <<<<<<< HEAD
# =======
    # Use secure, production-appropriate password hashers. MD5 is insecure and should not be used.
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "main/static"),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# <<<<<<< HEAD
STATICFILES_STORAGE = (
    "django.contrib.staticfiles.storage.StaticFilesStorage"
    if DEBUG
    else "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"
)
# =======
STATIC_ROOT = os.path.join(BASE_DIR,  "staticfiles")
STATIC_URL = "/static/"


if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1

CRISPY_TEMPLATE_PACK = "bootstrap4"

LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"

SITE_ID = 1

# <<<<<<< HEAD
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
SOCIALACCOUNT_QUERY_EMAIL = True
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_ADAPTER = "accounts.views.CustomSocialAccountAdapter"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
    "facebook": {
        "SCOPE": ["public_profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    },
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "your-email@gmail.com"
EMAIL_HOST_PASSWORD = "your-16-character-app-password"
DEFAULT_FROM_EMAIL = "your-email@gmail.com"
ADMIN_EMAIL = "your-email@gmail.com"
# =======
# EMAIL_FILE_PATH = BASE_DIR + "/emails"

# Gmail Email Backend Account
# EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
# EMAIL_HOST = "smtp.gmail.com"
# EMAIL_HOST_USER = "hunjin015@gmail.com"

# private email
# EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
# EMAIL_USE_SSL = False
# EMAIL_USE_TLS = True
# EMAIL_PORT = 587
# EMAIL_HOST = "smtp.privateemail.com"
# EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
# EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
# EMAIL_FILE_PATH = BASE_DIR + "/emails"

# DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1

SITE_URL = "http://127.0.0.1:8000"

# <<<<<<< HEAD
if os.environ.get("ENVIRONMENT") == "production":
    SITEURL = "https://www.codanalytics.net"
elif os.environ.get("ENVIRONMENT") == "testing":
    SITEURL = "https://codamakutano.herokuapp.com"
else:
    SITEURL = "http://localhost:8000"
# =======
EMAIL_INFO = {
    'USER': os.environ.get('EMAIL_INFO_USER'),
    'PASS': os.environ.get('EMAIL_INFO_PASS'),
    'HOST': os.environ.get('EMAIL_HOST'),
    'PORT': os.environ.get('EMAIL_PORT'),
    'USE_TLS': os.environ.get('EMAIL_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_USE_SSL'),
}
EMAIL_HR = {
    'USER': os.environ.get('EMAIL_HR_USER'),
    'PASS': os.environ.get('EMAIL_HR_PASS'),
    'HOST': os.environ.get('EMAIL_HR_HOST'),
    'PORT': os.environ.get('EMAIL_HR_PORT'),
    'USE_TLS': os.environ.get('EMAIL_HR_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_HR_USE_SSL'),
}
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1

EMAIL_INFO = {
    "USER": os.environ.get("EMAIL_INFO_USER"),
    "PASS": os.environ.get("EMAIL_INFO_PASS"),
    "HOST": os.environ.get("EMAIL_HOST"),
    "PORT": os.environ.get("EMAIL_PORT"),
    "USE_TLS": os.environ.get("EMAIL_USE_TLS"),
    "USE_SSL": os.environ.get("EMAIL_USE_SSL"),
}

EMAIL_HR = {
    "USER": os.environ.get("EMAIL_HR_USER"),
    "PASS": os.environ.get("EMAIL_HR_PASS"),
    "HOST": os.environ.get("EMAIL_HR_HOST"),
    "PORT": os.environ.get("EMAIL_HR_PORT"),
    "USE_TLS": os.environ.get("EMAIL_HR_USE_TLS"),
    "USE_SSL": os.environ.get("EMAIL_HR_USE_SSL"),
}

AWS_S3_REGION_NAME = "us-east-2"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None

from celery.schedules import crontab

# <<<<<<< HEAD
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "")
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_IMPORTS = ("coda_project.task",)

CELERYBEAT_SCHEDULE = {
    "task_history_monthly": {
        "task": "task_history",
        "schedule": crontab(0, 0, day_of_month="1"),
    }}
# =======
from celery.schedules import crontab

CELERY_BROKER_URL = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
CELERY_RESULT_BACKEND = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_IMPORTS = "coda_project.task"

CELERYBEAT_SCHEDULE = {
    "run_on_every_1st": {
        "task": "task_history",
        "schedule": crontab(0, 0, day_of_month="1"),
        #'schedule': crontab(),
    },

    "run_on_every_1st": {
        "task": "advertisement",
        "schedule": crontab(0, 0, day_of_month="1"),
        #'schedule': crontab(),
    },
}

#==================PAYMENT SETTINGS=================
# Testing Payment methods
def payment_details(request):
    # ================MPESA/CASHAPP/VENMO========================
    phone_number =os.environ.get('MPESA_PHONE_NUMBER')
    email_info =os.environ.get('EMAIL_INFO_USER')
    cashapp = os.environ.get('CASHAPP'),
    venmo= os.environ.get('VENMO'),
    account_no = os.environ.get('STANBIC_ACCOUNT_NO'),
    return (phone_number,email_info,cashapp,venmo,account_no)
    #==================STRIPE SETTINGS=================
STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

#==================PAYMENT SETTINGS=================


if os.environ.get('ENVIRONMENT') == 'production':
    SITEURL = "https://www.codanalytics.net"
elif os.environ.get('ENVIRONMENT') == 'testing':
   SITEURL = "https://codamakutano.herokuapp.com"
else:
    SITEURL = "http://localhost:8000"

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
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
    },
    "advertisement_monthly": {
        "task": "advertisement",
        "schedule": crontab(0, 0, day_of_month="1"),
    },
}

# <<<<<<< HEAD
CRONJOBS = [
    ("* * * * *", "application.msg_send_cron.SendMsgApplicatUser"),
    ("*/5 * * * *", "management.cron.advertisement"),
]
# =======
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # or 'mandatory', depending on your setup
ACCOUNT_SIGNUP_FIELDS = ['email*', 'username*', 'password1*', 'password2*']
SOCIALACCOUNT_QUERY_EMAIL = True
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1

STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'  # Your full Gmail address
EMAIL_HOST_PASSWORD = 'your-16-character-app-password'  # The app password you generated (remove spaces)
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
ADMIN_EMAIL = 'your-email@gmail.com'  # Send admin notifications to yourself for testing

# <<<<<<< HEAD
def payment_details(request):
    phone_number = os.environ.get("MPESA_PHONE_NUMBER")
    email_info = os.environ.get("EMAIL_INFO_USER")
    cashapp = os.environ.get("CASHAPP")
    venmo = os.environ.get("VENMO")
    account_no = os.environ.get("STANBIC_ACCOUNT_NO")

    return (phone_number, email_info, cashapp, venmo, account_no)
# =======
# Site URL for email links
SITE_URL = 'http://127.0.0.1:8000'
# >>>>>>> 6b38594f704780076e59319dcf0696de541774a1
