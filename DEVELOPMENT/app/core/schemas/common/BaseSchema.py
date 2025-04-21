
from pydantic import BaseModel , Extra


class BaseSchema(BaseModel):
    pass

    class Config:
        extra = Extra.forbid
        orm_mode =True
        allow_population_by_field_name = True