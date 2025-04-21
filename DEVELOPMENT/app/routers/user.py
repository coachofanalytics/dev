from fastapi import status, Response, HTTPException, APIRouter
from fastapi.params import Depends
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app import schemas, models
from typing import List
from passlib.context import CryptContext


router = APIRouter(
    tags=['Users']
)

# Mechanism for hashing a password
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Create a User
@router.post('/user', status_code=status.HTTP_201_CREATED, response_model=schemas.DisplayUser)
def create_user(request: schemas.User, db:Session=Depends(get_db)):
    hashed_password = pwd_context.hash(request.password)
    new_user = models.User(
        username = request.username,
        email = request.email,
        first_name = request.first_name,
        last_name = request.last_name,
        password = hashed_password
    )
    db.add(new_user)
    db.commit()
    return request