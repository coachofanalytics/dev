from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.v1.auth.jwt_handler import verify_access_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"www-Authenticate": "Bearer"},
        )
        
    return payload