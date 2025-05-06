from pydantic import BaseModel, Field
from typing import Optional
import uuid
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.db.database import Base



class Access(Base):
    """Access Table Model"""

    __tablename__ = "access"

    user_id = Column(UUID, primary_key=True, nullable=False)
    project_id = Column(UUID, ForeignKey("v1.projects.id"), primary_key=True, nullable=False)
    access_level = Column(String, nullable=False)

    user_projects = relationship("Projects", back_populates="access")


# class AccessResponseSchema(BaseModel):
#     user_id: uuid.UUID = Field(alias='userID')
#     access_level: Optional[str]=Field (alias =acessLevel)
