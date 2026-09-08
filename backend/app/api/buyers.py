from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.buyer import Buyer
from app.models.product import Product
from app.models.enquiry import Enquiry
from app.schemas.buyer import BuyerResponse
from app.schemas.enquiry import EnquiryCreate, EnquiryResponse
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/buyers",
    tags=["Buyers & Market Linkage"],
)


@router.get(
    "",
    response_model=List[BuyerResponse],
    summary="List B2B wholesale buyers (Public)",
)
def list_buyers(
    category: Optional[str] = Query(default=None, description="Filter by category (e.g. Home Decor, Textiles)"),
    location: Optional[str] = Query(default=None, description="Filter by location (e.g. Mumbai, Delhi)"),
    db: Session = Depends(get_db),
):
    """Retrieve all verified B2B buyers with optional category and location filtering."""
    query = db.query(Buyer)

    if category:
        query = query.filter(Buyer.category.ilike(f"%{category.strip()}%"))
    if location:
        query = query.filter(Buyer.location.ilike(f"%{location.strip()}%"))

    buyers = query.order_by(Buyer.id.asc()).all()
    return buyers


@router.get(
    "/{buyer_id}",
    response_model=BuyerResponse,
    summary="Get buyer details by ID (Public)",
)
def get_buyer(
    buyer_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve profile and procurement criteria for a specific B2B buyer."""
    buyer = db.query(Buyer).filter(Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found",
        )
    return buyer


@router.post(
    "/{buyer_id}/enquiries",
    response_model=EnquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send an enquiry to a B2B buyer (Owner only)",
)
def send_enquiry_to_buyer(
    buyer_id: int,
    payload: EnquiryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a purchase proposition / wholesale enquiry for an artisan product owned by current user."""
    # 1. Validate Buyer exists
    buyer = db.query(Buyer).filter(Buyer.id == buyer_id).first()
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found",
        )

    # 2. Validate Product exists AND belongs to authenticated artisan
    product = (
        db.query(Product)
        .filter(Product.id == payload.product_id, Product.user_id == current_user.id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or not owned by authenticated user",
        )

    # 3. Validate message content
    cleaned_message = payload.message.strip()
    if not cleaned_message:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Enquiry message cannot be empty",
        )

    # 4. Create enquiry record
    enquiry = Enquiry(
        buyer_id=buyer.id,
        product_id=product.id,
        message=cleaned_message,
        status="pending",
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    # 5. Automatically create in-app notification for the product owner
    try:
        from app.services.notification_service import notification_service
        buyer_name = buyer.company or buyer.name or "A verified wholesale buyer"
        notification_service.create_notification(
            db=db,
            user_id=product.user_id,
            type="new_enquiry",
            title="New Buyer Enquiry",
            message=f"{buyer_name} is interested in your product '{product.name}'.",
            related_product_id=product.id,
            related_enquiry_id=enquiry.id,
        )
    except Exception:
        # Non-blocking notification creation
        pass

    return EnquiryResponse(
        id=enquiry.id,
        buyer_id=enquiry.buyer_id,
        product_id=enquiry.product_id,
        message=enquiry.message,
        status=enquiry.status,
        artisan_response=enquiry.artisan_response,
        buyer_company=buyer.company,
        product_name=product.name,
        created_at=enquiry.created_at,
        updated_at=enquiry.updated_at,
        responded_at=enquiry.responded_at,
    )
