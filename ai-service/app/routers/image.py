"""
Image router — Gate 2.

Exposes POST /ai/validate-image. This is the only image-related endpoint
in scope for Gate 2. Background removal, enhancement, and vision
endpoints belong to later gates and must not be added here yet.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.services.image_service import validate_image

router = APIRouter(tags=["image"])


@router.post("/ai/validate-image")
@router.post("/ai/validate")
@router.post("/image/validate")
async def validate_product_image(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Validate an uploaded product image.

    Returns 200 with image metadata if valid.
    Returns 400 with a human-readable reason if invalid.
    """
    upload = file or image
    if upload is None:
        raise HTTPException(status_code=400, detail="Uploaded image file is missing.")
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    try:
        img = validate_image(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "valid": True,
        "width": img.width,
        "height": img.height,
        "format": img.format,
    }
