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
