from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel

class PricingSubPlanCreate(BaseModel):
    pricing_id: int
    title: str
    description: Optional[str] = None
    price: float

class PricingSubPlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None

class PricingSubPlanResponse(BaseModel):
    id: int
    pricing_id: int
    title: str
    description: Optional[str]
    price: float

    model_config = {"from_attributes": True}  # Pydantic v2


class PricingSubPlanCreate(BaseModel):
    name: str
    price: float


class PricingSubPlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None


class PricingSubPlanResponse(BaseModel):
    id: int
    name: str
    price: float

    model_config = {
        "from_attributes": True
    }


class SearchRecordBase(BaseModel):
    topic: str
    question: str
    uploaded: bool = False


class SearchRecordCreate(SearchRecordBase):
    pass


class SearchRecordUpdate(BaseModel):
    topic: Optional[str] = None
    question: Optional[str] = None
    uploaded: Optional[bool] = None


class SearchRecord(SearchRecordBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class JobDetailsBase(SQLModel):
    title: str
    company_name: Optional[str] = None

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


class JobDetailsCreate(JobDetailsBase):
    pass


class JobDetailsRead(JobDetailsBase):
    id: int
    created_at: str | None = None
    updated_at: str | None = None


class JobDetailsUpdate(SQLModel):
    title: Optional[str] = None
    company_name: Optional[str] = None

    description: Optional[str] = None
    skills_required: Optional[str] = None
    deliverables: Optional[str] = None

    payment_min: Optional[float] = None
    payment_max: Optional[float] = None
    currency: Optional[str] = None

    duration_value: Optional[int] = None
    duration_unit: Optional[str] = None

    project_type: Optional[str] = None
    engagement_level: Optional[str] = None

    external_reference_links: Optional[str] = None
    status: Optional[str] = None
