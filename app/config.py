from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

UPLOAD_DIR = BASE_DIR / "uploads"
RESUME_UPLOAD_DIR = UPLOAD_DIR / "resumes"

ALLOWED_RESUME_EXTENSIONS = {
    ".pdf",
    ".doc",
    ".docx",
}

ALLOWED_RESUME_CONTENT_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

MAX_RESUME_SIZE = 5 * 1024 * 1024


RESUME_UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True,
)