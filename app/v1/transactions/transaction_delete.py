from fastapi import APIRouter, Depends, HTTPException
from app.core.db.database import get_db
from sqlalchemy.orm import Session
# from app.core.schemas.transactions.transaction import TransactionSchema
from app.core.models.transactions.transaction import Transaction
from app.core.dependencies.auth import get_current_user
from app.core.models.users.user import User

router = APIRouter(
    tags = ['Transactions']
)

@router.delete('/transaction/{id}')
def delete_transaction(
    id:int, 
    db: Session = Depends(get_db),
     current_user: User = Depends(get_current_user)
    ):

    transaction = db.query(Transaction).filter(Transaction.id == id)
    if not transaction.first():
       raise HTTPException(status_code=404, detail=f"Transaction {id} not found")

    transaction.delete(synchronize_session=False)
    db.commit()

    return {f"Transaction {id} has been DELETED"}