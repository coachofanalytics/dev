from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel
from decimal import Decimal


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

    
    
def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CareerVacancy(SQLModel, table=True):
    __tablename__ = "career_vacancies"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    title: str = Field(
        max_length=255,
        nullable=False,
        index=True,
    )

    slug: str = Field(
        max_length=255,
        nullable=False,
        unique=True,
        index=True,
    )

    location: str = Field(
        max_length=255,
        nullable=False,
    )

    employment_type: str = Field(
        max_length=100,
        nullable=False,
    )

    summary: str = Field(
        nullable=False,
    )

    responsibilities: str = Field(
        nullable=False,
    )

    qualifications: str = Field(
        nullable=False,
    )

    requirements: str = Field(
        nullable=False,
    )

    compensation: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    application_deadline: Optional[datetime] = Field(
        default=None,
    )

    published_at: Optional[datetime] = Field(
        default=None,
    )

    # draft | sample | uat | approved | closed
    vacancy_status: str = Field(
        default="draft",
        max_length=50,
        index=True,
    )

    # production | uat | training
    environment_status: str = Field(
        default="uat",
        max_length=50,
        index=True,
    )

    is_active: bool = Field(
        default=False,
        index=True,
    )

    is_featured: bool = Field(
        default=False,
        index=True,
    )

    support_contact: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    privacy_notice: Optional[str] = Field(
        default=None,
    )

    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )


class CareerApplication(SQLModel, table=True):
    __tablename__ = "career_applications"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    vacancy_id: int = Field(
        foreign_key="career_vacancies.id",
        nullable=False,
        index=True,
    )

    full_name: str = Field(
        max_length=255,
        nullable=False,
    )

    email: str = Field(
        max_length=255,
        nullable=False,
        index=True,
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    location: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    resume_file: str = Field(
        max_length=500,
        nullable=False,
    )

    cover_letter: Optional[str] = Field(
        default=None,
    )

    privacy_confirmed: bool = Field(
        default=False,
        nullable=False,
    )

    # submitted | reviewing | shortlisted | rejected | hired
    application_status: str = Field(
        default="submitted",
        max_length=50,
        index=True,
    )

    submitted_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )



# ==========================================================
# DEPARTMENTS MODEL
# ==========================================================

class Departments(SQLModel, table=True):
    __tablename__ = "departments"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    slug: str = Field(
        max_length=255,
        unique=True,
        index=True,
        nullable=False,
    )

    is_featured: bool = Field(
        default=False,
        nullable=False,
    )

    is_active: bool = Field(
        default=True,
        nullable=False,
    )

class Transaction(SQLModel, table=True):
    __tablename__ = "accounts_transactions"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    sender_id: Optional[int] = Field(
        default=None,
        foreign_key="customer_users.id",
        index=True,
    )

    department_id: Optional[int] = Field(
        default=None,
        foreign_key="departments.id",
        index=True,
    )

    receiver: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    phone: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    type: Optional[str] = Field(
        default=None,
        max_length=100,
        index=True,
    )

    activity_date: datetime = Field(
        nullable=False,
        index=True,
    )

    receipt_link: Optional[str] = Field(
        default=None,
        max_length=255,
    )

    qty: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        max_digits=10,
        ge=0,
    )

    amount: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        max_digits=10,
        ge=0,
    )

    transaction_cost: Decimal = Field(
        default=Decimal("0.00"),
        decimal_places=2,
        max_digits=10,
        ge=0,
    )

    description: Optional[str] = Field(
        default=None,
    )

    payment_method: str = Field(
        default="Other",
        max_length=50,
        index=True,
    )

    category: str = Field(
        max_length=100,
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

    @property
    def total_transactions_amt(self) -> Decimal:
        quantity = self.qty or Decimal("0.00")
        amount = self.amount or Decimal("0.00")
        cost = self.transaction_cost or Decimal("0.00")

        return (quantity * amount) + cost