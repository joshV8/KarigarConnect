"""
Enhancement router — Gate 4.

Exposes POST /ai/enhance-image. Reuses Gate 2's validate_image() before
applying enhancement, ensuring invalid uploads are rejected consistently.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.services.enhancement_service import enhance_image
from app.services.image_service import validate_image

router = APIRouter(tags=["enhancement"])


@router.post("/ai/enhance-image")
@router.post("/image/enhance")
async def enhance_product_image(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Enhance an uploaded product image for better marketplace presentation.

    Reuses Gate 2's validate_image() first, enforcing the same size, format,
    resolution, and corruption checks.

    Returns the enhanced image as PNG bytes (image/png) with brightness,
    contrast, and sharpness improvements applied.
    Returns 400 if the input image is invalid, or 500 if an unexpected error occurs.
    """
    upload = file or image
    if upload is None:
        raise HTTPException(status_code=400, detail="Uploaded image file is missing.")
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    try:
        validate_image(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        png_bytes = enhance_image(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhancement failed: {e}")

    return Response(content=png_bytes, media_type="image/png")
