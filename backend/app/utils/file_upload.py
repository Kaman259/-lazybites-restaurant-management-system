"""Helpers for safe local image uploads."""

from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.exceptions import AppException


ALLOWED_IMAGE_TYPES = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


async def save_image_upload(
    upload: UploadFile,
    destination: Path,
    maximum_size_mb: int,
) -> str:
    """Validate and save an uploaded image."""

    if upload.content_type not in ALLOWED_IMAGE_TYPES:
        raise AppException(
            message="Only JPG, PNG and WebP images are allowed.",
            status_code=400,
        )

    file_content = await upload.read()
    maximum_size_bytes = maximum_size_mb * 1024 * 1024

    if not file_content:
        raise AppException(
            message="The uploaded image is empty.",
            status_code=400,
        )

    if len(file_content) > maximum_size_bytes:
        raise AppException(
            message=(
                f"The image cannot exceed {maximum_size_mb} MB."
            ),
            status_code=400,
        )

    destination.mkdir(parents=True, exist_ok=True)

    extension = ALLOWED_IMAGE_TYPES[upload.content_type]
    file_name = f"{uuid4().hex}{extension}"
    file_path = destination / file_name

    file_path.write_bytes(file_content)

    await upload.close()

    return file_name


def delete_local_upload(file_path: Path | None) -> None:
    """Delete an old uploaded file when it exists."""

    if file_path is None:
        return

    try:
        if file_path.exists() and file_path.is_file():
            file_path.unlink()
    except OSError:
        return