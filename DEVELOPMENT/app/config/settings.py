
#  ==============DBFUNCTIONS=====================================
def dba_values():
    if os.environ.get('ENVIRONMENT') == 'production':
        host = os.environ.get('HEROKU_DYCPROD_HOST')
        dbname = os.environ.get('HEROKU_DYCPROD_NAME')
        user = os.environ.get('HEROKU_DYCPROD_USER')
        password = os.environ.get('HEROKU_DYCPROD_PASS')

    elif os.environ.get('ENVIRONMENT') == 'staging':
        # In Heroku/Postgres it is Heroku_UAT
        host = os.environ.get('DB_NAME')
        dbname = os.environ.get('DB_NAME')
        user = os.environ.get('DB_USER')
        password = os.environ.get('DB_PASSWORD')

    else:
        #Test in staging database before staging deployment
        host = os.environ.get('STG_DB_HOST')
        dbname = os.environ.get('STG_DB_NAME') 
        user = os.environ.get('STG_DB_USER')
        password = os.environ.get('STG_DB_PASSWORD')

        # #Test locally 
        # host = os.environ.get('LOCAL_DB_HOST')
        # dbname = os.environ.get('LOCAL_DB_NAME') 
        # user = os.environ.get('LOCAL_DB_USER')
        # password = os.environ.get('LOCAL_DB_PASSWORD') 

        host = 'localhost'
        dbname = 'DC48K_DEV'
        user = 'postgres'
        password = 'postgres' 

    return host,dbname,user,password  

WSGI_APPLICATION = "coda_project.wsgi.application"
import dj_database_url

host,dbname,user,password=dba_values() #herokuprod() #herokudev() #dblocal()  #herokudev(),
# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": dbname,
        "USER":user,
        "PASSWORD":password,
        "HOST": host
    }
}
