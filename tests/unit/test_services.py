from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile
from starlette.datastructures import Headers

from app.services.customer_user_service import (
    validate_roles,
)
from app.services.resume_service import (
    validate_resume_file,
)


def create_upload_file(
    *,
    filename: str,
    content: bytes,
    content_type: str,
) -> UploadFile:
    return UploadFile(
        file=BytesIO(content),
        filename=filename,
        headers=Headers(
            {
                "content-type": content_type,
            }
        ),
    )


def test_customer_user_role_validation_accepts_applicant():
    validate_roles(
        is_admin=False,
        is_employee=False,
        is_client=False,
        is_applicant=True,
    )


def test_customer_user_role_validation_rejects_no_roles():
    with pytest.raises(HTTPException) as exc_info:
        validate_roles(
            is_admin=False,
            is_employee=False,
            is_client=False,
            is_applicant=False,
        )

    assert exc_info.value.status_code == 400
    assert "At least one" in exc_info.value.detail


@pytest.mark.asyncio
async def test_customer_user_pdf_resume_is_valid():
    upload = create_upload_file(
        filename="resume.pdf",
        content=b"%PDF-1.4 test resume",
        content_type="application/pdf",
    )

    contents = await validate_resume_file(
        upload
    )

    assert contents.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_customer_user_invalid_extension_is_rejected():
    upload = create_upload_file(
        filename="resume.exe",
        content=b"invalid executable",
        content_type="application/octet-stream",
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_resume_file(upload)

    assert exc_info.value.status_code == 400
    assert "PDF" in exc_info.value.detail


@pytest.mark.asyncio
async def test_customer_user_empty_resume_is_rejected():
    upload = create_upload_file(
        filename="resume.pdf",
        content=b"",
        content_type="application/pdf",
    )

    with pytest.raises(HTTPException) as exc_info:
        await validate_resume_file(upload)

    assert exc_info.value.status_code == 400
    assert "empty" in exc_info.value.detail.lower()