from fastapi import APIRouter, Depends
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionSchema
from app.core.models.transactions.transaction import Transaction
from app.v1.auth.dependencies import get_current_user

router = APIRouter(
    tags = ['Transactions']
)

@router.put('/transaction/{id}')
def update_transaction(id, request:TransactionSchema, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    transaction = db.query(Transaction).filter(Transaction.id == id)

    if not transaction.first():
        pass

    transaction.update(request.dict())
    db.commit()
    
    return {f"Transaction {id} was Successfully Updated"}