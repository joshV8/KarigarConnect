"""
Product models — Gate 5: Product Vision / Attribute Extraction.

Defines the Pydantic schema for structured product attributes extracted
from product images by multimodal vision LLMs, per 05_GATE_PRODUCT_VISION.md.
"""

from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


class ProductVisionResult(BaseModel):
    """
    Structured attributes extracted from an artisan product photograph.

    Per 05_GATE_PRODUCT_VISION.md:
    Only report attributes supported by the image.
    If an attribute cannot be determined, use null.
    Do not invent dimensions, certifications, origin, material, or features.
    """
    product_name: Optional[str] = Field(
        default=None,
        description="Identified or suggested title for the artisan product."
    )
    category: Optional[str] = Field(
        default=None,
        description="Broad product category, e.g. Handicrafts, Textiles, Pottery."
    )
    material: Optional[str] = Field(
        default=None,
        description="Primary material visible, e.g. Bamboo, Clay, Silk, Brass."
    )
    color: Optional[str] = Field(
        default=None,
        description="Dominant color(s) of the product."
    )
    craft_type: Optional[str] = Field(
        default=None,
        description="Specific craft or artisan technique, e.g. Handwoven, Terracotta, Woodcarving."
    )
    style: Optional[str] = Field(
        default=None,
        description="Aesthetic style, e.g. Traditional, Rustic, Contemporary, Folk."
    )
    visible_features: List[str] = Field(
        default_factory=list,
        description="List of specific visible design elements, textures, or components."
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0."
    )

    @field_validator("visible_features", mode="before")
    @classmethod
    def coerce_visible_features(cls, v: Any) -> List[str]:
        """
        Coerce visible_features to a list.

        Gemini (and other LLMs) occasionally returns a comma-separated
        string instead of a JSON array. We split on commas and strip
        whitespace so the model validates cleanly regardless.
        """
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item) for item in v if item is not None]
        if isinstance(v, str):
            return [item.strip() for item in v.split(",") if item.strip()]
        return []

    @field_validator("confidence", mode="before")
    @classmethod
    def parse_confidence(cls, v: Any) -> Optional[float]:
        """Allow robust parsing of float or descriptive strings from LLMs."""
        if v is None:
            return None
        if isinstance(v, (int, float)):
            val = float(v)
            return max(0.0, min(1.0, val))
        if isinstance(v, str):
            cleaned = v.strip().lower()
            if cleaned in ("high", "very high"):
                return 0.9
            elif cleaned in ("medium", "moderate"):
                return 0.7
            elif cleaned in ("low", "very low"):
                return 0.4
            try:
                val = float(cleaned)
                return max(0.0, min(1.0, val))
            except ValueError:
                return 0.8
        return None
