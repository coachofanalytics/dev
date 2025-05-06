from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.core.db.database import Base

class Extpositions(Base):
    __tablename__ = "ext_positions"
    __table_args__ = {'schema': 'v1'}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    position_id = Column(UUID)
    raw_data = Column(JSON)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))


# references positions (position_id --> ForeignKey)
