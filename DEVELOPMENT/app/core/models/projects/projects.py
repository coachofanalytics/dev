from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from app.core.db.database import Base

# class Projects(Base):
#     """Projects Table Model"""

#     __tablename__ = "projects"

#     name = Column(String, nullable=False)
#     description = Column(String, nullable=True)
#     engagement_code = Column(String, nullable=False)
#     engagement_type = Column(String, nullable=False)
#     partner = Column(String, nullable=False)
#     is_active = Column(Boolean, nullable=False)
#     creator_name = Column(String, nullable=False)

#     access = relationship("Access", back_populates="user_projects")
#     orgs = relationship("Orgs", back_populates="projects")

#     @hybrid_property
#     def total_projects(self):
#         """Calculates total number of projects in the table"""
#         return len(self)



class Projects(Base):
    __tablename__ = "projects"
    __table_args__ = {'schema': 'v1'}

    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    engagement_code = Column(String, nullable=False)
    engagement_type = Column(String, nullable=False)
    partner = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False)
    creator_name = Column(String, nullable=False)
    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    created_date = Column(DateTime(timezone=True))
    updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
    updated_date = Column(DateTime(timezone=True))

    orgs = relationship('Orgs', back_populates='project')
    access = relationship("Access", back_populates="user_projects")

    

    @hybrid_property
    def total_projects(self):
        """Calculates total number of projects in the table"""
        return len(self)



