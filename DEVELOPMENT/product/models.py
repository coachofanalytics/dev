from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from . database import Base

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


class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer,primary_key=True, index=True )
    name = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="project")
