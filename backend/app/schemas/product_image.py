from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class ProductImageResponse(BaseModel):
    """Schema returned for product image endpoints."""
    id: int
    product_id: int
    original_url: str
    processed_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductImageItem(BaseModel):
    """Schema for nested image items inside ProductResponse."""
    id: int
    original_url: str
    processed_url: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
