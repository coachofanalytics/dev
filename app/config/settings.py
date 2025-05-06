import os

from app.core.authenticator.jwt_token import create_access_token

# app.core.authenticator import jwt_token


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
        #Test locally 
        host = os.environ.get('LOCAL_FASTAPI_DB_HOST')
        dbname = os.environ.get('LOCAL_FASTAPI_DB_NAME') 
        user = os.environ.get('LOCAL_FASTAPI_DB_USER')
        password = os.environ.get('LOCAL_FASTAPI_DB_PASSWORD')
        port = 5432

        # import secrets
        # print(secrets.token_urlsafe(32))

        # SECRET_KEY = os.environ.get('FASTAPI_SECRET_KEY')
        # print(SECRET_KEY)

        # print(create_access_token())


    return host,dbname,user,password,port 
