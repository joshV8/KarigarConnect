"""
Background router — Gate 3.

Exposes POST /ai/remove-background. This is the only background-removal
endpoint in scope for Gate 3. Image enhancement and vision endpoints
belong to later gates and must not be added here yet.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.services.background_service import remove_background
from app.services.image_service import validate_image

router = APIRouter(tags=["background"])


@router.post("/ai/remove-background")
@router.post("/image/remove-background")
async def remove_product_background(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
):
    """
    Remove the background from an uploaded product image.

    Reuses Gate 2's validate_image() first, so the same size/format/
    resolution/corruption rules already enforced on upload apply here
    too — this endpoint does not loosen or duplicate that logic.

    Returns the processed image as PNG bytes (image/png) with a
    transparent background on success.
    Returns 400 with a human-readable reason if the input image is
    invalid, or 500 if background removal itself fails.
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
        png_bytes = remove_background(data)
    except RuntimeError as e:
        # rembg not installed / not runnable in this environment.
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return Response(content=png_bytes, media_type="image/png")
