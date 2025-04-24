from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from typing import Dict

# Replace with your real secret key and algorithm
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def get_user(request: Request, metadata: bool = False) -> Dict:
    """
    Extracts and validates the user from Authorization header.
    Optionally includes metadata if requested.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_data = {
            "id": payload.get("sub"),  # or payload["user_id"]
            "name": payload.get("name"),
            "email": payload.get("email"),
            "access_level": payload.get("access_level", "User")
        }

        if metadata:
            user_data["metadata"] = {
                "issued_at": payload.get("iat"),
                "expires": payload.get("exp")
            }

        return user_data

    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token",
        )
