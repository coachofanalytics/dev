from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class PositionSchema(BaseModel):
    title_id: UUID
    location_id: UUID
    dept_id: UUID
    copy_position_id: UUID
    role_type: str
    base_compensation: float
    bonus: float
    fringe_benefits: float
    fully_loaded_compensation: float
    is_active: bool
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

class PositionResponseSchema(BaseModel):
    title_id: UUID
    location_id: UUID
    dept_id: UUID
    copy_position_id: UUID
    role_type: str
    base_compensation: float
    bonus: float
    fringe_benefits: float
    fully_loaded_compensation: float
    is_active: bool
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 