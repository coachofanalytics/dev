from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.core.db.database import Base

class OrgsHierarchy(Base):
    __tablename__ = "org_hier" 
    __table_args__ = {'schema': 'v1'}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    org_id = Column(UUID)
    parent_position_id = Column(UUID)
    position_id = Column(UUID)
    layer = Column(Integer)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))

 
