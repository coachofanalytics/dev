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
from pydantic import BaseModel, EmailStr, field_validator
from decimal import Decimal


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
import re


PHONE_PATTERN = re.compile(
    r"^\+[1-9]\d{7,14}$"
)


def normalize_phone(
    value: str,
) -> str:
    if not value:
        raise ValueError(
            "Phone number is required."
        )

    cleaned = re.sub(
        r"[\s()\-.]",
        "",
        value.strip(),
    )

    # Kenyan local format: 0724364465
    if (
        cleaned.startswith("0")
        and cleaned.isdigit()
        and len(cleaned) == 10
    ):
        cleaned = "+254" + cleaned[1:]

    # Kenyan international format without +
    elif (
        cleaned.startswith("254")
        and cleaned.isdigit()
        and len(cleaned) == 12
    ):
        cleaned = "+" + cleaned

    # Other international numbers without +
    elif cleaned.isdigit():
        cleaned = "+" + cleaned

    if not PHONE_PATTERN.fullmatch(cleaned):
        raise ValueError(
            "Phone number must contain 8 to 15 digits. "
            "Kenyan numbers may use 07XXXXXXXX, "
            "2547XXXXXXXX, or +2547XXXXXXXX."
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


class CareerVacancyCreate(BaseModel):
    title: str
    slug: str
    location: str
    employment_type: str
    summary: str
    responsibilities: str
    qualifications: str
    requirements: str

    compensation: Optional[str] = None
    application_deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None

    vacancy_status: str = "draft"
    environment_status: str = "uat"

    is_active: bool = False
    is_featured: bool = False

    support_contact: Optional[str] = None
    privacy_notice: Optional[str] = None


class CareerVacancyUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    summary: Optional[str] = None
    responsibilities: Optional[str] = None
    qualifications: Optional[str] = None
    requirements: Optional[str] = None

    compensation: Optional[str] = None
    application_deadline: Optional[datetime] = None
    published_at: Optional[datetime] = None

    vacancy_status: Optional[str] = None
    environment_status: Optional[str] = None

    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None

    support_contact: Optional[str] = None
    privacy_notice: Optional[str] = None


class CareerVacancyRead(CareerVacancyCreate):
    id: int
    created_at: datetime
    updated_at: datetime


class CareerApplicationCreate(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    location: Optional[str] = None
    cover_letter: Optional[str] = None
    privacy_confirmed: bool

    @field_validator("privacy_confirmed")
    @classmethod
    def privacy_must_be_confirmed(
        cls,
        value: bool,
    ):
        if value is not True:
            raise ValueError(
                "You must confirm the applicant privacy notice."
            )

        return value


class CareerApplicationRead(BaseModel):
    id: int
    vacancy_id: int
    full_name: str
    email: str
    phone: Optional[str]
    location: Optional[str]
    resume_file: str
    cover_letter: Optional[str]
    privacy_confirmed: bool
    application_status: str
    submitted_at: datetime
TRANSACTION_PAYMENT_METHODS = {
    "Mpesa",
    "Bank Transfer",
    "Cash",
    "Card",
    "Other",
}


TRANSACTION_CATEGORIES = {
    "Income",
    "Expense",
    "Transfer",
    "Refund",
    "Other",
}


class TransactionCreate(BaseModel):
    sender_id: Optional[int] = None
    department_id: Optional[int] = None

    receiver: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None

    activity_date: datetime

    receipt_link: Optional[str] = None

    qty: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    transaction_cost: Decimal = Decimal("0.00")

    description: Optional[str] = None

    payment_method: str = "Other"
    category: str

    @field_validator(
        "qty",
        "amount",
        "transaction_cost",
    )
    @classmethod
    def validate_amounts(cls, value):
        if value is not None and value < 0:
            raise ValueError(
                "Transaction values cannot be negative."
            )

        return value

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(
        cls,
        value: str,
    ):
        if value not in TRANSACTION_PAYMENT_METHODS:
            raise ValueError(
                "Invalid payment method."
            )

        return value

    @field_validator("category")
    @classmethod
    def validate_category(
        cls,
        value: str,
    ):
        if value not in TRANSACTION_CATEGORIES:
            raise ValueError(
                "Invalid transaction category."
            )

        return value


class TransactionUpdate(BaseModel):
    sender_id: Optional[int] = None
    department_id: Optional[int] = None

    receiver: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None

    activity_date: Optional[datetime] = None

    receipt_link: Optional[str] = None

    qty: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    transaction_cost: Optional[Decimal] = None

    description: Optional[str] = None

    payment_method: Optional[str] = None
    category: Optional[str] = None

    @field_validator(
        "qty",
        "amount",
        "transaction_cost",
    )
    @classmethod
    def validate_amounts(cls, value):
        if value is not None and value < 0:
            raise ValueError(
                "Transaction values cannot be negative."
            )

        return value

    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(
        cls,
        value,
    ):
        if (
            value is not None
            and value not in TRANSACTION_PAYMENT_METHODS
        ):
            raise ValueError(
                "Invalid payment method."
            )

        return value

    @field_validator("category")
    @classmethod
    def validate_category(
        cls,
        value,
    ):
        if (
            value is not None
            and value not in TRANSACTION_CATEGORIES
        ):
            raise ValueError(
                "Invalid transaction category."
            )

        return value


class TransactionRead(BaseModel):
    id: int

    sender_id: Optional[int] = None
    department_id: Optional[int] = None

    receiver: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None

    activity_date: datetime

    receipt_link: Optional[str] = None

    qty: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    transaction_cost: Decimal

    description: Optional[str] = None

    payment_method: str
    category: str

    total_transactions_amt: Decimal

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }


class MessageResponse(BaseModel):
    message: str