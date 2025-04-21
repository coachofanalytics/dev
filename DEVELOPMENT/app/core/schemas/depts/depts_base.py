from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class DepartmentSchema(BaseModel):
    id: UUID
    bus_unit: str
    bus_func: str
    bus_subfunc: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

class DepartmentResponseSchema(BaseModel):
    id: UUID
    bus_unit: str
    bus_func: str
    bus_subfunc: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 