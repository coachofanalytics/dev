from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.database import engine, create_db_and_tables

app = FastAPI(
    title="INFLOW MANAGEMENT API - main5",
    description="Handles inflows and automatically parses ISO datetimes",
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
    internal_note: Optional[str] = None

# In-memory storage for demo
mock_inflows = []

@app.get("/")
def home():
    return {"message": "main5 - response model with datetime parsing"}

@app.post("/inflows/")
def create_inflow(inflow: InflowCreate):
    # Convert ISO 8601 string with 'Z' to Python datetime if necessary
    if inflow.transaction_date and isinstance(inflow.transaction_date, str):
        inflow.transaction_date = datetime.fromisoformat(inflow.transaction_date.replace("Z", "+00:00"))

    inflow_id = len(mock_inflows) + 1
    record = inflow.dict()
    record["id"] = inflow_id
    mock_inflows.append(record)
    return {"message": "Inflow recorded successfully", "data": record}

@app.get("/inflows/{inflow_id}")
def get_inflow(inflow_id: int):
    inflow = next((x for x in mock_inflows if x["id"] == inflow_id), None)
    if inflow is None:
        return {"error": "Inflow not found"}
    return inflow

@app.get("/inflows/")
def list_inflows(skip: int = 0, limit: int = 10, sender: Optional[int] = None):
    results = mock_inflows
    if sender is not None:
        results = [x for x in results if x["sender"] == sender]
    return results[skip : skip + limit]