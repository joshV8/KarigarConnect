"""
Pricing router — Gate 10.

Exposes POST /ai/recommend-price.
Accepts production cost components and product attributes, and returns a
deterministic, transparent price recommendation with explanation.
"""

from fastapi import APIRouter, HTTPException

from app.models.pricing import PricingRequest, PricingResult
from app.services.pricing_service import calculate_price_recommendation

router = APIRouter(prefix="/ai", tags=["pricing"])


@router.post("/recommend-price", response_model=PricingResult)
@router.post("/price", response_model=PricingResult)
def recommend_price(payload: PricingRequest) -> PricingResult:
    """
    Provide a transparent price recommendation for an artisan product.

    Accepts:
        - raw_material_cost: non-negative float
        - labour_cost: non-negative float
        - packaging_cost: non-negative float
        - other_cost: non-negative float
        - category: optional category
        - material: optional material
        - quality: 'standard', 'high', 'premium'
        - demand: 'low', 'medium', 'high'
        - margin_multiplier: optional markup factor (default 1.35)

    Returns:
        - recommended: float
        - minimum: float
        - maximum: float
        - currency: "INR"
        - explanation: str
        - breakdown: PricingBreakdown
    """
    try:
        result = calculate_price_recommendation(
            raw_material_cost=payload.raw_material_cost,
            labour_cost=payload.labour_cost,
            packaging_cost=payload.packaging_cost,
            other_cost=payload.other_cost,
            category=payload.category,
            material=payload.material,
            quality=payload.quality,
            demand=payload.demand,
            margin_multiplier=payload.margin_multiplier,
        )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pricing recommendation service encountered an unexpected error: {exc}",
        )
