from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select
from app.database import engine, create_db_and_tables

# Use SQLite for local testing
SQLITE_URL = "sqlite:///./test.db"
engine = create_engine(SQLITE_URL, echo=True)

class Inflow(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    sender: Optional[int] = None
    receiver: Optional[str] = Field(default=None, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=100)
    transaction_date: Optional[datetime] = None
    receipt_link: Optional[str] = Field(default=None, max_length=100)
    qty: Optional[Decimal] = Field(default=None, max_digits=10, decimal_places=2)
    amount: Optional[Decimal] = Field(default=None, max_digits=12, decimal_places=2)
    description: Optional[str] = None

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(
    title="Inflow Management API - Main 6 (SQLite)",
    description="SQLite CRUD for inflow records for local testing.",
    version="1.0.0",
    lifespan=lifespan
)

@app.post("/inflows/", response_model=Inflow)
def create_inflow(inflow: Inflow):
    # Ensure transaction_date is datetime
    if inflow.transaction_date and isinstance(inflow.transaction_date, str):
        inflow.transaction_date = datetime.fromisoformat(inflow.transaction_date.replace("Z", "+00:00"))

    with Session(engine) as session:
        session.add(inflow)
        session.commit()
        session.refresh(inflow)
        return inflow

@app.get("/inflows/{inflow_id}", response_model=Inflow)
def get_inflow(inflow_id: int):
    with Session(engine) as session:
        inflow = session.get(Inflow, inflow_id)
        if not inflow:
            raise HTTPException(status_code=404, detail="Inflow not found")
        return inflow