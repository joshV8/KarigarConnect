from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.product_image import ProductImageItem


class CatalogProductItem(BaseModel):
    """Schema for a product displayed inside a digital catalog."""
    id: int
    name: str
    category: Optional[str] = None
    material: Optional[str] = None
    recommended_price: Optional[float] = None
    status: str
    images: List[ProductImageItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class CatalogCreate(BaseModel):
    """Payload to create a new digital catalog collection."""
    title: str = Field(..., min_length=1, description="Title of the collection/catalog")
    description: Optional[str] = Field(default=None, description="Overview of the artisan collection")


class CatalogUpdate(BaseModel):
    """Payload to update an existing catalog."""
    title: Optional[str] = Field(default=None, min_length=1)
    description: Optional[str] = None
    status: Optional[str] = Field(default=None, description="draft | published | archived")


class CatalogResponse(BaseModel):
    """Schema returned for digital catalog queries."""
    id: int
    user_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    status: str = "draft"
    products: List[CatalogProductItem] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
