from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class AIProcessRequest(BaseModel):
    """Payload sent from FastAPI backend to Person 2's AI service."""
    product_id: int = Field(..., description="Unique product ID in catalog")
    image_url: Optional[str] = Field(default=None, description="Cloudinary/storage image URL")
    audio_url: Optional[str] = Field(default=None, description="Cloudinary/storage audio URL for STT")
    voice_text: Optional[str] = Field(default=None, description="Pre-transcribed voice text (if available)")
    language: Optional[str] = Field(default="hi", description="Artisan spoken language code (hi, mr, gu, ta, en)")
    raw_material_cost: Optional[float] = Field(default=0.0, description="Raw material cost in INR")
    labour_cost: Optional[float] = Field(default=0.0, description="Labour cost in INR")
    packaging_cost: Optional[float] = Field(default=0.0, description="Packaging cost in INR")


class AIProcessResponse(BaseModel):
    """Structured response validated from Person 2's AI service."""
    product_name: str = Field(..., min_length=1, description="AI generated/enhanced product title")
    description_en: str = Field(..., description="High quality English product description")
    description_hi: str = Field(..., description="High quality Hindi product description")
    category: str = Field(..., description="Marketplace category (e.g. Home Decor, Textiles, Pottery)")
    material: str = Field(..., description="Primary craft material (e.g. Bamboo, Brass, Terracotta)")
    seo_title: Optional[str] = Field(default=None, description="Search-optimized title for e-commerce")
    seo_keywords: Optional[List[str]] = Field(default=None, description="List of search tags and keywords")
    # Audio transcription fields — optional, populated when audio_url is provided
    transcription: Optional[str] = Field(default=None, description="STT output in artisan's regional language")
    translated_text: Optional[str] = Field(default=None, description="English translation of transcription")
    # Optional processed/enhanced image from AI pipeline
    processed_image_url: Optional[str] = Field(default=None, description="AI-enhanced image URL (Person 2 pipeline)")

    model_config = ConfigDict(from_attributes=True)


class ProductProcessPayload(BaseModel):
    """Optional payload supplied when triggering /products/{product_id}/process."""
    voice_text: Optional[str] = Field(default=None, description="Optional transcribed speech / artisan voice note")
    language: Optional[str] = Field(default="hi", description="Artisan input language code (hi, mr, gu, ta, etc.)")


class ProductStatusResponse(BaseModel):
    """Response for GET /products/{product_id}/status."""
    product_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
