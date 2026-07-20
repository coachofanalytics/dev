from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class JobDetails(SQLModel, table=True):
    __tablename__ = "job_details"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str
    company_name: str = ""
    description: str

    skills_required: str
    deliverables: str

    payment_min: float
    payment_max: float
    currency: str = "USD"

    duration_value: int
    duration_unit: str = "weeks"

    project_type: str = "fixed"
    engagement_level: str = "medium"

    external_reference_links: Optional[str] = None
    status: str = "open"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobDetailsResponse(BaseModel):
    id: int
    title: str
    company_name: str
    description: str
    skills_required: str
    deliverables: str
    payment_min: float
    payment_max: float
    currency: str
    duration_value: int
    duration_unit: str
    project_type: str
    engagement_level: str
    external_reference_links: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)