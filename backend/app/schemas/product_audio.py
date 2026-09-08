from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductAudioResponse(BaseModel):
    """Schema returned for product audio upload endpoints."""
    id: int
    product_id: int
    audio_url: str
    language: Optional[str] = "hi"
    duration: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductAudioItem(BaseModel):
    """Schema for nested audio items inside ProductResponse."""
    id: int
    audio_url: str
    language: Optional[str] = "hi"
    duration: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
