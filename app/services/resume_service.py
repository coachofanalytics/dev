from pathlib import Path
from uuid import uuid4

from fastapi import (
    HTTPException,
    UploadFile,
    status,
)

from app.config import (
    ALLOWED_RESUME_CONTENT_TYPES,
    ALLOWED_RESUME_EXTENSIONS,
    MAX_RESUME_SIZE,
    RESUME_UPLOAD_DIR,
)


async def validate_resume_file(
    resume_file: UploadFile,
) -> bytes:
    if not resume_file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A resume file is required.",
        )

    extension = Path(
        resume_file.filename
    ).suffix.lower()

    if extension not in ALLOWED_RESUME_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Only PDF, DOC and DOCX files "
                "are allowed."
            ),
        )

    if (
        resume_file.content_type
        and resume_file.content_type
        not in ALLOWED_RESUME_CONTENT_TYPES
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The uploaded resume type "
                "is not supported."
            ),
        )

    contents = await resume_file.read()

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The resume file cannot be empty.",
        )

    if len(contents) > MAX_RESUME_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The resume file must not exceed 5 MB."
            ),
        )

    return contents


async def save_resume_file(
    resume_file: UploadFile,
) -> str:
    contents = await validate_resume_file(
        resume_file,
    )

    original_filename = Path(
        resume_file.filename or "resume"
    ).name

    extension = Path(
        original_filename
    ).suffix.lower()

    generated_filename = (
        f"{uuid4().hex}{extension}"
    )

    destination = (
        RESUME_UPLOAD_DIR / generated_filename
    )

    try:
        destination.write_bytes(contents)
    except OSError as exc:
        raise HTTPException(
            status_code=(
                status.HTTP_500_INTERNAL_SERVER_ERROR
            ),
            detail="The resume could not be saved.",
        ) from exc

    return f"resumes/{generated_filename}"


def get_resume_full_path(
    stored_path: str,
) -> Path:
    filename = Path(stored_path).name

    return RESUME_UPLOAD_DIR / filename


def delete_resume_file(
    stored_path: str | None,
) -> None:
    if not stored_path:
        return

    full_path = get_resume_full_path(
        stored_path,
    )

    try:
        if full_path.exists():
            full_path.unlink()
    except OSError:
        pass