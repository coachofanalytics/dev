from fastapi import Header, HTTPException, status


def require_admin(
    x_admin: str | None = Header(default=None),
) -> bool:
    """
    Temporary administrator check.

    Use this header in Swagger or Postman:

    X-Admin: true
    """

    if x_admin != "true":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator permission is required.",
        )

    return True