# -*- coding: utf-8 -*-
from functools import wraps
import traceback
import logging
from fastapi import HTTPException
from core.custom_exceptions import (
    RecordNotFoundError,
    Unauthorized,
    ValidationError,
    DatabaseError,
)


def custom_exception_handler(func):
    """Exception handler decorator that is compatible with FastAPI endpoints"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        """Internal Wrapper"""
        try:
            return await func(*args, **kwargs)

        except RecordNotFoundError as e:
            logging.info("No Record Found Exception Raised")
            raise HTTPException(status_code=404, detail=str(e))

        except Unauthorized as e:
            logging.error(traceback.format_exc())
            raise HTTPException(status_code=401, detail=str(e))

        except ValidationError as e:
            logging.error(traceback.format_exc())
            raise HTTPException(status_code=400, detail=str(e))

        except DatabaseError as e:
            logging.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

        except Exception as e:
            logging.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {str(e)}"
            )

    return wrapper
