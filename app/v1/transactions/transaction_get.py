from fastapi import APIRouter, Request
from fastapi.params import Depends
from typing import List
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionResponse
from app.core.models.transactions.transaction import Transaction


router = APIRouter(
    tags = ['Transactions']
)

@router.get('/transaction', response_model=List[TransactionResponse])
def get_transactions(request:Request, db: Session = Depends(get_db)):

    transaction = db.query(Transaction).all()
    
    return transaction