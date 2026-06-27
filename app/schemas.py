from pydantic import BaseModel
from typing import Optional

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
from typing import Optional
from datetime import datetime
from pydantic import BaseModel


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