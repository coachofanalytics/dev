from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.industry.industry import Industry

# Router is required
router = APIRouter(tags=["industry"])


@router.delete("/industry/{id}")
def delete_industry(id, db: Session = Depends(get_db)):
    db.query(Industry).filter(Industry.id == id).delete(synchronize_session=False)
    db.commit()
    return {"Industry Deleted"}
