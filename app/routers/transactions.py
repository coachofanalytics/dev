from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Request,
    status,
)
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
)
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlmodel import Session

from app import crud, schemas
from app.database import get_db



router = APIRouter(
    prefix="/accounts/transactions",
    tags=["Accounts Transactions"],
)

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/pages/list",
    response_class=HTMLResponse,
)
def transaction_list_page(
    request: Request,
    receiver: Optional[str] = None,
    sender_id: Optional[int] = None,
    department_id: Optional[int] = None,
    payment_method: Optional[str] = None,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    transactions = crud.list_transactions(
        db=db,
        receiver=receiver,
        sender_id=sender_id,
        department_id=department_id,
        payment_method=payment_method,
        category=category,
        skip=0,
        limit=100,
    )

    return templates.TemplateResponse(
        request=request,
        name="transaction_list.html",
        context={
            "transactions": transactions,
            "receiver": receiver or "",
            "sender_id": sender_id or "",
            "department_id": department_id or "",
            "payment_method": payment_method or "",
            "category": category or "",
        },
    )


@router.get(
    "/pages/create",
    response_class=HTMLResponse,
)
def transaction_create_page(
    request: Request,
):
    return templates.TemplateResponse(
        "transaction_create.html",
        {
            "request": request,
            "error": None,
            "form_data": {},
        },
    )




@router.post(
    "/pages/create",
    response_class=HTMLResponse,
)
def transaction_create_submit(
    request: Request,

    activity_date: str = Form(...),
    category: str = Form(...),
    payment_method: str = Form("Other"),

    sender_id: Optional[int] = Form(None),
    department_id: Optional[int] = Form(None),

    receiver: str = Form(""),
    phone: str = Form(""),
    type: str = Form(""),

    receipt_link: str = Form(""),

    qty: Optional[float] = Form(None),
    amount: Optional[float] = Form(None),
    transaction_cost: float = Form(0),

    description: str = Form(""),

    db: Session = Depends(get_db),
):
    form_data = {
        "activity_date": activity_date,
        "category": category,
        "payment_method": payment_method,
        "sender_id": sender_id,
        "department_id": department_id,
        "receiver": receiver or None,
        "phone": phone or None,
        "type": type or None,
        "receipt_link": receipt_link or None,
        "qty": qty,
        "amount": amount,
        "transaction_cost": transaction_cost,
        "description": description or None,
    }

    try:
        payload = schemas.TransactionCreate(
            **form_data
        )

        crud.create_transaction(
            db=db,
            payload=payload,
        )

    except ValidationError as exc:

        return templates.TemplateResponse(
            "transaction_create.html",
            {
                "request": request,
                "error": str(exc),
                "form_data": form_data,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except HTTPException as exc:

        return templates.TemplateResponse(
            "transaction_create.html",
            {
                "request": request,
                "error": exc.detail,
                "form_data": form_data,
            },
            status_code=exc.status_code,
        )

    return RedirectResponse(
        url="/accounts/transactions/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )

@router.get(
    "/pages/views",
    response_class=HTMLResponse,
)
def transaction_view_page(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
):
    transaction = crud.get_transaction_or_404(
        db=db,
        transaction_id=id,
    )

    return templates.TemplateResponse(
        request=request,
        name="transaction_detail.html",
        context={
            "transaction": transaction,
        },
    )


@router.get(
    "/pages/edit",
    response_class=HTMLResponse,
)
def transaction_edit_page(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
):
    transaction = crud.get_transaction_or_404(
        db=db,
        transaction_id=id,
    )

    return templates.TemplateResponse(
        request=request,
        name="transaction_edit.html",
        context={
            "transaction": transaction,
            "error": None,
        },
    )


@router.post(
    "/pages/edit",
    response_class=HTMLResponse,
)
def transaction_edit_submit(
    request: Request,
    id: int,
    activity_date: str = Form(...),
    category: str = Form(...),
    payment_method: str = Form(...),
    sender_id: Optional[int] = Form(None),
    department_id: Optional[int] = Form(None),
    receiver: str = Form(""),
    phone: str = Form(""),
    type: str = Form(""),
    receipt_link: str = Form(""),
    qty: Optional[float] = Form(None),
    amount: Optional[float] = Form(None),
    transaction_cost: float = Form(0),
    description: str = Form(""),
    db: Session = Depends(get_db),
):
    transaction = crud.get_transaction_or_404(
        db=db,
        transaction_id=id,
    )

    try:
        payload = schemas.TransactionUpdate(
            activity_date=activity_date,
            category=category,
            payment_method=payment_method,
            sender_id=sender_id,
            department_id=department_id,
            receiver=receiver or None,
            phone=phone or None,
            type=type or None,
            receipt_link=receipt_link or None,
            qty=qty,
            amount=amount,
            transaction_cost=transaction_cost,
            description=description or None,
        )

        crud.update_transaction(
            db=db,
            transaction_id=id,
            payload=payload,
        )

    except ValidationError as exc:
        return templates.TemplateResponse(
            request=request,
            name="transaction_edit.html",
            context={
                "transaction": transaction,
                "error": str(exc),
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    except HTTPException as exc:
        return templates.TemplateResponse(
            request=request,
            name="transaction_edit.html",
            context={
                "transaction": transaction,
                "error": exc.detail,
            },
            status_code=exc.status_code,
        )

    return RedirectResponse(
        url=f"/accounts/transactions/pages/views?id={id}",
        status_code=status.HTTP_303_SEE_OTHER,
    )



@router.post(
    "/pages/delete",
)
def transaction_delete_page(
    id: int,
    db: Session = Depends(get_db),
):
    deleted = crud.delete_transaction(
        db=db,
        transaction_id=id,
    )

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return RedirectResponse(
        url="/accounts/transactions/pages/list",
        status_code=status.HTTP_303_SEE_OTHER,
    )




@router.post(
    "/",
    response_model=schemas.TransactionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction_api(
    payload: schemas.TransactionCreate,
    db: Session = Depends(get_db),
):
    return crud.create_transaction(
        db=db,
        payload=payload,
    )



@router.get(
    "/",
    response_model=list[schemas.TransactionRead],
)
def list_transactions_api(
    sender_id: Optional[int] = None,
    department_id: Optional[int] = None,
    receiver: Optional[str] = None,
    payment_method: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    return crud.list_transactions(
        db=db,
        sender_id=sender_id,
        department_id=department_id,
        receiver=receiver,
        payment_method=payment_method,
        category=category,
        skip=skip,
        limit=limit,
    )




@router.get(
    "/{transaction_id}",
    response_model=schemas.TransactionRead,
)
def get_transaction_api(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    return crud.get_transaction_or_404(
        db=db,
        transaction_id=transaction_id,
    )




@router.patch(
    "/{transaction_id}",
    response_model=schemas.TransactionRead,
)
def update_transaction_api(
    transaction_id: int,
    payload: schemas.TransactionUpdate,
    db: Session = Depends(get_db),
):
    return crud.update_transaction(
        db=db,
        transaction_id=transaction_id,
        payload=payload,
    )


# ==========================================================
# API DELETE
# DELETE /accounts/transactions/5
# ==========================================================

@router.delete(
    "/{transaction_id}",
    response_model=schemas.MessageResponse,
)
def delete_transaction_api(
    transaction_id: int,
    db: Session = Depends(get_db),
):
    deleted = crud.delete_transaction(
        db=db,
        transaction_id=transaction_id,
    )

    if deleted is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found.",
        )

    return {
        "message": "Transaction deleted successfully."
    }