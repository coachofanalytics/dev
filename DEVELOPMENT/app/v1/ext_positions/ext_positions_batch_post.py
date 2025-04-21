import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.ext_positions.ext_positions import Extpositions
from app.core.schemas.ext_positions.ext_positions_base import ExtPositionSchema

# Router is required
router = APIRouter(
    tags = ['Ext Positions']
)


@router.post('/ext_position', status_code=status.HTTP_201_CREATED)
def add_ext_position(request:ExtPositionSchema, db: Session = Depends(get_db)):
    new_ext_postn = Extpositions(
        position_id = request.bus_unit,
        raw_data = request.bus_func,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_ext_postn)
    db.commit()
    db.refresh(new_ext_postn)
    return request


