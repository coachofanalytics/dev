from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

# Base schema – common fields
class UserBase(BaseModel):
    email: EmailStr
    username: str

# Schema for REGISTER 
class UserCreate(UserBase):
    password: str  

# Schema for LOGIN 
class UserLogin(BaseModel):
    username: str
    password: str

# Schema for RESPONSE 
class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schema for Token 
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None
