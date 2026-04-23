from fastapi import APIRouter, Depends
from app.core.db.database import get_db
from sqlalchemy.orm import Session
# from app.core.schemas.transactions.transaction import TransactionSchema
from app.core.models.transactions.transaction import Transaction


router = APIRouter(
    tags = ['Transactions']
)

@router.delete('/transaction/{id}')
def delete_transaction(id, db: Session = Depends(get_db)):

    transaction = db.query(Transaction).filter(Transaction.id == id)
    transaction.delete(synchronize_session=False)
    db.commit()

    return {f"Transaction {id} has been DELETED"}