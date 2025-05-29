from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.respository.users.get_users import get_all_users
from api.respository.users.update_users import update_user
from api.respository.users.delete_users import delete_user
from core.db.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def fetch_users(db: Session = Depends(get_db)):
    """Fetch all users with optional limit"""
    try:
        result = await get_all_users(db=db)
        return result
    except Exception:
        raise


@router.put("/{user_id}")
async def update_user_endpoint(
    user_id: str, user_data: dict, db: Session = Depends(get_db)
):
    """Update a user's information"""
    try:
        result = await update_user(user_id=user_id, user_data=user_data, db=db)
        return result
    except Exception:
        raise


@router.delete("/{user_id}")
async def delete_user_endpoint(user_id: str, db: Session = Depends(get_db)):
    """Delete a user"""
    try:
        result = await delete_user(user_id=user_id, db=db)
        return result
    except Exception:
        raise
