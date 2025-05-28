from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    """Domain model representing a user in the system."""

    id: int
    email: str
    username: str
    is_active: bool = True
    created_at: datetime = datetime.now()
    last_login: Optional[datetime] = None

    def validate_email(self) -> bool:
        """Business rule: Email must be valid and unique."""
        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")
        return True

    def validate_username(self) -> bool:
        """Business rule: Username must be between 3 and 50 characters."""
        if not 3 <= len(self.username) <= 50:
            raise ValueError("Username must be between 3 and 50 characters")
        return True

    def deactivate(self) -> None:
        """Business rule: Deactivate user account."""
        self.is_active = False

    def update_last_login(self) -> None:
        """Business rule: Update last login timestamp."""
        self.last_login = datetime.now()
