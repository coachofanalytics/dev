from datetime import datetime, timedelta
from jose import jwt
import os


# Constants
SECRET_KEY = os.environ.get("SECRET_KEY", "your-super-secret-key-here-123456789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600000


def create_access_token():
    """
    Generates a JWT access token with user data.
    """
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable is not set")

    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        # "id": str(uuid.uuid4()),
        "id": "74",
        "sub": "coda_info",
        "roles": ["viewer"],
        "exp": expire,
        "iat": datetime.utcnow(),
    }

    try:
        encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    except Exception as e:
        raise ValueError(f"Failed to create JWT token: {str(e)}")
