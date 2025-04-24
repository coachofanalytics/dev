from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


#from app.core.schemas.projects import ProjectsBase

# # class ProjectsCreate(BaseModel):
# class ProjectsCreate(ProjectsBase):
#     """
#     Schema for creating a new project (e.g., POST Projects)
#     """
#     id: Optional[uuid.UUID]  # Add `id` field, which is optional for now
#     name: str
#     description: Optional[str]
#     engagement_code: str = Field(alias="engagementCode")
#     engagement_type: str = Field(alias="engagementType")
#     partner: str
#     access: List[uuid.UUID] = Field(alias="accessRights", default=[])

#     @validator("access")
#     def access_must_be_unique(cls, v):  # pylint: disable=E0213
#         """Checks if user ids provided in request body consist of unique user ids."""
#         if len(np.unique(v)) != len(v):
#             raise ValueError("Must be an array of unique user ids")
#         return v

#     class Config:
#         orm_mode = True

class ProjectSchema(BaseModel):

    id: UUID  # <- Make it Optional with a default
    name: str
    description: Optional[str] = None
    engagement_code: str 
    engagement_type: str 
    partner: str    
    is_active: bool
    creator_name: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 
