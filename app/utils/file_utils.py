import os
import uuid
from pathlib import Path

from fastapi import UploadFile

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024

CONTENT_TYPE_TO_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def validate_image(file: UploadFile) -> None:
    if file.content_type not in ALLOWED_TYPES:
        raise ValueError("Invalid image type")

    data = file.file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise ValueError("File too large")

    file.file.seek(0)


def save_file(file: UploadFile, upload_dir: str) -> str:
    upload_path = Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)

    extension = CONTENT_TYPE_TO_EXT.get(file.content_type)
    if not extension:
        raise ValueError("Invalid image type")

    filename = f"{uuid.uuid4()}{extension}"
    disk_path = upload_path / filename

    with disk_path.open("wb") as output:
        output.write(file.file.read())

    file.file.seek(0)

    relative_parts = disk_path.parts
    uploads_index = relative_parts.index("uploads") if "uploads" in relative_parts else None
    if uploads_index is None:
        raise ValueError("Upload path must be under uploads directory")

    relative_url = "/" + "/".join(relative_parts[uploads_index:])
    return relative_url


def delete_file(path: str) -> None:
    normalized = path.lstrip("/")
    disk_path = Path(normalized)
    if disk_path.exists() and disk_path.is_file():
        os.remove(disk_path)
