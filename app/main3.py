from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

app = FastAPI(
    title="INFLOW MANAGEMENT API - main3",
    description="create inflow records using pydantic validation",
    version="1.0.0"
)

class Inflow(BaseModel):
    sender: Optional[int] = None
    receiver: Optional[str] = None
    phone: Optional[str] = None
    transaction_date: Optional[datetime] = None
    receipt_link: Optional[str] = None
    qty: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None

# Root endpoint
@app.get("/")
def home():
    return {"message": "main3 - pydantic POST validation", }

# Create a new inflow
@app.post("/inflow/")
def create_inflow(inflow: Inflow):
    return {"message": "Inflow recorded successfully", "data": inflow}
