import os
from fastapi import Request, HTTPException, status
from jose import jwt, JWTError
from typing import Dict


# Replace with your real secret key and algorithm

SECRET_KEY = os.environ.get('FASTAPI_SECRET_KEY')
ALGORITHM = "HS256"

def get_user(request: Request, metadata: bool = False) -> Dict:
    """
    Extracts and validates the user from Authorization header.
    Optionally includes metadata if requested.
    """
    auth_header = request.headers.get("Authorization")
    print('HERE 1',auth_header)
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    print('HERE 2')
    token = auth_header.split(" ")[1]
    print('HERE 3',token)
    try:
        # print('token',token 'secret_key',SECRET_KEY)
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



def validate_user_access(
    expected_access_level: list[str], actual_access_level: list[str]
):
    counter = 0
    for item in expected_access_level:
        if item in actual_access_level:
            counter = counter + 1

    if counter == 0:
        raise Unauthorized(
            "Persona's role could not meet the authentication"
            " requirements of the Operation."
            " Please contact the administrator."
        )
    return "Authorised"