from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID

class access(Base):
    __tablename__ = "acess"
    __table_args__ = {'schema': 'v1'}
   
    user_id = Column(UUID, primary_key=True, nullable=False)
    project_id = Column(UUID,  ForeignKey("projects_id" primary_key=True, nullable=False)
    access_level = Column(String, nullable=False)
    user_projects=relationship("projects", back_populates ="access")
