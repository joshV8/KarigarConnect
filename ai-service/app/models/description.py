"""
Product description models — Gate 8: AI Product Description.

Defines schemas for requesting and receiving structured marketplace product
descriptions generated strictly from verified attributes and artisan inputs.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from app.models.product import ProductVisionResult


class DescriptionRequest(BaseModel):
    """
    Input payload for generating an artisan product description.

    Accepts verified visual attributes (Gate 5) and/or transcribed/translated
    artisan voice notes (Gate 6/7).
    """
    model_config = {"extra": "allow"}

    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured product attributes (e.g. from ProductVisionResult or manual inputs).",
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Optional top-level product name.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Optional top-level product category.",
    )
    material: Optional[str] = Field(
        default=None,
        description="Optional top-level product material.",
    )
    transcription: Optional[str] = Field(
        default=None,
        description="Artisan voice input transcription or translation text.",
    )
    artisan_notes: Optional[str] = Field(
        default=None,
        description="Optional artisan commentary, story, or technique notes.",
    )
    language: Optional[str] = Field(
        default="en",
        description="Target language for output descriptions (e.g. 'en', 'hi'). Default is 'en'.",
    )


class ProductDescriptionResult(BaseModel):
    """
    Marketplace-ready product description response.

    Per 08_GATE_AI_DESCRIPTION.md:
    - title
    - short_description
    - description
    - features
    - materials
    """
    title: str = Field(
        ...,
        description="Clear, descriptive, marketplace-ready product title.",
    )
    short_description: str = Field(
        ...,
        description="Concise 1-2 sentence overview for catalog cards.",
    )
    description: str = Field(
        ...,
        description="Full, rich product description highlighting craftsmanship and authenticity.",
    )
    features: List[str] = Field(
        default_factory=list,
        description="Bullet points of verified product features and handmade techniques.",
    )
    materials: List[str] = Field(
        default_factory=list,
        description="List of materials used in creating the product.",
    )

    @field_validator("features", "materials", mode="before")
    @classmethod
    def coerce_to_string_list(cls, v: Any) -> List[str]:
        """Coerce strings or None into list of clean strings."""
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if item is not None and str(item).strip()]
        if isinstance(v, str):
            return [part.strip() for part in v.split(",") if part.strip()]
        return []
