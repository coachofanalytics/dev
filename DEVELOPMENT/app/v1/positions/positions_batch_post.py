import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.positions.positions import Positions
from app.core.schemas.positions.positions_base import PositionSchema, PositionResponseSchema

# Router is required
router = APIRouter(
    tags = ['Positions']
)


@router.post('/position', status_code=status.HTTP_201_CREATED)
def add_position(request:PositionSchema, db: Session = Depends(get_db)):
    new_position = Positions(
        title_id = request.title_id,
        location_id = request.location_id,
        dept_id = request.dept_id,
        copy_position_id = request.copy_position_id,
        role_type = request.role_type,
        base_compensation =request.base_compensation,
        bonus = request.bonus,
        fringe_benefits = request.fringe_benefits,
        fully_loaded_compensation = request.fully_loaded_compensation,
        is_active = request.is_active,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_position)
    db.commit()
    db.refresh(new_position)
    return request