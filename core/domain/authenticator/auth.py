import os
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from core.config.settings import Settings

settings = Settings()
SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
#     to_encode = data.copy()
#     if expires_delta:
#         expire = datetime.utcnow() + expires_delta
#     else:
#         expire = datetime.utcnow() + timedelta(minutes=15)
#     to_encode.update({"exp": expire})
#     encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
#     return encoded_jwt


def get_user(request, metadata=False):
    """Retrieves the user details if available, raises exception otherwise"""
    auth_header_value = request.headers.get("Authorization")
    
    # Add debug logs (new)
    print("=== Debug Logs Start ===")
    print("All Headers:", dict(request.headers))
    print("Auth Header:", auth_header_value)
    print("=== Debug Logs End ===")
    
    if not auth_header_value:
        raise ValueError("Auth token not provided.")
    
    jwt_token = auth_header_value[7:]  # Strip "Bearer "
    
    # Add more debug logs (new)
    print("=== Token Debug ===")
    print("JWT Token:", jwt_token)
    print("Token Length:", len(jwt_token))
    print("================")

    try:
        parsed_jwt = jwt.decode(
            jwt_token,
            key=SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_signature": False},  # Disable only if testing
        )
        # Add debug log (new)
        print("Parsed JWT:", parsed_jwt)
    except Exception as e:
        # Add debug log (new)
        print("JWT Decode Error:", str(e))
        raise ValueError(f"Token decoding failed: {str(e)}")
    
    if len(parsed_jwt) == 0:
        raise ValueError("User Token could not be decoded")

    if not parsed_jwt.get("roles"):
        raise ValueError(
            "Roles missing from the token. Please check authorization and try again"
        )
    if metadata:
        return {
            "id": parsed_jwt.get("id", ""),
            "name": parsed_jwt.get("sub", ""),
            "access_level": parsed_jwt.get("roles", [])
        }
    return parsed_jwt



def validate_user_access(
    expected_access_level: list[str], actual_access_level: list[str]
):
    """Validates the user by checking the
    access level expected by code to match
    access level retrived from token

    Args:
        expected_access_level: List desired access_level
        actual_access_level: List obtained access_level fr0m token

    Raises:
        Unauthorized: If counter value remains zero then no expected
        access level were found in extracted access level from token

    Returns:
        Authorised in case one expected access level was found in extracted
        access level.
    """
        
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




# from dataclasses import dataclass
# from datetime import datetime, timedelta
# from typing import Optional
# import jwt
# from ..user.user import User

# @dataclass
# class AuthToken:
#     """Domain model for authentication tokens."""
#     access_token: str
#     refresh_token: str
#     token_type: str = "bearer"
#     expires_at: datetime = None

#     @classmethod
#     def create_tokens(cls, user: User, secret_key: str) -> 'AuthToken':
#         """Business rule: Create new access and refresh tokens."""
#         access_token_expires = datetime.utcnow() + timedelta(minutes=15)
#         refresh_token_expires = datetime.utcnow() + timedelta(days=7)

#         access_token = jwt.encode(
#             {
#                 "sub": str(user.id),
#                 "exp": access_token_expires,
#                 "type": "access"
#             },
#             secret_key,
#             algorithm="HS256"
#         )

#         refresh_token = jwt.encode(
#             {
#                 "sub": str(user.id),
#                 "exp": refresh_token_expires,
#                 "type": "refresh"
#             },
#             secret_key,
#             algorithm="HS256"
#         )

#         return cls(
#             access_token=access_token,
#             refresh_token=refresh_token,
#             expires_at=access_token_expires
#         )

# @dataclass
# class Credentials:
#     """Domain model for user credentials."""
#     email: str
#     password: str

#     def validate(self) -> bool:
#         """Business rule: Validate credentials format."""
#         if not self.email or '@' not in self.email:
#             raise ValueError("Invalid email format")
#         if not self.password or len(self.password) < 8:
#             raise ValueError("Password must be at least 8 characters")
#         return True
