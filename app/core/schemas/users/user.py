from pydantic import BaseModel, EmailStr

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    
class UserLogin(BaseModel):
    username: str
    password: str
    
class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    
    class Config:
        from_attributes = True