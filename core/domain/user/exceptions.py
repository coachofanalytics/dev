class UserDomainError(Exception):
    """Base exception for user domain errors."""

    pass


class UserNotFoundError(UserDomainError):
    """Raised when a user is not found."""

    pass


class UserAlreadyExistsError(UserDomainError):
    """Raised when attempting to create a user that already exists."""

    pass


class UserValidationError(UserDomainError):
    """Raised when user validation fails."""

    pass
