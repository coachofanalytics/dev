from fastapi import HTTPException, status


def validate_roles(
    *,
    is_admin: bool,
    is_employee: bool,
    is_client: bool,
    is_applicant: bool,
) -> None:
    roles = [
        is_admin,
        is_employee,
        is_client,
        is_applicant,
    ]

    if not any(roles):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "At least one customer-user role "
                "must be selected."
            ),
        )