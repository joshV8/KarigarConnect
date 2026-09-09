"""
SEO router — Gate 9.

Exposes POST /ai/generate-seo.
Accepts product title, description, attributes, or transcription, and returns
searchable, marketplace-ready SEO metadata (seo_title, meta_description, keywords).
"""

from fastapi import APIRouter, HTTPException

from app.models.seo import SEORequest, SEOResult
from app.services.seo_service import generate_seo_metadata

router = APIRouter(prefix="/ai", tags=["seo"])


@router.post("/generate-seo", response_model=SEOResult)
@router.post("/seo", response_model=SEOResult)
def generate_seo(payload: SEORequest) -> SEOResult:
    """
    Generate marketplace SEO metadata for an artisan product.

    Accepts:
        - title: optional product title
        - description: optional product description
        - attributes: optional dict of visual/product attributes
        - transcription: optional voice transcription or notes
        - category: optional category

    Returns:
        - seo_title
        - meta_description
        - keywords (List[str])
    """
    has_title = bool(payload.title and payload.title.strip())
    has_desc = bool(payload.description and payload.description.strip())
    has_attr = bool(payload.attributes and any(v is not None and v != "" and v != [] for v in payload.attributes.values()))
    has_trans = bool(payload.transcription and payload.transcription.strip())
    has_cat = bool(payload.category and payload.category.strip())

    if not (has_title or has_desc or has_attr or has_trans or has_cat):
        raise HTTPException(
            status_code=400,
            detail="At least one source of product information (title, description, attributes, transcription, or category) must be provided.",
        )

    try:
        result = generate_seo_metadata(
            title=payload.title,
            description=payload.description,
            attributes=payload.attributes,
            transcription=payload.transcription,
            category=payload.category,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"SEO generation service encountered an unexpected error: {exc}",
        )
