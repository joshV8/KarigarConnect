from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.database import get_db
from app.models.user import User
from app.models.enquiry import Enquiry
from app.models.product import Product
from app.schemas.enquiry import EnquiryResponse, EnquiryUpdate, FeasibilityRequest
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/enquiries",
    tags=["Buyer Enquiries"],
)


def _get_user_enquiry_or_404(enquiry_id: int, user_id: int, db: Session) -> Enquiry:
    """Helper to verify that an enquiry exists AND is associated with a product owned by the artisan."""
    enquiry = (
        db.query(Enquiry)
        .join(Product, Enquiry.product_id == Product.id)
        .filter(Enquiry.id == enquiry_id, Product.user_id == user_id)
        .first()
    )
    if not enquiry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Enquiry not found",
        )
    return enquiry


def _build_enquiry_response(enquiry: Enquiry) -> EnquiryResponse:
    """Helper to transform an Enquiry SQLAlchemy model into a rich EnquiryResponse."""
    return EnquiryResponse(
        id=enquiry.id,
        buyer_id=enquiry.buyer_id,
        product_id=enquiry.product_id,
        message=enquiry.message,
        status=enquiry.status,
        artisan_response=enquiry.artisan_response,
        buyer_company=enquiry.buyer.company if enquiry.buyer else None,
        product_name=enquiry.product.name if enquiry.product else None,
        created_at=enquiry.created_at,
        updated_at=enquiry.updated_at,
        responded_at=enquiry.responded_at,
    )


@router.get(
    "",
    response_model=List[EnquiryResponse],
    summary="List all B2B enquiries for the authenticated artisan",
)
def list_enquiries(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status: pending, contacted, accepted, rejected"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all B2B enquiries for products owned by the authenticated artisan."""
    query = (
        db.query(Enquiry)
        .join(Product, Enquiry.product_id == Product.id)
        .filter(Product.user_id == current_user.id)
    )

    if status_filter:
        query = query.filter(Enquiry.status == status_filter.lower().strip())

    enquiries = (
        query.order_by(Enquiry.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return [_build_enquiry_response(e) for e in enquiries]


@router.get(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
    summary="Get details of a specific B2B enquiry (Owner only)",
)
def get_enquiry(
    enquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve details, message, and current status of an enquiry for an artisan's product."""
    enquiry = _get_user_enquiry_or_404(enquiry_id, current_user.id, db)
    return _build_enquiry_response(enquiry)


@router.put(
    "/{enquiry_id}",
    response_model=EnquiryResponse,
    summary="Update enquiry status and supply artisan response (Owner only)",
)
def update_enquiry(
    enquiry_id: int,
    payload: EnquiryUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update enquiry status (pending -> contacted -> accepted / rejected) and record official artisan response."""
    enquiry = _get_user_enquiry_or_404(enquiry_id, current_user.id, db)

    if payload.status is not None:
        enquiry.status = payload.status

    if payload.artisan_response is not None:
        enquiry.artisan_response = payload.artisan_response
        enquiry.responded_at = func.now()

    db.commit()
    db.refresh(enquiry)
    return _build_enquiry_response(enquiry)


@router.post(
    "/{enquiry_id}/analyze",
    summary="Analyze a B2B buyer offer using AI",
)
async def analyze_enquiry_offer(
    enquiry_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates the buyer's enquiry (offer price, quantity, lead time) against the artisan's floor price 
    (material + labour costs) and production capacity. Returns a summary and suggested counter-offers.
    """
    enquiry = _get_user_enquiry_or_404(enquiry_id, current_user.id, db)
    
    from app.services.ai_service import ai_service
    
    analysis = await ai_service.analyze_negotiation(
        enquiry_message=enquiry.message,
        material_cost=enquiry.product.raw_material_cost,
        labour_cost=enquiry.product.labour_cost,
    )
    return analysis


@router.post(
    "/{enquiry_id}/feasibility",
    summary="AI Order Feasibility Engine — checks if the artisan can fulfill a B2B order",
)
async def check_order_feasibility(
    enquiry_id: int,
    payload: FeasibilityRequest = Body(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Evaluates whether the artisan can fulfill the buyer's order quantity within the
    requested deadline given:
      - Current inventory
      - Monthly production capacity
      - Number of workers
      - Raw material availability %

    Returns a full feasibility report with a breakdown table and a ready-to-send
    recommended response (optionally polished by Gemini AI).
    """
    enquiry = _get_user_enquiry_or_404(enquiry_id, current_user.id, db)

    from app.services.feasibility_service import calculate_feasibility_with_ai

    product_name = enquiry.product.name if enquiry.product else "artisan product"

    result = calculate_feasibility_with_ai(
        enquiry_message=enquiry.message,
        current_inventory=payload.current_inventory,
        monthly_capacity=payload.monthly_capacity,
        num_workers=payload.num_workers,
        raw_material_availability_pct=payload.raw_material_availability_pct,
        product_name=product_name,
    )
    return result
