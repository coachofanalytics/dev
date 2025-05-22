import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session, relationship

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.industry.industry import Industry
from app.core.schemas.industry.industry_base import IndustrySchema

# Router is required
router = APIRouter(
    tags = ['industry']
)

@router.post('/industry', status_code=status.HTTP_201_CREATED)
def add_industry(request:IndustrySchema, db: Session = Depends(get_db)):

    new_industry =Industry(
        id = request.id,
        level1 = request.level1,
        level2 = request.level2,
        level3 = request.level3,
        level4 = request.level4,
        created_by =request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_industry)
    db.commit()
    db.refresh(new_industry)
    return request
