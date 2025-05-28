import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def log_error(func: Callable) -> Callable:
    """
    Decorator to log errors that occur in the decorated function.

    Args:
        func: The function to be decorated

    Returns:
        The decorated function
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            raise

    return wrapper
