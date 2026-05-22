import os
from dotenv import load_dotenv

load_dotenv()

def dba_values():

    env = os.environ.get('ENVIRONMENT')

    if env == 'production':
        host = os.environ.get('PROD_FASTAPI_DB_HOST')
        dbname = os.environ.get('PROD_FASTAPI_DB_NAME')
        user = os.environ.get('PROD_FASTAPI_DB_USER')
        password = os.environ.get('PROD_FASTAPI_DB_PASSWORD')
        port = 5432

    elif env == 'staging':
        host = os.environ.get('STG_FASTAPI_DB_HOST')
        dbname = os.environ.get('STG_FASTAPI_DB_NAME')
        user = os.environ.get('STG_FASTAPI_DB_USER')
        password = os.environ.get('STG_FASTAPI_DB_PASSWORD')
        port = 5432

    else:
        host = os.environ.get('LOCAL_FASTAPI_DB_HOST', 'localhost')
        dbname = os.environ.get('LOCAL_FASTAPI_DB_NAME', 'transaction_db')
        user = os.environ.get('LOCAL_FASTAPI_DB_USER', 'postgres')
        password = os.environ.get('LOCAL_FASTAPI_DB_PASSWORD', '123')
        port = 5432

    return host, dbname, user, password, port


def get_database_url():
    host, dbname, user, password, port = dba_values()

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"