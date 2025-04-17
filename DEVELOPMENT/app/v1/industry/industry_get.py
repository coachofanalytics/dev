from fastapi import status, Response, HTTPException, APIRouter
from fastapi.params import Depends
from  app.database import get_db
from sqlalchemy.orm import Session
from app import schemas, models
from typing import List
from app.routers.login import get_current_user

router = APIRouter(
    tags=['Industry'],
    # prefix="/industry"
)

@router.get('/industry', response_model=List[schemas.DisplayIndustrySchema])
def get_industrys(db: Session = Depends(get_db)):
    industry = db.query(models.Industry).all()
    return industry