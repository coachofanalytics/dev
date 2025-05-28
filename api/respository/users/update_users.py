from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.config.decorators._custom_error_handler import custom_exception_handler
from app.core.custom_exceptions import RecordNotFoundError, DatabaseError

# Import models and schemas
from app.models.accounts.users import CustomerUser
from app.schemas.accounts.users import CustomerUserFetchSchema

# Router is required
router = APIRouter(tags=["Users"])

@router.put("/{user_id}", tags=["Users"])
@custom_exception_handler
async def update_user(
    user_id: str,
    user_data: CustomerUserFetchSchema,
    db: Session = Depends(get_db)
):
    """Updates a user's information

    Args:
        - user_id (str): ID of the user to update
        - user_data (CustomerUserFetchSchema): Updated user data
        - db (Session): Database session

    Exceptions:
        - 404: User not found
        - 500: Database error

    Returns:
        - 200: Updated user information
    """
    try:
        # Find the user
        user = db.query(CustomerUser).filter(CustomerUser.id == user_id).first()
        if not user:
            raise RecordNotFoundError(f"User with ID {user_id} not found")

        # Update user fields
        user.username = user_data.username
        user.first_name = user_data.first_name
        user.last_name = user_data.last_name
        user.email = user_data.email
        user.phone = user_data.phone

        # Commit changes
        db.commit()
        db.refresh(user)

        # Return updated user
        return CustomerUserFetchSchema(
            id=str(user.id),
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone
        )

    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to update user: {str(e)}")
