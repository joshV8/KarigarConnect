"""
Description router — Gate 8.

Exposes POST /ai/generate-description.
Accepts verified product attributes, artisan transcription, and artisan notes,
and returns structured, marketplace-ready product descriptions grounded strictly
in supplied information.
"""

from fastapi import APIRouter, HTTPException

from app.models.description import DescriptionRequest, ProductDescriptionResult
from app.services.description_service import generate_product_description

router = APIRouter(prefix="/ai", tags=["description"])


@router.post("/generate-description", response_model=ProductDescriptionResult)
@router.post("/describe", response_model=ProductDescriptionResult)
def generate_description(payload: DescriptionRequest) -> ProductDescriptionResult:
    """
    Generate professional marketplace listing content for an artisan product.

    Accepts:
        - attributes: optional dict of visual/product attributes (e.g. from Gate 5)
        - transcription: optional voice transcription or translation (from Gate 6/7)
        - artisan_notes: optional artisan context or notes
        - language: target language (default "en")

    Returns:
        - title
        - short_description
        - description
        - features (List[str])
        - materials (List[str])
    """
    # Merge any top-level attribute fields into payload.attributes
    attrs = dict(payload.attributes or {})
    for key in ["product_name", "category", "material"]:
        val = getattr(payload, key, None)
        if val is not None and str(val).strip() and key not in attrs:
            attrs[key] = val
    # Check extra fields if any
    extra = getattr(payload, "__pydantic_extra__", None) or {}
    for k, v in extra.items():
        if k not in attrs and v is not None and str(v).strip():
            attrs[k] = v
    if attrs:
        payload.attributes = attrs

    has_attr = bool(payload.attributes and any(v is not None and v != "" and v != [] for v in payload.attributes.values()))
    has_trans = bool(payload.transcription and payload.transcription.strip())
    has_notes = bool(payload.artisan_notes and payload.artisan_notes.strip())

    if not (has_attr or has_trans or has_notes):
        raise HTTPException(
            status_code=400,
            detail="At least one source of information (attributes, transcription, or artisan_notes) must be provided.",
        )

    try:
        result = generate_product_description(
            attributes=payload.attributes,
            transcription=payload.transcription,
            artisan_notes=payload.artisan_notes,
            language=payload.language or "en",
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Description generation service encountered an unexpected error: {exc}",
        )
