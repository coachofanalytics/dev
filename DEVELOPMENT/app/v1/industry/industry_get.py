from fastapi import status, Response, HTTPException, APIRouter
from fastapi.params import Depends
from  app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.industry.industry_base import DisplayIndustrySchema
from app.core.models.industry.industry import Industry
from typing import List
from app.routers.login import get_current_user

router = APIRouter(
    tags=['Industry'],
    # prefix="/industry"
)

@router.get('/industry', response_model=List[DisplayIndustrySchema])
def get_industrys(db: Session = Depends(get_db)):
    
    industry = db.query(Industry).all()
    return industry