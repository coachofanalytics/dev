from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransactionBase(BaseModel):
    sender_id: Optional[int]
    department_id: Optional[int]
    receiver: Optional[str]
    phone: Optional[str]
    type: Optional[str]
    activity_date: datetime
    receipt_link: Optional[str]
    qty: Optional[float]
    amount: Optional[float]
    transaction_cost: float = 0
    description: Optional[str]
    payment_method: str
    category: str
    total_transactions_amt: Optional[float]

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int
    created_at: datetime
    updated_at: datetime

model_config = {
    "from_attributes": True
}