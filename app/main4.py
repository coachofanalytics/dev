from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

app = FastAPI(
    title="INFLOW MANAGEMENT API - main4",
    description="Using respose models to control return data",
    version="1.0.0"
)

class InflowCreate(BaseModel):
    sender: Optional[int] = None
    receiver: Optional[str] = None
    phone: Optional[str] = None
    transaction_date: Optional[datetime] = None
    receipt_link: Optional[str] = None
    qty: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    description: Optional[str] = None
    # internal_note[str] = None

class InflowResponse(BaseModel):
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
    return {"message": "main4 - response model", }

# Create a new inflow
@app.get("/inflows/{inflow_id}")
def get_inflow(inflow_id: int):
    inflow = {"id": inflow_id, "receiver": "John Doe"}
    return inflow 
    