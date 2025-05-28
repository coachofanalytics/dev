from models.common.base import Base


class OpenaiPrompt(Base):
    __tablename__ = "getdata_openaiprompt"
    __table_args__ = {"schema": "getdata"}

    pass
