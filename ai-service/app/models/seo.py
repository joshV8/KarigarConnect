"""
SEO catalog models — Gate 9: SEO Catalog Content.

Defines schemas for requesting and generating marketplace SEO metadata,
per 09_GATE_SEO_CATALOG.md.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class SEORequest(BaseModel):
    """
    Input payload for generating marketplace SEO metadata.

    Accepts product title, description, attributes, or transcription cues.
    """
    title: Optional[str] = Field(
        default=None,
        description="Product title from Gate 8 or catalog.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Product description or short description from Gate 8.",
    )
    attributes: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Product attributes (e.g. material, craft_type, category).",
    )
    transcription: Optional[str] = Field(
        default=None,
        description="Artisan voice transcription or notes.",
    )
    category: Optional[str] = Field(
        default=None,
        description="Product category, e.g. Handicrafts, Pottery, Textiles.",
    )


class SEOResult(BaseModel):
    """
    Marketplace SEO metadata response.

    Per 09_GATE_SEO_CATALOG.md:
    - seo_title
    - meta_description
    - keywords
    """
    seo_title: str = Field(
        ...,
        description="Searchable, market-ready title (e.g. 'Handwoven Bamboo Basket | Handmade Indian Handicraft').",
    )
    meta_description: str = Field(
        ...,
        description="Search-optimized summary snippet for search engine listing.",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="List of directly relevant search keywords. No unrelated trending keywords.",
    )

    @field_validator("keywords", mode="before")
    @classmethod
    def coerce_keywords(cls, v: Any) -> List[str]:
        """Coerce comma-separated string or list to clean string list."""
        if v is None:
            return []
        if isinstance(v, list):
            return [str(item).strip() for item in v if item is not None and str(item).strip()]
        if isinstance(v, str):
            return [part.strip() for part in v.split(",") if part.strip()]
        return []
