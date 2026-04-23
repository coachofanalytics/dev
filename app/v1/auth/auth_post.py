from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.core.db.database import get_db
from app.core.models.users.user import User
from app.core.schemas.users.user import UserCreate, UserResponse, Token, UserLogin
from app.core.security.hashing import get_password_hash, verify_password
from app.core.security.jwt import create_access_token


router = APIRouter(tags=['Authentication'], prefix='/auth')

@router.post('/register', response_model=UserResponse, status_code=status.HTTP_201_CREATED)

def register(user_data:UserCreate, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.username == user_data.username).first()

    if existing_user:
        raise  HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Username already registered"
        )

    existing_email = db.query(User).filter(User.email == user_data.email).first()
    
    if existing_email:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Email already registered"
        )
    
    new_user = User(
        email = user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post('/login', response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    
    user = db.query(User).filter(User.username == user_data.username).first()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer",}
        )

    access_token = create_access_token(data={"sub": user.username})

    return {"access_token": access_token, "token_type":"bearer"}
    