from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class BuyerCreate(BaseModel):
    """Schema for adding demo/wholesale buyers."""
    name: str = Field(..., min_length=1, description="Contact person or manager")
    company: str = Field(..., min_length=1, description="Company / Wholesale Business Name")
    email: Optional[str] = Field(default=None, description="Business email")
    phone: Optional[str] = Field(default=None, description="Contact phone")
    location: str = Field(..., description="City or Regional hub (e.g. Mumbai, Delhi, Jaipur)")
    category: str = Field(..., description="Target merchandise category (e.g. Home Decor, Textiles, Pottery)")
    description: Optional[str] = Field(default=None, description="Procurement requirements / specialization")


class BuyerResponse(BaseModel):
    """Schema returned for B2B buyer information."""
    id: int
    name: str
    company: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: str
    category: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class BuyerMatchResponse(BaseModel):
    """Schema for a B2B buyer matched with a specific artisan product."""
    id: int
    name: str
    company: str
    category: str
    location: str
    description: Optional[str] = None
    match_score: int = Field(..., description="Calculated matching relevance score (0-100)")
    match_reasons: List[str] = Field(default_factory=list, description="Specific alignment signals")

    model_config = ConfigDict(from_attributes=True)


class ProductBuyerMatchResult(BaseModel):
    """Result returned by /products/{product_id}/buyers endpoint."""
    product_id: int
    buyers: List[BuyerMatchResponse] = Field(default_factory=list)
