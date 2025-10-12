# settings
"""
Django settings for coda_project project.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SECRET_KEY = "!cxl7yhjsl00964n=#e-=xblp4u!hbajo2k8u#$v9&s6__5=xf"
ALLOWED_HOSTS = ["*"]
AUTH_USER_MODEL = "accounts.CustomerUser"
AUTHENTICATION_BACKENDS = (("accounts.custom_backend.EmailOrUsernameModelBackend"), ("django.contrib.auth.backends.ModelBackend"), ("allauth.account.auth_backends.AuthenticationBackend"))

# Application definition
INSTALLED_APPS = [
    'main.apps.MainConfig',  # ✅ Also OK (but not both)
    "accounts.apps.AccountsConfig",
    "application.apps.ApplicationConfig",   # ✅ keep this
    "crispy_forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django_extensions",
    "django.contrib.staticfiles",
    "storages",
    "django_countries",
    "mathfilters",
    "mptt",
    "django_filters",
    "django.contrib.sites",
    "allauth",
    # "allauth.account",
    # "allauth.socialaccount",
    # "allauth.socialaccount.providers.google",
    # "allauth.socialaccount.providers.facebook",
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

CSRF_COOKIE_SECURE = False

ROOT_URLCONF = "coda_project.urls"
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],  # or ['templates'] if you use a global templates folder
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


#  ==============DBFUNCTIONS=====================================
def dba_values():
    if os.environ.get('ENVIRONMENT') == 'production':
        host = os.environ.get('HEROKU_PROD_HOST')
        dbname = os.environ.get('HEROKU_PROD_NAME')
        user = os.environ.get('HEROKU_PROD_USER')
        password = os.environ.get('HEROKU_PROD_PASS')
    elif os.environ.get('ENVIRONMENT') == 'testing':
        # In Heroku/Postgres it is Heroku_UAT
        host = os.environ.get('DB_HOST')
        dbname = os.environ.get('DB_NAME')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')
    else:
        host = os.environ.get('STG_DB_HOST')
        dbname = os.environ.get('STG_DB_NAME')
        user = os.environ.get('STG_DB_USER')
        password = os.environ.get('STG_DB_PASSWORD')

        # host = "localhost"
        # dbname = "CODA_TRAIN"
        # user = "postgres"
        # password = "Ajtgm258*" #"*******"
        
        # host = os.environ.get('POSTGRES_DB_NAME')
        # dbname = "CODA_PRACTICE" #os.environ.get('POSTGRES_DB_NAME') 
        # user = os.environ.get('POSTGRESDB_USER')
        # password = os.environ.get('POSTGRESSPASS') 
    return host,dbname,user,password  

WSGI_APPLICATION = "coda_project.wsgi.application"
import dj_database_url

host,dbname,user,password=dba_values()



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
DATABASES = {
'default': {
'ENGINE': 'django.db.backends.sqlite3',
'NAME': os.path.join(BASE_DIR, 'coda_dev.db'),
}
}
'''=========== Heroku DB ================'''
db_from_env = dj_database_url.config(conn_max_age=600)
DATABASES["default"].update(db_from_env)

import sys
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'coda_dev'
    }

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

STATIC_ROOT = os.path.join(BASE_DIR, '..', "staticfiles")
STATIC_URL = "/static/"
STATICFILES_DIR = os.path.join(BASE_DIR, "static")


CRISPY_TEMPLATE_PACK = "bootstrap4"

LOGIN_REDIRECT_URL = "main:layout"
LOGIN_URL = "accounts:account-login"


# private email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_USE_SSL = False
EMAIL_USE_TLS = True
EMAIL_PORT = 587
EMAIL_HOST = "smtp.privateemail.com"
EMAIL_HOST_USER = os.environ.get("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_PASS")
EMAIL_FILE_PATH = BASE_DIR + "/emails"

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

EMAIL_INFO = {
    'USER': os.environ.get('EMAIL_INFO_USER'),
    'PASS': os.environ.get('EMAIL_INFO_PASS'),
    'HOST': os.environ.get('EMAIL_INFO_HOST'),
    'PORT': os.environ.get('EMAIL_INFO_PORT'),
    'USE_TLS': os.environ.get('EMAIL_INFO_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_INFO_USE_SSL'),
}

EMAIL_HR = {
    'USER': os.environ.get('EMAIL_HR_USER'),
    'PASS': os.environ.get('EMAIL_HR_PASS'),
    'HOST': os.environ.get('EMAIL_HR_HOST'),
    'PORT': os.environ.get('EMAIL_HR_PORT'),
    'USE_TLS': os.environ.get('EMAIL_HR_USE_TLS'),
    'USE_SSL': os.environ.get('EMAIL_HR_USE_SSL'),
}

AWS_S3_REGION_NAME = "us-east-2"  # change to your region
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None


# from celery.schedules import crontab

# CELERY_BROKER_URL = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
# CELERY_RESULT_BACKEND = "redis://default:xjaoROhpU8Lbiz8OZskVTgyYDFAdSmlo@redis-11854.c240.us-east-1-3.ec2.cloud.redislabs.com:11854"
# CELERY_ACCEPT_CONTENT = ["application/json"]
# CELERY_TASK_SERIALIZER = "json"
# CELERY_RESULT_SERIALIZER = "json"
# CELERY_IMPORTS = "coda_project.task"

# CELERYBEAT_SCHEDULE = {
#     "run_on_every_1st": {
#         "task": "task_history",
#         "schedule": crontab(0, 0, day_of_month="1"),
#         #'schedule': crontab(),
#     },

#     "run_on_every_1st": {
#         "task": "advertisement",
#         "schedule": crontab(0, 0, day_of_month="1"),
#         #'schedule': crontab(),
#     },
# }

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


if os.environ.get('ENVIRONMENT') == 'production':
    SITEURL = "https://www.codanalytics.net"
    SECURE_SSL_REDIRECT = True
    DEBUG = False
elif os.environ.get('ENVIRONMENT') == 'testing':
    SECURE_SSL_REDIRECT = True
    SITEURL = "https://codamakutano.herokuapp.com"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    DEBUG = True
else:
    SITEURL = "http://127.0.0.1:8000"
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
    DEBUG = True

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


# settings.py
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE')
MPESA_PASSWORD = os.environ.get('MPESA_PASSWORD')
MPESA_TIMESTAMP = os.environ.get('MPESA_TIMESTAMP')
MPESA_CALLBACK_URL = os.environ.get('MPESA_CALLBACK_URL')