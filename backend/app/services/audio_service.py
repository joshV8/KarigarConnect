"""
Audio storage service — uploads voice recordings to Cloudinary (production)
or local static storage (dev fallback).  Re-uses the Cloudinary config from
app.config without duplicating credentials.
"""
import os
import uuid
import logging
from typing import Set
from fastapi import UploadFile, HTTPException, status
import cloudinary
import cloudinary.uploader

from app.config import (
    IS_CLOUDINARY_CONFIGURED,
)

logger = logging.getLogger("artisan.audio_service")

# ---- validation constants ------------------------------------------------
MAX_AUDIO_SIZE_BYTES: int = 50 * 1024 * 1024  # 50 MB

# Broad set — includes every format the Flutter `record` package can produce
# on Android (AAC/M4A), iOS (AAC/M4A), Web (WebM/Opus), Linux (OGG/Opus),
# plus common field-recorder formats.
ALLOWED_AUDIO_MIME_TYPES: Set[str] = {
    "audio/aac",
    "audio/m4a",
    "audio/x-m4a",
    "audio/mp4",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/webm",
    "audio/ogg",
    "audio/opus",
    "audio/x-aac",
    "application/octet-stream",  # Flutter web sometimes sends this
}

ALLOWED_AUDIO_EXTENSIONS: Set[str] = {
    ".aac", ".m4a", ".mp3", ".mp4", ".wav", ".webm", ".ogg", ".opus",
}

CLOUDINARY_AUDIO_FOLDER = "artisan/audio"

# Local dev uploads directory
DEV_AUDIO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "audio")
)


# ---- helpers -------------------------------------------------------------

def validate_audio_file(file: UploadFile) -> str:
    """Validate audio MIME type and filename extension. Returns extension."""
    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()

    if ext and ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio extension '{ext}'. "
                f"Allowed: {', '.join(sorted(ALLOWED_AUDIO_EXTENSIONS))}"
            ),
        )

    content_type = (file.content_type or "").lower()
    if content_type and content_type not in ALLOWED_AUDIO_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Unsupported audio MIME type '{content_type}'. "
                f"Allowed formats: AAC/M4A, WAV, MP3, WebM/Opus, OGG."
            ),
        )

    return ext or ".m4a"  # sensible default if filename has no extension


async def upload_product_audio(
    file: UploadFile,
    product_id: int,
) -> str:
    """Upload a voice recording to Cloudinary (prod) or local storage (dev).

    Returns the resulting audio URL.
    """
    ext = validate_audio_file(file)

    contents = await file.read()
    if len(contents) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded audio file is empty.",
        )
    if len(contents) > MAX_AUDIO_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Audio file exceeds maximum allowed size of {MAX_AUDIO_SIZE_BYTES // (1024 * 1024)} MB.",
        )

    if IS_CLOUDINARY_CONFIGURED:
        try:
            upload_result = cloudinary.uploader.upload(
                contents,
                folder=CLOUDINARY_AUDIO_FOLDER,
                resource_type="video",   # Cloudinary uses 'video' for audio files
                public_id=f"audio_{product_id}_{uuid.uuid4().hex[:8]}",
                format=ext.lstrip(".") or "m4a",
            )
            url = upload_result.get("secure_url") or upload_result.get("url")
            logger.info(f"[CLOUDINARY] Uploaded audio for product {product_id}: {url}")
            return url
        except Exception as exc:
            logger.error(f"Cloudinary audio upload failed: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to upload audio to Cloudinary: {str(exc)}",
            )
    else:
        # Development / Offline Fallback Mode
        os.makedirs(DEV_AUDIO_DIR, exist_ok=True)
        unique_filename = f"audio_{product_id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = os.path.join(DEV_AUDIO_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"[DEV_MODE] Saved audio locally: {file_path}")
        return f"http://127.0.0.1:8000/uploads/audio/{unique_filename}"
