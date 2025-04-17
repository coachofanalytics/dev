from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

#user request model
class User(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str

#user response model
class DisplayUser(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str

    class Config:
        orm_mode = True

#product request model
class Product(BaseModel):
    name: str 
    description: str
    price: int

# product response model
class DisplayProduct(BaseModel):
    name: str
    description: str
    # seller: DisplayUser

    class Config:
        orm_mode = True


# project request model
class Project(BaseModel):
    name: str
    seller: DisplayUser
    # user: str


# project response model
class DisplayProject(BaseModel):
    name: str
    class Config:
        orm_mode = True


class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

#======================================================================
class IndustrySchema(BaseModel):
    id: UUID
    level1: str
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    created_by: Optional[UUID] = None
    created_date: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    updated_date: Optional[datetime] = None

class DisplayIndustrySchema(BaseModel):
    id: UUID
    level1: Optional[str] = None
    level2: Optional[str] = None
    level3: Optional[str] = None
    level4: Optional[str] = None
    created_by: Optional[UUID] = None
    created_date: Optional[datetime] = None
    updated_by: Optional[UUID] = None
    updated_date: Optional[datetime] = None

    class Config:
        orm_mode = True 
