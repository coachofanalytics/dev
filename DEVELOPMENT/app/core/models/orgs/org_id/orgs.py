from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.core.db.database import Base

class Orgs(Base):
    __tablename__ = "orgs" 
    __table_args__ = {'schema': 'v1'}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    project_id = Column(UUID)
    industry_id = Column(UUID)
    name = Column(String)
    descriptione = Column(String)
    is_sub_org = Column(Boolean)
    sub_org_desc = Column(String)
    preceding_org_id = Column(UUID)
    is_benchmarkable = Column(Boolean)
    is_benchmark = Column(Boolean)
    is_internal = Column(Boolean)
    is_global_external = Column(Boolean)
    published = Column(Boolean)
    published_searchable = Column(Boolean)
    published_date = Column(DateTime)
    publication_venuee = Column(String)
    published_state = Column(String)
    total_conversations = Column(Float)
    low_span_threshold = Column(Integer)
    is_low_span_threshold_changed = Column(Boolean)
    is_accessed = Column(Boolean)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))