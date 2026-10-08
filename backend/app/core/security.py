from pathlib import Path
from uuid import uuid4
import mimetypes

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "text/csv",
    "application/json",
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_EXTENSIONS = {".pdf", ".txt", ".csv", ".json", ".jpg", ".jpeg", ".png", ".webp"}

def sanitize_filename(filename: str) -> str:
    name = Path(filename).name.replace("\\", "_").replace("/", "_")
    stem = Path(name).stem.replace("..", "_")
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        suffix = ".bin"
    return f"{uuid4().hex}_{stem[:80]}{suffix}"

def validate_upload_metadata(filename: str, content_type: str | None, size: int, max_mb: int) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported file extension: {suffix or 'none'}")
    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported content type: {content_type}")
    if size <= 0:
        raise ValueError("Uploaded file is empty.")
    if size > max_mb * 1024 * 1024:
        raise ValueError(f"File exceeds the {max_mb} MB limit.")

def sniff_content_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"
