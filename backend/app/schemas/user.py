from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    """Schema returned for authenticated user profile information."""
    id: int
    firebase_uid: str
    name: Optional[str] = None
    phone: Optional[str] = None
    language: str = "hi"
    location: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """Schema for updating an artisan's profile."""
    name: Optional[str] = None
    language: Optional[str] = None
    location: Optional[str] = None
