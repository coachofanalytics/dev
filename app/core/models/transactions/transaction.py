from sqlalchemy import Column, Integer, String, DateTime, Float
from app.core.db.database import Base


class Transaction(Base):
    __tablename__ = "finance_transactions"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, index=True, default=1)
    sender = Column(String)
    receiver = Column(String)
    phone = Column(String)
    type = Column(String)
    activity_date = Column(DateTime)
    receipt_link = Column(String)
    qty = Column(Integer)
    amount = Column(Float)
    transaction_cost = Column(Float)
    description = Column(String)
    payment_method = Column(String)
    sender_id = Column(Integer)
    department_id = Column(Integer)
    category_id = Column(Integer)
    subcategory_id = Column(Integer)
