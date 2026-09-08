from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from app.schemas.product import ProductResponse


class PriceCreate(BaseModel):
    """Optional adjustments when manually triggering a price calculation."""
    market_adjustment: Optional[float] = Field(default=None, description="Market premium or discount in INR")
    demand_adjustment: Optional[float] = Field(default=None, description="Demand factor adjustment in INR")
    custom_margin_percent: Optional[float] = Field(default=None, ge=0.0, description="Override artisan profit margin %")
    margin_percent: Optional[float] = Field(default=None, ge=0.0, description="Alias for custom_margin_percent")

    def get_margin_percent(self) -> Optional[float]:
        """Return custom_margin_percent or margin_percent if supplied."""
        if self.custom_margin_percent is not None:
            return self.custom_margin_percent
        return self.margin_percent


class PriceResponse(BaseModel):
    """Schema for pricing calculation and history records."""
    id: int
    product_id: int
    recommended_price: float
    minimum_price: float
    maximum_price: float
    reason: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductProcessResponse(BaseModel):
    """Response returned by /products/{product_id}/process combining AI enhancements and pricing recommendation."""
    product: ProductResponse
    pricing: Optional[PriceResponse] = None

    model_config = ConfigDict(from_attributes=True)
