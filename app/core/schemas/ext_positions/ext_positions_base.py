from pydantic import BaseModel, Field, Json
from typing import Optional
from uuid import UUID
from datetime import datetime


class ExtPositionSchema(BaseModel):
    position_id: UUID
    raw_data: Json
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

class ExtPositionResponseSchema(BaseModel):
    position_id: UUID
    raw_data: Json
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 