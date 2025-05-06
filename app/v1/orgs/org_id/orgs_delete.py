import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.orgs.org_id.orgs import Orgs
from app.core.schemas.orgs.org_id.orgs_base import OrgSchema

# Router is required
router = APIRouter(
    tags = ['orgs']
)

@router.delete('org/{id}')
def delete_org(id, db: Session = Depends(get_db)):
    db.query(Orgs).filter(Orgs.id == id).delete(synchronize_session=False)
    db.commit()
    return {'Org Deleted'}
