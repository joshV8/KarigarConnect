"""
Pricing models — Gate 10: Pricing Recommendation.

Defines schemas for requesting and receiving transparent, deterministic
pricing recommendations for artisan handicraft products.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PricingRequest(BaseModel):
    """
    Input payload for requesting an artisan price recommendation.

    Per 10_GATE_PRICING_ENGINE.md:
    - raw_material_cost
    - labour_cost
    - packaging_cost
    - other_cost
    - category
    - material
    - quality
    - demand
    """
    raw_material_cost: float = Field(
        ...,
        ge=0.0,
        description="Cost of raw materials in INR (e.g. bamboo, clay, dyes).",
    )
    labour_cost: float = Field(
        ...,
        ge=0.0,
        description="Estimated artisan labour/time cost in INR.",
    )
    packaging_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Cost of protective or display packaging in INR.",
    )
    other_cost: float = Field(
        default=0.0,
        ge=0.0,
        description="Miscellaneous overhead, electricity, transport costs in INR.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Product category, e.g. 'Handicrafts', 'Pottery', 'Textiles'.",
    )
    material: Optional[str] = Field(
        default=None,
        description="Primary material, e.g. 'Bamboo', 'Terracotta', 'Silk', 'Brass'.",
    )
    quality: Optional[str] = Field(
        default="standard",
        description="Artisan craftsmanship quality level: 'standard', 'high', or 'premium'.",
    )
    demand: Optional[str] = Field(
        default="medium",
        description="Current market demand level: 'low', 'medium', or 'high'.",
    )
    margin_multiplier: Optional[float] = Field(
        default=1.35,
        ge=1.0,
        le=3.0,
        description="Configurable profit margin multiplier (default 1.35 = 35% margin).",
    )


class PricingBreakdown(BaseModel):
    """Detailed breakdown of costs and adjustments."""
    raw_material_cost: float
    labour_cost: float
    packaging_cost: float
    other_cost: float
    production_cost: float
    base_price: float
    quality_adjustment: float
    demand_adjustment: float


class PricingResult(BaseModel):
    """
    Price recommendation output.

    Per 10_GATE_PRICING_ENGINE.md:
    - recommended
    - minimum
    - maximum
    - currency
    - explanation
    """
    recommended: float = Field(
        ...,
        description="Recommended listing price in specified currency.",
    )
    minimum: float = Field(
        ...,
        description="Minimum viable price ensuring production costs and basic artisan margin are covered.",
    )
    maximum: float = Field(
        ...,
        description="Maximum suggested price ceiling according to market benchmarks.",
    )
    currency: str = Field(
        default="INR",
        description="Currency code (e.g. 'INR').",
    )
    explanation: str = Field(
        ...,
        description="Transparent, clear breakdown explaining production cost, adjustments, and market range.",
    )
    breakdown: Optional[PricingBreakdown] = Field(
        default=None,
        description="Detailed numeric cost breakdown.",
    )
