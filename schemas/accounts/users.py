from pydantic import BaseModel


class CustomerUserFetchSchema(BaseModel):
    id: str
    username: str
    first_name: str
    last_name: str
    email: str
    phone: str

    class Config:
        orm_mode = True
        from_attributes = True
