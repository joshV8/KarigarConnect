"""
Vision router — Gate 5: Product Vision / Attribute Extraction.

Exposes POST /ai/analyze-product. Reuses Gate 2's validate_image() before
invoking the multimodal LLM, ensuring bad or corrupted uploads are rejected
early with standard validation errors.
"""

from typing import Optional

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.product import ProductVisionResult
from app.services.image_service import validate_image
from app.services.vision_service import analyze_product

router = APIRouter(tags=["vision"])


@router.post("/ai/analyze-product", response_model=ProductVisionResult)
@router.post("/vision/analyze", response_model=ProductVisionResult)
async def analyze_artisan_product(
    file: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
) -> ProductVisionResult:
    """
    Analyze an uploaded artisan product image and return structured attributes.

    Reuses Gate 2's validate_image() first, enforcing format (JPEG/PNG/WEBP),
    minimum resolution (300x300), and max size (10MB).

    Uses a multimodal vision LLM (Gemini or OpenAI) to extract product name,
    category, material, color, craft type, style, visible features, and confidence.
    """
    upload = file or image
    if upload is None:
        raise HTTPException(status_code=400, detail="Uploaded image file is missing.")
    data = await upload.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded image file is empty.")

    # Step 1: Validate input image using Gate 2 validation
    try:
        validate_image(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Step 2: Extract attributes via multimodal LLM
    try:
        mime = file.content_type or "image/jpeg"
        result = analyze_product(data, mime_type=mime)
        return result
    except RuntimeError as e:
        # Missing API key or SDK configuration issue
        raise HTTPException(status_code=500, detail=str(e))
    except ValueError as e:
        # Parsing error or malformed model output
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Product vision analysis failed: {e}")
