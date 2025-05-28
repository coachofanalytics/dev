from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from core.db.database import get_db
from core.config.decorators._custom_error_handler import custom_exception_handler
from core.custom_exceptions import RecordNotFoundError, DatabaseError

# Import models
from models.accounts.users import CustomerUser

# Router is required
router = APIRouter(tags=["Users"])

@router.delete("/{user_id}", tags=["Users"])
@custom_exception_handler
async def delete_user(
    user_id: str,
    db: Session = Depends(get_db)
):
    """Deletes a user from the database

    Args:
        - user_id (str): ID of the user to delete
        - db (Session): Database session

    Exceptions:
        - 404: User not found
        - 500: Database error

    Returns:
        - 200: Success message
    """
    try:
        # Find the user
        user = db.query(CustomerUser).filter(CustomerUser.id == user_id).first()
        if not user:
            raise RecordNotFoundError(f"User with ID {user_id} not found")

        # Delete the user
        db.delete(user)
        db.commit()

        return {"message": f"User with ID {user_id} successfully deleted"}

    except Exception as e:
        db.rollback()
        raise DatabaseError(f"Failed to delete user: {str(e)}")
