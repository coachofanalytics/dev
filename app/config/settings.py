import os
from dotenv import load_dotenv


load_dotenv()
#  ==============DBFUNCTIONS=====================================
def dba_values():
    if os.environ.get('ENVIRONMENT') == 'production':
        host = os.environ.get('PROD_FASTAPI_DB_HOST')
        dbname = os.environ.get('PROD_FASTAPI_DB_NAME')
        user = os.environ.get('PROD_FASTAPI_DB_USER')
        password = os.environ.get('PROD_FASTAPI_DB_PASS')
        port = 5432

    elif os.environ.get('ENVIRONMENT') == 'staging':
        host = os.environ.get('STG_FASTAPI_DB_HOST')
        dbname = os.environ.get('STG_FASTAPI_DB_NAME') 
        user = os.environ.get('STG_FASTAPI_DB_USER')
        password = os.environ.get('STG_FASTAPI_DB_PASSWORD')
        port = 5432

    else:
        # Test locally 
        host = os.environ.get('LOCAL_FASTAPI_DB_HOST', 'localhost')
        dbname = os.environ.get('LOCAL_FASTAPI_DB_NAME', 'transaction_database') 
        user = os.environ.get('LOCAL_FASTAPI_DB_USER', 'postgres')
        password = os.environ.get('LOCAL_FASTAPI_DB_PASSWORD', 'postgres123')
        port = 5432

        # host = os.environ.get('STG_DB_HOST')
        # dbname = os.environ.get('STG_DB_NAME') 
        # user = os.environ.get('STG_DB_USER')
        # password = os.environ.get('STG_DB_PASSWORD')
        # port = 5432


    return host,dbname,user,password,port 


def get_database_url():
    host, dbname, user, password, port = dba_values()

    database_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"

    return database_url