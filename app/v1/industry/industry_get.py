from fastapi import status, Response, HTTPException, APIRouter,Request
from fastapi.params import Depends
from  app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.industry.industry_base import DisplayIndustrySchema
from app.core.models.industry.industry import Industry
from typing import List


from app.core.db.database import get_db
from app.core.models.industry.industry import Industry

# Router is required
router = APIRouter(
    tags=['Industry'],
    # prefix="/industry"
)

@router.get('/industry', response_model=List[DisplayIndustrySchema])
def get_industrys(
    request:Request,
    db: Session = Depends(get_db)):

    industry = db.query(Industry).all()
    return industry





