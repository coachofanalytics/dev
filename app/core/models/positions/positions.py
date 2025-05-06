from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.core.db.database import Base

class Positions(Base):
    __tablename__ = "positions"
    __table_args__ = {'schema': 'v1'}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    title_id = Column(UUID)
    location_id = Column(UUID)
    dept_id = Column(UUID)
    copy_position_id = Column(UUID)
    role_type = Column(String)
    base_compensation = Column(Float)
    bonus = Column(Float)
    fringe_benefits = Column(Float)
    fully_loaded_compensation = Column(Float)
    is_active = Column(Boolean)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))

# Need to define relationships (foreign keys title, department and location)