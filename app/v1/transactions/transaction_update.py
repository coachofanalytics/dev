from fastapi import APIRouter, Depends, HTTPException
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionCreate
from app.core.models.transactions.transaction import Transaction
from app.core.dependencies.auth import get_current_user
from app.core.models.users.user import User
router = APIRouter(
    tags = ['Transactions']
)

@router.put('/transaction/{id}')
def update_transaction(
    id: int, 
    request:TransactionCreate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    transaction = db.query(Transaction).filter(Transaction.id == id)

    if not transaction.first():
       raise HTTPException(status_code=404, detail=f"Transaction {id} not found")

    transaction.update(request.model_dump())
    db.commit()
    
    return {f"Transaction {id} was Successfully Updated"}