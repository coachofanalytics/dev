from fastapi import APIRouter, status
from fastapi.params import Depends
from app.core.db.database import get_db
from sqlalchemy.orm import Session
from app.core.schemas.transactions.transaction import TransactionCreate,TransactionResponse
from app.core.models.transactions.transaction import Transaction


router = APIRouter(
    tags = ['Transactions']
)

@router.post('/transaction', status_code = status.HTTP_201_CREATED)
def add_transaction(request:TransactionCreate, db: Session = Depends(get_db)):

    new_transaction =  Transaction(
        # id = request.id,
        sender = request.sender,
        receiver = request.receiver,
        phone = request.phone,
        type = request.type,
        activity_date = request.activity_date,
        receipt_link = request.receipt_link,
        qty = request.qty,
        amount = request.amount,
        transaction_cost = request.transaction_cost,
        description = request.description,
        payment_method = request.payment_method,
        sender_id = request.sender_id,
        department_id = request.department_id,
        category_id = request.category_id,
        subcategory_id = request.subcategory_id,
    )

    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)

    return new_transaction