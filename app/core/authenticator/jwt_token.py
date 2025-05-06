import uuid
from datetime import datetime, timedelta
from jose import jwt
import os


# Constants
SECRET_KEY = os.environ.get('FASTAPI_SECRET_KEY')



ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600000

def create_access_token():
    """
    Generates a JWT access token with user data.
    """


    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload = {
        "id": str(uuid.uuid4()),
        "sub": "testuser",
        "roles": ["admin"],
        "exp": expire,
        "iat": datetime.utcnow()
    }

    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
