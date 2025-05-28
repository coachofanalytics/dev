from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.core.db.database import Base


class TaskHistory(Base):
    __tablename__ = "task_history"
    __table_args__ = {"schema": "v1"}

    level1 = Column(String)
    level2 = Column(String)
    level3 = Column(String)
    level4 = Column(String)
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))
