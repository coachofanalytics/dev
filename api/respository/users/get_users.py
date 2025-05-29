# -*- coding: utf-8 -*-

# Required Imports
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from core.db.database import get_db
from core.config.decorators._custom_error_handler import custom_exception_handler
from core.custom_exceptions import DatabaseError

# Import auth modules

# Import models and schemas
from models.accounts.users import CustomerUser
from schemas.accounts.users import CustomerUserFetchSchema

router = APIRouter()


@router.get("/", tags=["Users"])
@custom_exception_handler
async def get_all_users(db: Session = Depends(get_db), limit: int = 10):
    """Fetches the list of users

    Args:
        - db (Session): Backend function to manage persistence of
          ORM changes. Defaults to Depends(get_db).
        - limit (int): Number of records to return. Defaults to 10, minimum 1, maximum 100.

    Exceptions
        - 400 : Bad Request - Invalid limit parameter
        - 500 : Internal server error

    Returns:
        -200 : List of users, limited by the specified number.
    """
    try:
        users = db.query(CustomerUser).limit(limit).all()
        result = []
        
        for user in users:
            try:
                if user is None:
                    continue

                user_schema = CustomerUserFetchSchema(
                    id=str(user.id) if user.id else "",
                    username=user.username or "",
                    first_name=user.first_name or "",
                    last_name=user.last_name or "",
                    email=user.email or "",
                    phone=user.phone or "",
                )
                result.append(user_schema)
            except Exception:
                continue

        return result
    except Exception as e:
        raise DatabaseError(f"Database error: {str(e)}")
