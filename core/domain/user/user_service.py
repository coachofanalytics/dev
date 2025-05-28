from .user import User
from .exceptions import UserNotFoundError, UserAlreadyExistsError


class UserService:
    """Service implementing user-related business operations."""

    def __init__(self, user_repository):
        self.user_repository = user_repository

    def create_user(self, email: str, username: str) -> User:
        """
        Business operation: Create a new user.

        Business rules:
        - Email must be unique
        - Username must be unique
        - User must be validated before creation
        """
        # Check if user already exists
        if self.user_repository.find_by_email(email):
            raise UserAlreadyExistsError(f"User with email {email} already exists")

        if self.user_repository.find_by_username(username):
            raise UserAlreadyExistsError(
                f"User with username {username} already exists"
            )

        # Create and validate user
        user = User(id=0, email=email, username=username)  # Will be set by repository

        user.validate_email()
        user.validate_username()

        # Save user
        return self.user_repository.save(user)

    def get_user(self, user_id: int) -> User:
        """Business operation: Get user by ID."""
        user = self.user_repository.find_by_id(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    def deactivate_user(self, user_id: int) -> None:
        """
        Business operation: Deactivate a user.

        Business rules:
        - User must exist
        - Cannot deactivate already deactivated user
        """
        user = self.get_user(user_id)
        if not user.is_active:
            raise ValueError("User is already deactivated")

        user.deactivate()
        self.user_repository.save(user)

    def update_last_login(self, user_id: int) -> None:
        """
        Business operation: Update user's last login.

        Business rules:
        - User must exist
        - User must be active
        """
        user = self.get_user(user_id)
        if not user.is_active:
            raise ValueError("Cannot update last login for inactive user")

        user.update_last_login()
        self.user_repository.save(user)
