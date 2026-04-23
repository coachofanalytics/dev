from fastapi import APIRouter, Depends
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionCreate
from app.core.models.transactions.transaction import Transaction


router = APIRouter(
    tags = ['Transactions']
)

@router.put('/transaction/{id}')
def update_transaction(id, request:TransactionCreate, db: Session = Depends(get_db)):

    transaction = db.query(Transaction).filter(Transaction.id == id)

    if not transaction.first():
        return {"error": f"Transaction {id} not found"}

    transaction.update(request.model_dump())
    db.commit()
    
    return {f"Transaction {id} was Successfully Updated"}