from fastapi import HTTPException, status


ALLOWED_ENVIRONMENTS = {
    "production",
    "uat",
    "training",
}


ALLOWED_VACANCY_STATUSES = {
    "draft",
    "sample",
    "uat",
    "approved",
    "closed",
}


def validate_vacancy_status(
    vacancy_status: str,
    environment_status: str,
):
    if vacancy_status not in ALLOWED_VACANCY_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid vacancy status.",
        )

    if environment_status not in ALLOWED_ENVIRONMENTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid environment status.",
        )


def can_accept_applications(
    vacancy,
) -> bool:
    return (
        vacancy.is_active
        and vacancy.vacancy_status == "approved"
        and vacancy.environment_status == "production"
    )


def vacancy_status_label(
    vacancy,
) -> str:
    if vacancy.environment_status in {
        "uat",
        "training",
    }:
        return "UAT / Training Content"

    if vacancy.vacancy_status == "approved":
        return "Current Opening"

    if vacancy.vacancy_status == "closed":
        return "Closed"

    return "Not Currently Recruiting"