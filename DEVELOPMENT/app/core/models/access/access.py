from pydantic import BaseModel, Field
from typing import Optional
import uuid


class AccessResponseSchema(BaseModel):
    user_id: uuid.UUID = Field(alias='userID')
    access_level: Optional[str]=Field (alias =acessLevel)
