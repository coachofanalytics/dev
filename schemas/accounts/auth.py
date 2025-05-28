from datetime import datetime
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    """API schema for login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """API schema for token response."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_at: datetime
