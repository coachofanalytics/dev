from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class IndustrySchema(BaseModel):
    id: UUID
    level1: str
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    created_by: Optional[UUID] = None
    created_date: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    updated_date: Optional[datetime] = None

class DisplayIndustrySchema(BaseModel):
    id: UUID
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    created_by: Optional[UUID] = None
    created_date: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True 