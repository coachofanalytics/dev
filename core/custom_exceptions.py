class RecordNotFoundError(Exception):
    """Raised when a requested record is not found in the database."""

    pass


class Unauthorized(Exception):
    """Raised when a user is not authorized to perform an action."""

    pass


class ValidationError(Exception):
    """Raised when data validation fails."""

    pass


class DatabaseError(Exception):
    """Raised when there is an error with database operations."""

    pass
