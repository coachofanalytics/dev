from typing import Optional
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone

from sqlmodel import Field, SQLModel
   



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





def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Score(SQLModel, table=True):
    __tablename__ = "accounts_score"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    email: str = Field(
        max_length=255,
        nullable=False,
        index=True,
    )

    gender: str | None = Field(
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




class UserGroupLink(SQLModel, table=True):
    """
    Junction table connecting users and groups.
    """

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


class CustomerUser(SQLModel, table=True):
    """
    Basic user model.
    """

    __tablename__ = "customer_users"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

    username: str = Field(
        min_length=2,
        max_length=150,
        unique=True,
        index=True,
    )

    email: str = Field(
        max_length=255,
        unique=True,
        index=True,
    )

    is_admin: bool = Field(
        default=False,
    )

    is_active: bool = Field(
        default=True,
    )

    groups: list["UserGroups"] = Relationship(
        back_populates="users",
        link_model=UserGroupLink,
    )


class UserGroups(SQLModel, table=True):
    """
    User group model.
    """

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
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500,
    )

    is_active: bool = Field(
        default=True,
        index=True,
    )

    is_featured: bool = Field(
        default=False,
        index=True,
    )

    users: list["CustomerUser"] = Relationship(
        back_populates="groups",
        link_model=UserGroupLink,
    )