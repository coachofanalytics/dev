from typing import Tuple

from .auth import AuthToken, Credentials
from .exceptions import AuthenticationError, InvalidCredentialsError
from ..user.user import User
from ..user.user_service import UserService


class AuthService:
    """Service implementing authentication-related business operations."""

    def __init__(self, user_service: UserService, secret_key: str):
        self.user_service = user_service
        self.secret_key = secret_key

    def authenticate(self, credentials: Credentials) -> Tuple[User, AuthToken]:
        """
        Complex business operation: Authenticate user and generate tokens.

        Business rules:
        - Credentials must be valid
        - User must exist
        - User must be active
        - Password must match
        - Must generate both access and refresh tokens
        """
        # Validate credentials format
        credentials.validate()

        # Get user and verify existence
        user = self.user_service.get_user_by_email(credentials.email)
        if not user:
            raise InvalidCredentialsError("Invalid email or password")

        # Verify user is active
        if not user.is_active:
            raise AuthenticationError("User account is deactivated")

        # Verify password (assuming password is hashed)
        if not self._verify_password(credentials.password, user.password_hash):
            raise InvalidCredentialsError("Invalid email or password")

        # Update last login
        self.user_service.update_last_login(user.id)

        # Generate tokens
        tokens = AuthToken.create_tokens(user, self.secret_key)

        return user, tokens

    def refresh_token(self, refresh_token: str) -> AuthToken:
        """
        Complex business operation: Refresh access token.

        Business rules:
        - Refresh token must be valid
        - Refresh token must not be expired
        - User must exist and be active
        - Must generate new access token
        """
        try:
            # Decode and verify refresh token
            payload = self._decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise AuthenticationError("Invalid token type")

            # Get user and verify existence/status
            user = self.user_service.get_user(payload["sub"])
            if not user.is_active:
                raise AuthenticationError("User account is deactivated")

            # Generate new access token
            return AuthToken.create_tokens(user, self.secret_key)

        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Refresh token has expired")
        except jwt.InvalidTokenError:
            raise AuthenticationError("Invalid refresh token")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Business rule: Verify password against hash."""
        # In real implementation, use proper password hashing
        # This is just a placeholder
        return plain_password == hashed_password

    def _decode_token(self, token: str) -> dict:
        """Business rule: Decode and verify JWT token."""
        return jwt.decode(token, self.secret_key, algorithms=["HS256"])
