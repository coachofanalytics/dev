import uuid
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from models.common.django_base import DjangoBase


class CustomerUser(DjangoBase):
    __tablename__ = "accounts_customeruser"
    __table_args__ = {"schema": "public"}

    id = Column(UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    gender = Column(Integer)
    phone = Column(String)
    address = Column(String)
    city = Column(String)
    state = Column(String)
    zipcode = Column(String)
    country = Column(String)
    category = Column(Integer)
    sub_category = Column(Integer)
    is_admin = Column(Boolean)
    is_staff = Column(Boolean)
    is_client = Column(Boolean)
    is_applicant = Column(Boolean)
    is_employee_contract_signed = Column(Boolean)
    resume_file = Column(String)
    email_verified = Column(Boolean)
    verification_token = Column(UUID(as_uuid=True))

    class Config:
        from_attributes = True  # Updated for Pydantic v2 compatibility
