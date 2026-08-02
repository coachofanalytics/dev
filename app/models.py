from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# ==========================================================
# PRICING MODELS
# ==========================================================

class Pricing(SQLModel, table=True):
    __tablename__ = "pricing"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    title: str = Field(
        max_length=255,
        nullable=False,
    )

    description: Optional[str] = Field(
        default=None,
    )

    subplans: list["PricingSubPlan"] = Relationship(
        back_populates="pricing",
    )


class PricingSubPlan(SQLModel, table=True):
    __tablename__ = "pricingsubplan"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    pricing_id: int = Field(
        foreign_key="pricing.id",
        nullable=False,
    )

    title: str = Field(
        max_length=255,
        nullable=False,
    )

    description: Optional[str] = Field(
        default=None,
    )

    price: float = Field(
        nullable=False,
    )

    pricing: Optional[Pricing] = Relationship(
        back_populates="subplans",
    )


# ==========================================================
# SEARCH RECORD MODEL
# ==========================================================

class SearchRecord(SQLModel, table=True):
    __tablename__ = "search_records"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    topic: str = Field(
        max_length=255,
        nullable=False,
    )

    question: str = Field(
        nullable=False,
    )

    uploaded: bool = Field(
        default=False,
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )


# ==========================================================
# JOB DETAILS MODEL
# ==========================================================

class JobDetails(SQLModel, table=True):
    __tablename__ = "job_details"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    title: str = Field(
        index=True,
        max_length=255,
        nullable=False,
    )

    company_name: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    description: str = Field(
        nullable=False,
    )

    skills_required: str = Field(
        nullable=False,
    )

    deliverables: str = Field(
        nullable=False,
    )

    payment_min: float = Field(
        nullable=False,
    )

    payment_max: float = Field(
        nullable=False,
    )

    currency: str = Field(
        default="USD",
        max_length=20,
        nullable=False,
    )

    duration_value: int = Field(
        nullable=False,
    )

    duration_unit: str = Field(
        default="weeks",
        max_length=50,
        nullable=False,
    )

    project_type: str = Field(
        default="fixed",
        max_length=100,
        nullable=False,
    )

    engagement_level: str = Field(
        default="medium",
        max_length=100,
        nullable=False,
    )

    external_reference_links: Optional[str] = Field(
        default=None,
    )

    status: str = Field(
        default="open",
        max_length=50,
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )


# ==========================================================
# SCORE MODEL
# ==========================================================

class Score(SQLModel, table=True):
    __tablename__ = "accounts_score"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    email: str = Field(
        max_length=255,
        nullable=False,
        index=True,
    )

    gender: Optional[str] = Field(
        default=None,
        max_length=30,
        nullable=True,
    )

    phone: str = Field(
        max_length=20,
        nullable=False,
        index=True,
    )

    address: str = Field(
        max_length=255,
        nullable=False,
    )

    city: str = Field(
        max_length=100,
        nullable=False,
        index=True,
    )

    state: str = Field(
        max_length=100,
        nullable=False,
        index=True,
    )

    zipcode: str = Field(
        max_length=20,
        nullable=False,
    )

    country: str = Field(
        max_length=100,
        nullable=False,
        index=True,
    )

    category: str = Field(
        max_length=100,
        nullable=False,
        index=True,
    )

    sub_category: int = Field(
        nullable=False,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )


# ==========================================================
# USER GROUP LINK TABLE
# ==========================================================

class UserGroupLink(SQLModel, table=True):
    __tablename__ = "user_group_links"

    user_id: int = Field(
        foreign_key="customer_users.id",
        primary_key=True,
        ondelete="CASCADE",
    )

    group_id: int = Field(
        foreign_key="user_groups.id",
        primary_key=True,
        ondelete="CASCADE",
    )


# ==========================================================
# CUSTOMER USER MODEL
# ==========================================================

class CustomerUser(SQLModel, table=True):
    __tablename__ = "customer_users"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    username: str = Field(
        max_length=100,
        index=True,
        unique=True,
        nullable=False,
    )

    email: str = Field(
        max_length=255,
        index=True,
        unique=True,
        nullable=False,
    )

    city: str = Field(
        max_length=100,
        nullable=False,
    )

    state: str = Field(
        max_length=100,
        nullable=False,
    )

    country: str = Field(
        max_length=100,
        nullable=False,
    )

    category: str = Field(
        max_length=50,
        index=True,
        nullable=False,
    )

    is_admin: bool = Field(
        default=False,
        nullable=False,
    )

    is_employee: bool = Field(
        default=False,
        nullable=False,
    )

    is_client: bool = Field(
        default=False,
        nullable=False,
    )

    is_applicant: bool = Field(
        default=False,
        nullable=False,
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
    )

    resume_file: str = Field(
        max_length=500,
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    groups: list["UserGroups"] = Relationship(
        back_populates="users",
        link_model=UserGroupLink,
    )


# ==========================================================
# USER GROUP MODEL
# ==========================================================

class UserGroups(SQLModel, table=True):
    __tablename__ = "user_groups"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    name: str = Field(
        min_length=2,
        max_length=150,
        unique=True,
        index=True,
        nullable=False,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    is_active: bool = Field(
        default=True,
        index=True,
        nullable=False,
    )

    is_featured: bool = Field(
        default=False,
        index=True,
        nullable=False,
    )

    users: list["CustomerUser"] = Relationship(
        back_populates="groups",
        link_model=UserGroupLink,
    )