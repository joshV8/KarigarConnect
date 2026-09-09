from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

ALLOWED_ENQUIRY_STATUSES = {"pending", "contacted", "accepted", "rejected"}


class EnquiryCreate(BaseModel):
    """Payload to send an enquiry from an artisan for a product to a buyer."""
    product_id: int = Field(..., description="ID of the artisan product being presented")
    message: str = Field(..., description="Message / purchase proposition to the buyer")

    @field_validator("message")
    @classmethod
    def validate_message_not_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Enquiry message cannot be empty or whitespace only")
        return cleaned


class EnquiryUpdate(BaseModel):
    """Payload for an artisan to update the enquiry status and supply an official response."""
    status: Optional[str] = Field(
        default=None,
        description="Status transition: pending | contacted | accepted | rejected",
    )
    artisan_response: Optional[str] = Field(
        default=None,
        description="Artisan's reply message or negotiation terms to the buyer",
    )

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.lower().strip()
            if cleaned not in ALLOWED_ENQUIRY_STATUSES:
                raise ValueError(
                    f"Invalid status '{v}'. Allowed statuses: {', '.join(sorted(ALLOWED_ENQUIRY_STATUSES))}"
                )
            return cleaned
        return v

    @field_validator("artisan_response")
    @classmethod
    def validate_artisan_response(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip()
            if not cleaned:
                raise ValueError("Artisan response cannot be empty or whitespace only")
            return cleaned
        return v


class EnquiryResponse(BaseModel):
    """Schema returned for B2B enquiry records."""
    id: int
    buyer_id: int
    product_id: int
    message: str
    status: str
    artisan_response: Optional[str] = None
    buyer_company: Optional[str] = None
    product_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class NegotiationAnalysisResponse(BaseModel):
    """Schema for AI evaluation of a buyer's enquiry."""
    is_sustainable: bool = Field(..., description="True if the offer meets or exceeds the artisan's floor price/capacity")
    evaluation_summary: str = Field(..., description="Short explanation of why the deal is good or bad")
    proposed_counter_offers: list[str] = Field(..., description="List of 2-3 actionable counter offers to send to the buyer")

    model_config = ConfigDict(from_attributes=True)


class FeasibilityRequest(BaseModel):
    """Artisan's current production capacity inputs for feasibility check."""
    current_inventory: int = Field(0, description="Units currently in stock", ge=0)
    monthly_capacity: int = Field(100, description="Max units artisan can produce per month", ge=1)
    num_workers: int = Field(1, description="Number of workers available", ge=1)
    raw_material_availability_pct: float = Field(100.0, description="% of raw material available (0-100)", ge=0, le=100)


class FeasibilityBreakdown(BaseModel):
    """Step-by-step production breakdown."""
    required_units: int
    inventory_available: int
    units_to_produce: int
    production_rate_per_day: float
    estimated_days: float
    raw_material_adjusted_rate: float
    can_fulfill: bool


class FeasibilityResponse(BaseModel):
    """AI Order Feasibility Engine full report."""
    can_fulfill_on_time: bool
    status_emoji: str  # ✅ or ❌
    status_label: str
    summary: str
    breakdown: FeasibilityBreakdown
    recommended_response: str
    split_delivery_suggestion: Optional[str] = None
