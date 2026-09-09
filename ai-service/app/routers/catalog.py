"""
Catalog router — Gate 11: Catalog Orchestration.

Exposes POST /ai/generate-catalog.
Accepts an artisan product photo, optional voice recording, and optional cost details,
and returns the complete, unified catalog JSON structure.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.models.catalog import CatalogResult
from app.services.catalog_service import orchestrate_catalog

router = APIRouter(tags=["catalog"])


@router.post("/ai/generate-catalog", response_model=CatalogResult)
async def generate_catalog(
    image: Optional[UploadFile] = File(None, description="Product photograph to be validated, segmented, and analyzed."),
    photo: Optional[UploadFile] = File(None, description="Product photograph alias."),
    file: Optional[UploadFile] = File(None, description="Product photograph alias."),
    audio: Optional[UploadFile] = File(None, description="Optional artisan voice audio file."),
    raw_material_cost: Optional[float] = Form(0.0, description="Raw material cost in INR."),
    labour_cost: Optional[float] = Form(0.0, description="Artisan labour cost in INR."),
    packaging_cost: Optional[float] = Form(0.0, description="Packaging cost in INR."),
    other_cost: Optional[float] = Form(0.0, description="Miscellaneous overhead in INR."),
    quality: Optional[str] = Form("standard", description="Artisan craft quality ('standard', 'high', 'premium')."),
    demand: Optional[str] = Form("medium", description="Market demand ('low', 'medium', 'high')."),
    artisan_notes: Optional[str] = Form(None, description="Optional artisan story or notes."),
    skip_bg_removal: Optional[bool] = Form(False, description="Optional flag to skip background removal for faster processing."),
) -> CatalogResult:
    """
    Generate a full marketplace product listing from a photo and optional audio.

    Coordinates:
        - Image validation, background removal, and enhancement
        - Product vision & attribute extraction
        - Voice transcription & multilingual translation
        - AI description generation (English & Hindi)
        - SEO title & keyword generation
        - Pricing recommendation and cost breakdown
    """
    img = image or photo or file
    if img is None:
        raise HTTPException(status_code=400, detail="Image file is missing.")
    image_bytes = await img.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    audio_bytes: Optional[bytes] = None
    audio_filename: str = "audio.wav"
    if audio is not None:
        audio_bytes = await audio.read()
        audio_filename = audio.filename or "audio.wav"

    try:
        result = orchestrate_catalog(
            image_bytes=image_bytes,
            image_filename=img.filename or "product.jpg",
            image_mime_type=img.content_type or "image/jpeg",
            audio_bytes=audio_bytes,
            audio_filename=audio_filename,
            raw_material_cost=raw_material_cost or 0.0,
            labour_cost=labour_cost or 0.0,
            packaging_cost=packaging_cost or 0.0,
            other_cost=other_cost or 0.0,
            quality=quality,
            demand=demand,
            artisan_notes=artisan_notes,
            skip_bg_removal=bool(skip_bg_removal),
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Catalog orchestration failed: {exc}",
        )


@router.post("/products/process")
@router.post("/ai/products/process")
async def process_product_contract(
    photo: Optional[UploadFile] = File(None),
    image: Optional[UploadFile] = File(None),
    file: Optional[UploadFile] = File(None),
    audio: Optional[UploadFile] = File(None),
    raw_material_cost: Optional[float] = Form(0.0),
):
    """
    Person 1 (Flutter) ↔ Person 2/3 Contract endpoint per API_CONTRACT.md section 1.

    Accepts:
        photo: file (jpg/png)
        audio: file (m4a/wav) — optional voice description
        raw_material_cost: number

    Returns 200:
        {
            "image_url": "...",
            "description_hi": "...",
            "description_en": "...",
            "price": 850,
            "price_reason": "Cost ₹250 + labour + market rate for similar items"
        }
    """
    img = photo or image or file
    if img is None:
        raise HTTPException(status_code=400, detail="Photo file is missing.")
    img_bytes = await img.read()
    if not img_bytes:
        raise HTTPException(status_code=400, detail="Photo file is empty.")

    aud_bytes: Optional[bytes] = None
    aud_fname = "audio.wav"
    if audio is not None:
        aud_bytes = await audio.read()
        aud_fname = audio.filename or "audio.wav"

    try:
        result = orchestrate_catalog(
            image_bytes=img_bytes,
            image_filename=img.filename or "product.jpg",
            image_mime_type=img.content_type or "image/jpeg",
            audio_bytes=aud_bytes,
            audio_filename=aud_fname,
            raw_material_cost=raw_material_cost or 0.0,
        )
        return {
            "id": f"prod_{uuid.uuid4().hex[:8]}",
            "image_url": result.images.processed or result.images.original or "",
            "description_hi": result.description.hindi or "",
            "description_en": result.description.english or "",
            "price": result.pricing.recommended,
            "price_reason": result.pricing.explanation or "",
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Product processing failed: {exc}")


class PublishProductRequest(BaseModel):
    image_url: Optional[str] = None
    description_hi: Optional[str] = None
    description_en: Optional[str] = None
    price: float = 0.0
    price_reason: Optional[str] = None
    artisan_id: Optional[str] = "default"


CATALOG_STORAGE: list = []


@router.post("/products")
@router.post("/ai/products")
async def publish_product(payload: PublishProductRequest):
    """
    Person 3 Contract endpoint per API_CONTRACT.md section 2.
    Accepts:
        image_url: str
        description_hi: str
        description_en: str
        price: number
        price_reason: str
    Returns 200:
        {"id": "abc123"}
    """
    product_id = f"prod_{uuid.uuid4().hex[:8]}"
    item = {
        "id": product_id,
        "image_url": payload.image_url or "",
        "description_hi": payload.description_hi or "",
        "description_en": payload.description_en or "",
        "price": payload.price,
        "price_reason": payload.price_reason or "",
        "artisan_id": payload.artisan_id or "default",
    }
    CATALOG_STORAGE.append(item)
    return {"id": product_id}


@router.get("/products")
@router.get("/ai/products")
async def get_catalog(artisan_id: Optional[str] = None):
    """
    Person 3 Contract endpoint per API_CONTRACT.md section 3.
    Returns 200:
        List of product objects matching the contract schema.
    """
    if artisan_id:
        return [p for p in CATALOG_STORAGE if p.get("artisan_id") == artisan_id]
    return CATALOG_STORAGE

