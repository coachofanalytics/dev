from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel
from app import schemas

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
    title: str | None = None
    company_name: str | None = None
    description: str | None = None
    skills_required: str | None = None
    deliverables: str | None = None

    payment_min: float | None = None
    payment_max: float | None = None
    currency: str | None = None

    duration_value: int | None = None
    duration_unit: str | None = None

    project_type: str | None = None
    engagement_level: str | None = None
    external_reference_links: str | None = None
    status: str | None = None

import re
from datetime import datetime

from pydantic import ConfigDict, EmailStr, field_validator
from sqlmodel import Field, SQLModel


PHONE_PATTERN = re.compile(r"^\+?[1-9]\d{7,14}$")


def normalize_phone(value: str) -> str:
    cleaned = re.sub(r"[\s\-()]", "", value)

    if not PHONE_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "Phone number must contain 8 to 15 digits and may begin with +."
        )

    return cleaned


class ScoreBase(SQLModel):
    email: EmailStr
    gender: str | None = Field(default=None, max_length=30)
    phone: str = Field(min_length=8, max_length=20)
    address: str = Field(min_length=2, max_length=255)
    city: str = Field(min_length=2, max_length=100)
    state: str = Field(min_length=2, max_length=100)
    zipcode: str = Field(min_length=2, max_length=20)
    country: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=100)
    sub_category: int = Field(ge=1)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        return normalize_phone(value)


class ScoreCreate(ScoreBase):
    pass


class ScoreRead(ScoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScoreUpdate(SQLModel):
    email: EmailStr | None = None
    gender: str | None = Field(default=None, max_length=30)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    address: str | None = Field(default=None, min_length=2, max_length=255)
    city: str | None = Field(default=None, min_length=2, max_length=100)
    state: str | None = Field(default=None, min_length=2, max_length=100)
    zipcode: str | None = Field(default=None, min_length=2, max_length=20)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    category: str | None = Field(default=None, min_length=2, max_length=100)
    sub_category: int | None = Field(default=None, ge=1)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return None

        return normalize_phone(value)


        from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobDetailsBase(BaseModel):
    title: str
    company_name: str
    location: Optional[str] = None
    job_type: Optional[str] = None
    description: str
    requirements: Optional[str] = None
    salary: Optional[str] = None
    application_link: Optional[str] = None
    is_active: bool = True


class JobDetailsCreate(JobDetailsBase):
    pass


class JobDetailsResponse(JobDetailsBase):
  id: int

model_config = ConfigDict(
    from_attributes=True,
)

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerUserCreate(BaseModel):
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool = True


class CustomerUserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )


class UserSummary(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(
        from_attributes=True
    )


class UserGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    user_ids: list[int] = Field(default_factory=list)


class UserGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    user_ids: Optional[list[int]] = None


class UserGroupStatusUpdate(BaseModel):
    is_active: bool


class UserGroupFeaturedUpdate(BaseModel):
    is_featured: bool


class UserGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_active: bool
    is_featured: bool
    users: list[UserSummary] = Field(default_factory=list)

    model_config = ConfigDict(
        from_attributes=True
    )


class ActiveGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )


class MessageResponse(BaseModel):
    message: str