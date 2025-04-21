from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class LocationSchema(BaseModel):
    id: UUID
    ESRI_response: str
    latitude: str
    longitude: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

class LocationResponseSchema(BaseModel):
    id: UUID
    ESRI_response: str
    latitude: str
    longitude: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 