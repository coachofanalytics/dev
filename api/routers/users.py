from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.respository.users.get_users import get_all_users
from core.db.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/")
async def fetch_users(db: Session = Depends(get_db)):
    try:
        result = await get_all_users(db=db)
        return result
    except Exception:
        raise
