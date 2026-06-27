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