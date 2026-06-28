from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Pricing(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None

    subplans: list["PricingSubPlan"] = Relationship(back_populates="pricing")

class PricingSubPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    pricing_id: int = Field(foreign_key="pricing.id")
    title: str
    description: Optional[str] = None
    price: float

    pricing: Optional[Pricing] = Relationship(back_populates="subplans")




class SearchRecord(SQLModel, table=True):
    __tablename__ = "search_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    topic: str = Field(max_length=255)
    question: str
    uploaded: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)



class JobDetails(SQLModel, table=True):
    __tablename__ = "job_details"

    id: Optional[int] = Field(default=None, primary_key=True)

    title: str = Field(index=True, max_length=255)
    company_name: Optional[str] = Field(default=None, max_length=255)

    description: str
    skills_required: str
    deliverables: str

    payment_min: float
    payment_max: float
    currency: str = Field(default="USD", max_length=20)

    duration_value: int
    duration_unit: str = Field(default="weeks", max_length=50)

    project_type: str = Field(default="fixed", max_length=100)
    engagement_level: str = Field(default="medium", max_length=100)

    external_reference_links: Optional[str] = None

    status: str = Field(default="open", max_length=50)

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    


