from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class TransactionSchema(BaseModel):
    id: int
    sender: Optional[str] = None
    receiver: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None
    activity_date: Optional[datetime] = None
    receipt_link: Optional[str] = None
    qty: Optional[int] = None
    amount: Optional[float] = None
    transaction_cost: Optional[float] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    sender_id: Optional[int] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None


class TransactionResponseSchema(BaseModel):
    id: int
    sender: Optional[str] = None
    receiver: Optional[str] = None
    phone: Optional[str] = None
    type: Optional[str] = None
    activity_date: Optional[datetime] = None
    receipt_link: Optional[str] = None
    qty: Optional[int] = None
    amount: Optional[float] = None
    transaction_cost: Optional[float] = None
    description: Optional[str] = None
    payment_method: Optional[str] = None
    sender_id: Optional[int] = None
    department_id: Optional[int] = None
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None

    class config:
        orm_mode = True
