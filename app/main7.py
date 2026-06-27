from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, Session, create_engine, select 
from app.database import engine, create_db_and_tables



MYSQL_URL = "mysql+pymysql://root:@localhost:3306/inflow_db?charset=utf8mb4"

engine = create_engine(
    MYSQL_URL,
    echo=True,
    pool_pre_ping=True,
    pool_recycle=3600
)


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
    title="Inflow Management API - Main 7",
    description="MySQL CRUD for inflow records.",
    version="1.0.0",
    lifespan=lifespan
)


@app.post("/inflows/", response_model=Inflow)
def create_inflow(inflow: Inflow):
    with Session(engine) as session:
        session.add(inflow)
        session.commit()
        session.refresh(inflow)
        return inflow


@app.get("/inflows/", response_model=List[Inflow])
def list_inflows():
    with Session(engine) as session:
        inflows = session.exec(select(Inflow)).all()
        return inflows


@app.get("/inflows/{inflow_id}", response_model=Inflow)
def get_inflow(inflow_id: int):
    with Session(engine) as session:
        inflow = session.get(Inflow, inflow_id)

        if not inflow:
            raise HTTPException(status_code=404, detail="Inflow not found")

        return inflow