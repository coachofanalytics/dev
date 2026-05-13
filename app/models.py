from sqlalchemy import Column, Integer, String, DateTime, Numeric
from sqlalchemy.ext.declarative import declarative_base
import datetime

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, nullable=True)
    department_id = Column(Integer, nullable=True)
    receiver = Column(String(100), nullable=True)
    phone = Column(String(50), nullable=True)
    type = Column(String(100), nullable=True)
    activity_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    receipt_link = Column(String(255), nullable=True)
    qty = Column(Numeric(10, 2), nullable=True)
    amount = Column(Numeric(10, 2), nullable=True)
    transaction_cost = Column(Numeric(10, 2), default=0, nullable=False)
    description = Column(String, nullable=True)
    payment_method = Column(String(50), nullable=False, default="Other")
    category = Column(String(100), nullable=False)
    total_transactions_amt = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False
    )