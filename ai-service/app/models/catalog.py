"""
Catalog models — Gate 11: Catalog Orchestration.

Defines schemas for unifying image processing, product vision, voice transcription,
translation, product description, SEO metadata, and pricing into a complete marketplace listing.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CatalogProductInfo(BaseModel):
    """Basic product attributes."""
    name: str = Field(..., description="Product name/title.")
    category: str = Field(..., description="Product category.")
    material: str = Field(..., description="Primary material.")


class CatalogImages(BaseModel):
    """Image links or data URIs for original and processed photos."""
    original: str = Field(..., description="Original uploaded image link or data URI.")
    processed: str = Field(..., description="Background-removed, enhanced image link or data URI.")


class CatalogDescriptions(BaseModel):
    """Multilingual product descriptions."""
    english: str = Field(..., description="Product description in English.")
    hindi: str = Field(..., description="Product description in Hindi.")
    original: Optional[str] = Field(None, description="Original language text or transcription if provided.")


class CatalogSEO(BaseModel):
    """Search engine metadata."""
    title: str = Field(..., description="SEO title.")
    keywords: List[str] = Field(default_factory=list, description="Relevant search keywords.")


class CatalogPricing(BaseModel):
    """Price recommendation details."""
    recommended: float = Field(..., description="Recommended listing price in INR.")
    minimum: float = Field(..., description="Minimum price covering production and basic margin.")
    maximum: float = Field(..., description="Maximum market price ceiling.")
    currency: str = Field(default="INR", description="Currency code.")
    explanation: str = Field(..., description="Transparent calculation explanation.")


class CatalogResult(BaseModel):
    """
    Complete consolidated marketplace product catalog entry.

    Per 11_GATE_CATALOG_ORCHESTRATION.md:
    - product: { name, category, material }
    - images: { original, processed }
    - description: { english, hindi, original }
    - seo: { title, keywords }
    - pricing: { recommended, minimum, maximum, currency, explanation }
    """
    product: CatalogProductInfo
    images: CatalogImages
    description: CatalogDescriptions
    seo: CatalogSEO
    pricing: CatalogPricing
