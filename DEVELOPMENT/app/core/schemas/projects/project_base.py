
from app.core.schemas.common import BaseSchema

class ProjectsBase(BaseSchema):
    """Base Schema for all Project Schemas"""

    id: Optional[uuid.UUID] = None  # <- Make it Optional with a default
    name: str
    description: Optional[str]
    engagement_code: str = Field(alias="engagementCode")
    engagement_type: str = Field(alias="engagementType")
    partner: str
    is_active: bool
    createor_name: str
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        allow_population_by_field_name = True
        orm_mode = True


