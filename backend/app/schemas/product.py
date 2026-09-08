from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from app.schemas.product_image import ProductImageItem


class ProductBase(BaseModel):
    """Base schema with shared product fields."""
    name: str = Field(..., description="Product name cannot be empty")
    description_en: Optional[str] = Field(default=None, description="English description")
    description_hi: Optional[str] = Field(default=None, description="Hindi description")
    category: Optional[str] = Field(default=None, description="Product category (e.g. Home Decor, Textiles)")
    material: Optional[str] = Field(default=None, description="Primary craft material (e.g. Bamboo, Clay)")
    raw_material_cost: float = Field(default=0.0, ge=0.0, description="Raw material cost (INR), non-negative")
    labour_cost: float = Field(default=0.0, ge=0.0, description="Labour cost (INR), non-negative")
    packaging_cost: float = Field(default=0.0, ge=0.0, description="Packaging cost (INR), non-negative")

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Product name cannot be empty or whitespace only")
        return cleaned


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating an existing product. All fields optional."""
    name: Optional[str] = Field(default=None, description="Updated product name")
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    raw_material_cost: Optional[float] = Field(default=None, ge=0.0)
    labour_cost: Optional[float] = Field(default=None, ge=0.0)
    packaging_cost: Optional[float] = Field(default=None, ge=0.0)
    status: Optional[str] = Field(default=None, description="Status: draft | uploaded | processing | processed | processing_failed")
    seo_title: Optional[str] = None
    seo_keywords: Optional[List[str]] = None

    @field_validator("name")
    @classmethod
    def validate_name_if_present(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Product name cannot be empty or whitespace only")
            return cleaned
        return v


class ProductPriceItem(BaseModel):
    """Schema for embedded pricing info in product responses."""
    id: int
    product_id: int
    recommended_price: float
    minimum_price: float
    maximum_price: float
    reason: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductAudioItem(BaseModel):
    """Schema for embedded audio items in product responses."""
    id: int
    audio_url: str
    language: Optional[str] = "hi"
    duration: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductResponse(BaseModel):
    """Schema returned by product endpoints, including AI data, images, audio, and pricing."""
    id: int
    user_id: Optional[int] = None
    name: str
    description_en: Optional[str] = None
    description_hi: Optional[str] = None
    category: Optional[str] = None
    material: Optional[str] = None
    raw_material_cost: float
    labour_cost: float
    packaging_cost: float
    status: str
    seo_title: Optional[str] = None
    seo_keywords: Optional[List[str]] = None
    voice_transcription: Optional[str] = None
    translated_voice_text: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    images: List[ProductImageItem] = Field(default_factory=list)
    audio_recordings: List[ProductAudioItem] = Field(default_factory=list)
    prices: List[ProductPriceItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
