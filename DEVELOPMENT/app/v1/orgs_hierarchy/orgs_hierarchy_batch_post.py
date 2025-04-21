import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

# Import Core Sub-Modules
from app.core.db.database import get_db
from app.core.models.orgs_hierarchy.orgs_hierarchy import OrgsHierarchy
from app.core.schemas.orgs_hierarchy.orgs_hierarchy_base import OrgHierarchySchema

# Router is required
router = APIRouter(
    tags = ['orgs_hierarchy']
)


@router.post('/org_hierarchy', status_code=status.HTTP_201_CREATED)
def add_orgs_hierarchy(request:OrgHierarchySchema, db: Session = Depends(get_db)):
    new_org_hier = OrgsHierarchy(
        org_id = request.org_id,
        parent_position_id = request.parent_position_id,
        position_id = request.position_id,
        layer = request.layer,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_org_hier)
    db.commit()
    db.refresh(new_org_hier)
    return request

