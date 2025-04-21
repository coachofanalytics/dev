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


@router.post('/org', status_code=status.HTTP_201_CREATED)
def add_orgs(request:OrgSchema, db: Session = Depends(get_db)):
    new_org = Orgs(
        project_id = request.project_id,
        industry_id = request.industry_id,
        name = request.name,
        descriptione = request.description,
        is_sub_org = request.is_sub_org,
        sub_org_desc = request.sub_org_desc,
        preceding_org_id = request.preceding_org_id,
        is_benchmarkable = request.is_benchmarkable,
        is_benchmark = request.is_benchmark,
        is_internal = request.is_internal,
        is_global_external = request.is_global_external,
        published = request.published,
        published_searchable = request.published_searchable,
        published_date = request.published_date,
        publication_venuee = request.publication_venue,
        published_state = request.published_state,
        total_conversations =request.total_conversations,
        low_span_threshold = request.low_span_threshold,
        is_low_span_threshold_changed = request.is_low_span_threshold_changed,
        is_accessed = request.is_accessed,
        created_by = request.created_by,
        created_date = request.created_date,
        updated_by = request.updated_by,
        updated_date = request.updated_date
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)
    return request

