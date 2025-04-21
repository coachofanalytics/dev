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

@router.put('/update_org{id}')
def update_org(id, request:OrgSchema, db: Session=Depends(get_db)):
    org = db.query(Orgs).filter(Orgs.id == id)

    if not product.first():
        pass

    org.update(request.dict())
    db.commit()
    return {'Org Successfully Updated'}


