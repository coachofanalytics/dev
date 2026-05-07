from sqlalchemy.orm import Session
from . import models, schemas

def create_transaction(db: Session, transaction: schemas.TransactionCreate):
    db_transaction = models.Transaction(
        sender_id=transaction.sender_id,
        department_id=transaction.department_id,
        receiver=transaction.receiver,
        phone=transaction.phone,
        type=transaction.type,
        activity_date=transaction.activity_date,
        receipt_link=transaction.receipt_link,
        qty=transaction.qty,
        amount=transaction.amount,
        transaction_cost=transaction.transaction_cost,
        description=transaction.description,
        payment_method=transaction.payment_method,
        category=transaction.category,
        total_transactions_amt=transaction.total_transactions_amt
    )
    db.add(db_transaction)
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

def get_transactions(db: Session, skip: int = 0, limit: int = 10):
    return db.query(models.Transaction).offset(skip).limit(limit).all()

def get_transaction(db: Session, transaction_id: int):
    return db.query(models.Transaction).filter(models.Transaction.id == transaction_id).first()