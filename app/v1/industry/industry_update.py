import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.industry.industry import Industry
from app.core.schemas.industry.industry_base import IndustrySchema

# Router is required
router = APIRouter(
    tags = ['industry']
)

@router.put('/update_industry/{id}')
def update_industry(id, request:IndustrySchema, db: Session=Depends(get_db)):
    industry = db.query(Industry).filter(Industry.id == id)

    if not industry.first():
        pass

    industry.update(request.dict())
    db.commit()
    return {'Industry Successfully Updated'}


