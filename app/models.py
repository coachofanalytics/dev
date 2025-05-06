from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.orm import relationship
from app.core.db.database import get_db, Base

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    description = Column(String)
    price = Column(Integer)
    user_id = Column(Integer, ForeignKey("users.id"))
    users = relationship("User", back_populates="products")


class User(Base):
    __tablename__ = "users"
    id = Column(Integer,primary_key=True, index=True )
    username = Column(String)
    email = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)
    products = relationship("Product", back_populates="users")
    # project = relationship("Project", back_populates="user")


# class Project(Base):
#     __tablename__ = "projects"
#     id = Column(Integer,primary_key=True, index=True )
#     name = Column(String)
#     user_id = Column(Integer, ForeignKey("users.id"))cla
#     user = relationship("User", back_populates="project")


#=============================================================================

# class Industry(Base):
#     __tablename__ = "industry"
#     __table_args__ = {'schema': 'v1'}
#     level1 = Column(String)
#     level2 = Column(String)
#     level3 = Column(String)
#     level4 = Column(String)
#     id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
#     created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
#     created_date = Column(DateTime(timezone=True))
#     updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
#     updated_date = Column(DateTime(timezone=True))



# class Project(Base):
#     __tablename__ = "industry"
#     # __table_args__ = {'schema': 'v1'}
#     level1 = Column(String)
#     level2 = Column(String)
#     level3 = Column(String)
#     level4 = Column(String)
#     id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
#     created_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
#     created_date = Column(DateTime(timezone=True))
#     updated_by = Column(UUID(as_uuid=True), default=uuid.uuid4)
#     updated_date = Column(DateTime(timezone=True))

# class Project()
#     level1 = Column(String)
    # level2 = Column(String)