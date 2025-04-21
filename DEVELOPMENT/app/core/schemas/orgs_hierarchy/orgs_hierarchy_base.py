from pydantic import BaseModel, Field, Json
from typing import Optional
from uuid import UUID
from datetime import datetime


class OrgHierarchySchema(BaseModel):
    org_id: UUID
    parent_position_id: UUID
    position_id: UUID
    layer: int
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

# Need to establish relationships later

class OrgHierarchyResponseSchema(BaseModel):
    org_id: UUID
    parent_position_id: UUID
    position_id: UUID
    layer: int
    id: UUID
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 