import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.locations.locations import Locations
from app.core.schemas.locations.locations_base import LocationSchema, LocationResponseSchema

# Router is required
router = APIRouter(
    tags = ['Locations']
)


@router.post('/location', status_code=status.HTTP_201_CREATED)
def add_location(request:LocationSchema, db: Session = Depends(get_db)):
    new_location = Locations(
        ESRI_response = request.ESRI_response,
        latitude = request.latitude,
        longitude = request.longitude,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return request


