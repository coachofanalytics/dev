import os
from secrets import compare_digest
from typing import Annotated

from fastapi import Header, HTTPException, status


def require_authorized_user(
    x_api_key: Annotated[
        str | None,
        Header(alias="X-API-Key"),
    ] = None,
) -> str:
    expected_api_key = os.getenv("SCORE_API_KEY")

    if not expected_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="SCORE_API_KEY is not configured.",
        )

    if (
        x_api_key is None
        or not compare_digest(x_api_key, expected_api_key)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to manage Score records.",
        )

    return x_api_key