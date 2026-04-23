from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.core.db.database import get_db
from app.core.models.users.user import User
from app.core.security.jwt import decode_access_token

security = HTTPBearer()

def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    
    token = credentials.credentials

    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail = "Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail = "Token missing username",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user  = db.query(User).filter(User.username == username).first()

    if user is None:
        raise HTTPException(
            status_code= status.HTTP_401_UNAUTHORIZED,
            detail = "User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_optional_user(
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
) -> Optional[User]:
    
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        return None
    username = payload.get("sub")
    if username is None:
        return None


    return db.query(User).filter(User.username == username).first()