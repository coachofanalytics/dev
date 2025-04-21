from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class OrgSchema(BaseModel):
    id: UUID
    project_id: UUID
    industry_id: UUID
    name: str
    description: str
    is_sub_org: bool
    sub_org_desc: str
    preceding_org_id: UUID
    is_benchmarkable: bool 
    is_benchmark: bool 
    is_internal: bool 
    is_global_external: bool 
    published: bool
    published_searchable: bool
    published_date: datetime
    publication_venue: str
    published_state: str
    total_conversations: float
    low_span_threshold: int
    is_low_span_threshold_changed: bool
    is_accessed: bool
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime



class OrgResponseSchema(BaseModel):
    id: UUID
    project_id: UUID
    industry_id: UUID
    name: str
    description: str
    is_sub_org: bool
    sub_org_desc: str
    preceding_org_id: UUID
    is_benchmarkable: bool 
    is_benchmark: bool 
    is_internal: bool 
    is_global_external: bool 
    published: bool
    published_searchable: bool
    published_date: datetime
    publication_venue: str
    published_state: str
    total_conversations: float
    low_span_threshold: int
    is_low_span_threshold_changed: bool
    is_accessed: bool
    created_by: UUID
    created_date: datetime
    updated_by: UUID
    updated_date: datetime

    class Config:
        orm_mode = True 