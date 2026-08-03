from pathlib import Path

output = Path("/mnt/data/schemas_fixed.py")

import re
from datetime import datetime
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    field_validator,
    model_validator,
)
from sqlmodel import Field, SQLModel


# ==========================================================
# PRICING SUBPLAN SCHEMAS
# ==========================================================

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
    description: Optional[str] = None
    price: float

    model_config = ConfigDict(
        from_attributes=True,
    )


# ==========================================================
# SEARCH RECORD SCHEMAS
# ==========================================================

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

    model_config = ConfigDict(
        from_attributes=True,
    )


# ==========================================================
# JOB DETAILS SCHEMAS
# ==========================================================

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


class JobDetailsRead(JobDetailsBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


class JobDetailsResponse(JobDetailsRead):
    pass


# ==========================================================
# SCORE SCHEMAS
# ==========================================================

PHONE_PATTERN = re.compile(
    r"^\\+?[1-9]\\d{7,14}$"
)


PHONE_PATTERN = re.compile(
    r"^\+?[1-9]\d{7,14}$"
)


def normalize_phone(
    value: str,
) -> str:
    cleaned = re.sub(
        r"[\s()\-]",
        "",
        value,
    )

    if not PHONE_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "Phone number must contain 8 to 15 digits "
            "and may begin with +."
        )

    return cleaned


class ScoreBase(SQLModel):
    email: EmailStr

    gender: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    phone: str = Field(
        min_length=8,
        max_length=20,
    )

    address: str = Field(
        min_length=2,
        max_length=255,
    )

    city: str = Field(
        min_length=2,
        max_length=100,
    )

    state: str = Field(
        min_length=2,
        max_length=100,
    )

    zipcode: str = Field(
        min_length=2,
        max_length=20,
    )

    country: str = Field(
        min_length=2,
        max_length=100,
    )

    category: str = Field(
        min_length=2,
        max_length=100,
    )

    sub_category: int = Field(
        ge=1,
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(
        cls,
        value: str,
    ) -> str:
        return normalize_phone(value)


class ScoreCreate(ScoreBase):
    pass


class ScoreRead(ScoreBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class ScoreUpdate(SQLModel):
    email: Optional[EmailStr] = None

    gender: Optional[str] = Field(
        default=None,
        max_length=30,
    )

    phone: Optional[str] = Field(
        default=None,
        min_length=8,
        max_length=20,
    )

    address: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )

    city: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    state: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    zipcode: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=20,
    )

    country: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    category: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    sub_category: Optional[int] = Field(
        default=None,
        ge=1,
    )

    @field_validator("phone")
    @classmethod
    def validate_phone(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        return normalize_phone(value)


# ==========================================================
# CUSTOMER USER SCHEMAS
# ==========================================================

ALLOWED_CUSTOMER_USER_CATEGORIES = {
    "administrator",
    "employee",
    "client",
    "applicant",
}


class CustomerUserBase(BaseModel):
    username: str
    email: EmailStr

    city: str
    state: str
    country: str
    category: str

    is_admin: bool = False
    is_employee: bool = False
    is_client: bool = False
    is_applicant: bool = False
    is_active: bool = True

    @field_validator(
        "username",
        "city",
        "state",
        "country",
        "category",
    )
    @classmethod
    def validate_required_text(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "This field is required."
            )

        return cleaned_value

    @field_validator("category")
    @classmethod
    def validate_category(
        cls,
        value: str,
    ) -> str:
        cleaned_value = value.strip().lower()

        if (
            cleaned_value
            not in ALLOWED_CUSTOMER_USER_CATEGORIES
        ):
            raise ValueError(
                "Unsupported customer-user category."
            )

        return cleaned_value

    @model_validator(mode="after")
    def validate_at_least_one_role(
        self,
    ):
        if not any(
            [
                self.is_admin,
                self.is_employee,
                self.is_client,
                self.is_applicant,
            ]
        ):
            raise ValueError(
                "At least one role must be selected."
            )

        return self


class CustomerUserCreate(CustomerUserBase):
    pass


class CustomerUserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None

    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None

    is_admin: Optional[bool] = None
    is_employee: Optional[bool] = None
    is_client: Optional[bool] = None
    is_applicant: Optional[bool] = None
    is_active: Optional[bool] = None

    @field_validator(
        "username",
        "city",
        "state",
        "country",
        "category",
    )
    @classmethod
    def validate_optional_text(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(
                "This field cannot be empty."
            )

        return cleaned_value

    @field_validator("category")
    @classmethod
    def validate_optional_category(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        cleaned_value = value.strip().lower()

        if (
            cleaned_value
            not in ALLOWED_CUSTOMER_USER_CATEGORIES
        ):
            raise ValueError(
                "Unsupported customer-user category."
            )

        return cleaned_value


class CustomerUserResponse(CustomerUserBase):
    id: int
    resume_file: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class CustomerUserListResponse(BaseModel):
    total: int
    customer_users: list[CustomerUserResponse]


# ==========================================================
# USER GROUP SCHEMAS
# ==========================================================

class UserSummary(BaseModel):
    id: int
    username: str
    email: str

    model_config = ConfigDict(
        from_attributes=True,
    )


class UserGroupCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_featured: bool = False
    user_ids: list[int] = Field(
        default_factory=list,
    )


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

    users: list[UserSummary] = Field(
        default_factory=list,
    )

    model_config = ConfigDict(
        from_attributes=True,
    )


class ActiveGroupResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True,
    )


# ==========================================================
# GENERAL RESPONSE SCHEMAS
# ==========================================================

class MessageResponse(BaseModel):
    message: str
# '''

# output.write_text(code, encoding="utf-8")
# compile(code, str(output), "exec")
# print(f"Created and syntax-checked: {output}")
