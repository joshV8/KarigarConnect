import os
import uuid
import logging
from typing import Tuple, Set
from fastapi import UploadFile, HTTPException, status
import cloudinary
import cloudinary.uploader

from app.config import (
    CLOUDINARY_FOLDER,
    IS_CLOUDINARY_CONFIGURED,
)

logger = logging.getLogger("artisan.image_service")

# Validation constants
MAX_FILE_SIZE_BYTES: int = 10 * 1024 * 1024  # 10 MB
ALLOWED_MIME_TYPES: Set[str] = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/jpg",
}
ALLOWED_EXTENSIONS: Set[str] = {".jpg", ".jpeg", ".png", ".webp"}

# Local dev uploads directory for mock/dev mode when Cloudinary credentials aren't set
DEV_UPLOADS_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "products")
)


def validate_image_file(file: UploadFile) -> str:
    """Validate image MIME content-type and filename extension."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )

    content_type = (file.content_type or "").lower()
    if content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file MIME type '{content_type}'. Allowed: {', '.join(sorted(ALLOWED_MIME_TYPES))}",
        )

    return ext


async def upload_product_image(file: UploadFile, product_id: int) -> str:
    """Upload a product image to Cloudinary (production) or local static storage (dev fallback).
    
    Returns the resulting image URL.
    """
    ext = validate_image_file(file)

    # Read and check size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB",
        )

    if IS_CLOUDINARY_CONFIGURED:
        try:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder=CLOUDINARY_FOLDER,
                resource_type="image",
                public_id=f"prod_{product_id}_{uuid.uuid4().hex[:8]}",
            )
            return upload_result.get("secure_url") or upload_result.get("url")
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload image to Cloudinary storage: {str(e)}",
            )
    else:
        # Development / Offline Fallback Mode
        os.makedirs(DEV_UPLOADS_DIR, exist_ok=True)
        unique_filename = f"prod_{product_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(DEV_UPLOADS_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(
            f"[DEV_MODE] Cloudinary credentials not set. Saved locally to {file_path}"
        )
        return f"http://127.0.0.1:8000/uploads/products/{unique_filename}"


def delete_product_image_from_storage(image_url: str) -> bool:
    """Delete the image asset from Cloudinary or local dev storage."""
    if not image_url:
        return True

    if "res.cloudinary.com" in image_url and IS_CLOUDINARY_CONFIGURED:
        try:
            # Extract public_id from Cloudinary URL
            parts = image_url.split("/")
            if "upload" in parts:
                idx = parts.index("upload")
                # Skip version tag if present (e.g. v123456789)
                path_parts = parts[idx + 1:]
                if path_parts and path_parts[0].startswith("v") and path_parts[0][1:].isdigit():
                    path_parts = path_parts[1:]
                public_id_with_ext = "/".join(path_parts)
                public_id = os.path.splitext(public_id_with_ext)[0]
                cloudinary.uploader.destroy(public_id)
                return True
        except Exception as e:
            logger.warning(f"Failed to delete asset from Cloudinary ({image_url}): {e}")
            return False
    elif "/uploads/products/" in image_url:
        try:
            filename = image_url.split("/uploads/products/")[-1]
            local_path = os.path.join(DEV_UPLOADS_DIR, filename)
            if os.path.exists(local_path):
                os.remove(local_path)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete local dev image ({image_url}): {e}")
            return False

    return True
