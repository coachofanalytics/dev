from fastapi import APIRouter, Request
from fastapi.params import Depends
from typing import List
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionSchema, TransactionResponseSchema
from app.core.models.transactions.transaction import Transaction
from app.v1.auth.dependencies import get_current_user


router = APIRouter(
    tags = ['Transactions']
)

@router.get('/transaction', response_model=List[TransactionResponseSchema])
def get_transactions(request:Request, db: Session = Depends(get_db), current_user = Depends(get_current_user)):

    transaction = db.query(Transaction).all()
    
    return transaction