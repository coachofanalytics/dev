from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from app.config.settings import get_jwt_settings


def get_jwt_settings():
    import os
    secret_key = os.environ.get('SECRET_KEY', 'my-secrete-key-fro-development-only')
    algorithm = os.environ.get('ALGORITHM', 'HS256')
    expire_minutes = int(os.environ.get('ACCESS_TOKEN_EXPIRES_MINUTES', '30'))

    return secret_key, algorithm, expire_minutes


def create_access_token(data: dict, expires_delta:Optional[timedelta] = None):
    to_encode = data.copy()

    if expires_delta:
        expire: datetime.utcnow() + expires_delta
    else:
        _, _, expire_minutes = get_jwt_settings()
        expire = datetime.utcnow() + timedelta(minutes=expire_minutes)

    to_encode.update({"exp":expire_minutes})
    secret_key, algorith, _ = get_jwt_settings()

    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    
    return encoded_jwt


def decode_access_token(token: str):

    secret_key, algorithm, _ = get_jwt_settings()

    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        return payload
    except JWTError:
        return None