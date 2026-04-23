from fastapi import APIRouter, Request
from fastapi.params import Depends
from typing import List
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionResponse
from app.core.models.transactions.transaction import Transaction
from app.core.dependencies.auth import get_current_user
from app.core.models.users.user import User


router = APIRouter(
    tags = ['Transactions']
)

@router.get('/transaction', response_model=List[TransactionResponse])
def get_transactions(
    request:Request, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
    ):

    transaction = db.query(Transaction).all()
    
    return transaction