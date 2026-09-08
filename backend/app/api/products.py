from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_audio import ProductAudio
from app.models.price import Price
from app.models.buyer import Buyer
from app.models.enquiry import Enquiry
from app.models.notification import Notification
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.schemas.product_image import ProductImageResponse
from app.schemas.product_audio import ProductAudioResponse
from app.schemas.ai import AIProcessRequest, ProductProcessPayload, ProductStatusResponse
from app.schemas.price import (
    PriceCreate,
    PriceResponse,
    ProductProcessResponse,
)
from app.schemas.buyer import ProductBuyerMatchResult
from app.schemas.enquiry import EnquiryResponse
from app.services.image_service import (
    upload_product_image,
    delete_product_image_from_storage,
)
from app.services.audio_service import upload_product_audio
from app.services.ai_service import ai_service
from app.services.pricing_service import pricing_service
from app.services.market_service import market_service
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)


def _get_user_product_or_404(product_id: int, user_id: int, db: Session) -> Product:
    """Helper to verify product existence and strict user ownership."""
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == user_id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


# ==========================================
# Product Core CRUD Endpoints (Protected)
# ==========================================


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product (Owned by current user)",
)
def create_product(
    payload: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new artisan product record securely assigned to the authenticated user."""
    product = Product(
        name=payload.name.strip(),
        description_en=payload.description_en,
        description_hi=payload.description_hi,
        category=payload.category,
        material=payload.material,
        raw_material_cost=payload.raw_material_cost,
        labour_cost=payload.labour_cost,
        packaging_cost=payload.packaging_cost,
        status="draft",
        user_id=current_user.id,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.get(
    "",
    response_model=List[ProductResponse],
    summary="List products owned by current user",
)
def list_products(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all catalog products owned by the authenticated artisan with pagination."""
    safe_limit = min(max(1, limit), 100)
    products = (
        db.query(Product)
        .filter(Product.user_id == current_user.id)
        .order_by(Product.id.desc())
        .offset(offset)
        .limit(safe_limit)
        .all()
    )
    return products


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID (Owner only)",
)
def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a single product by ID if owned by the authenticated user."""
    return _get_user_product_or_404(product_id, current_user.id, db)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product by ID (Owner only)",
)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update fields of an existing product owned by the authenticated user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return product

    if "name" in update_data and update_data["name"] is not None:
        cleaned_name = update_data["name"].strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Product name cannot be empty",
            )
        update_data["name"] = cleaned_name

    for field, value in update_data.items():
        if field == "status" and value is not None:
            valid_statuses = {"draft", "uploaded", "processing", "processed", "processing_failed", "published", "archived"}
            if value not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Invalid product status '{value}'. Must be one of: {', '.join(sorted(valid_statuses))}",
                )
            if value == "published" and product.status not in ("processed", "published"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only processed products can be published directly to the marketplace",
                )
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.post(
    "/{product_id}/publish",
    response_model=ProductResponse,
    summary="Publish a processed product directly to the marketplace (Owner only)",
)
def publish_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a product to the marketplace. Enforces that the product is processed."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    if product.status not in ("processed", "published"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only processed products can be published to the marketplace",
        )

    product.status = "published"
    db.commit()
    db.refresh(product)
    return product


@router.delete(
    "/{product_id}",
    summary="Delete product by ID (Owner only)",
)
def delete_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a product and its associated images from the user's catalog."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    for img in product.images:
        delete_product_image_from_storage(img.original_url)
        if img.processed_url:
            delete_product_image_from_storage(img.processed_url)

    # Ensure related notifications have product reference cleared
    db.query(Notification).filter(Notification.related_product_id == product.id).update({"related_product_id": None})

    db.delete(product)
    db.commit()
    return {
        "status": "success",
        "message": f"Product {product_id} deleted successfully",
    }


# ==========================================
# Product Image Endpoints (Owner only)
# ==========================================


@router.post(
    "/{product_id}/images",
    response_model=ProductImageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an image for a product (Owner only)",
)
async def upload_image(
    product_id: int,
    file: UploadFile = File(..., description="Product image file (JPEG, PNG, WebP, max 10MB)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a product photograph for a product owned by the current user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    image_url = await upload_product_image(file=file, product_id=product.id)

    product_image = ProductImage(
        product_id=product.id,
        original_url=image_url,
        processed_url=None,
    )
    db.add(product_image)

    # Advance status to 'uploaded' once image is stored
    if product.status == "draft":
        product.status = "uploaded"

    db.commit()
    db.refresh(product_image)
    return product_image


@router.get(
    "/{product_id}/images",
    response_model=List[ProductImageResponse],
    summary="Get all images for a product (Owner only)",
)
def get_product_images(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all image URLs for a product owned by the current user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)
    return product.images


@router.delete(
    "/{product_id}/images/{image_id}",
    summary="Delete a specific product image (Owner only)",
)
def delete_image(
    product_id: int,
    image_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a product image from the user's product and storage."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    image = (
        db.query(ProductImage)
        .filter(
            ProductImage.id == image_id,
            ProductImage.product_id == product.id,
        )
        .first()
    )
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found for this product",
        )

    delete_product_image_from_storage(image.original_url)
    if image.processed_url:
        delete_product_image_from_storage(image.processed_url)

    db.delete(image)
    db.commit()

    return {
        "status": "success",
        "message": f"Image {image_id} deleted successfully from product {product_id}",
    }


# ==========================================
# Product Audio Endpoints (Owner only)
# ==========================================


@router.post(
    "/{product_id}/audio",
    response_model=ProductAudioResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a voice recording for a product (Owner only)",
)
async def upload_audio(
    product_id: int,
    file: UploadFile = File(..., description="Voice recording (M4A/AAC/WAV/WebM/MP3, max 50MB)"),
    language: str = Form(default="hi", description="Artisan spoken language code (hi, mr, gu, ta, en)"),
    duration: Optional[float] = Form(default=None, description="Recording duration in seconds"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload a voice description for a product owned by the current user.

    Accepted formats: M4A/AAC (Flutter mobile default), WAV, MP3, WebM/Opus (Flutter web).
    """
    product = _get_user_product_or_404(product_id, current_user.id, db)

    audio_url = await upload_product_audio(file=file, product_id=product.id)

    audio_record = ProductAudio(
        product_id=product.id,
        audio_url=audio_url,
        language=language,
        duration=duration,
    )
    db.add(audio_record)
    db.commit()
    db.refresh(audio_record)

    return audio_record


@router.get(
    "/{product_id}/audio",
    response_model=List[ProductAudioResponse],
    summary="Get all audio recordings for a product (Owner only)",
)
def get_product_audio(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all voice recording metadata for a product owned by the current user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)
    return product.audio_recordings


# ==========================================
# Processing Status Endpoint (Owner only)
# ==========================================


@router.get(
    "/{product_id}/status",
    response_model=ProductStatusResponse,
    summary="Get processing status of a product (Owner only)",
)
def get_product_status(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current processing status of a product.
    Statuses: draft → uploaded → processing → processed | processing_failed
    """
    product = _get_user_product_or_404(product_id, current_user.id, db)
    return ProductStatusResponse(product_id=product.id, status=product.status)


# ==========================================
# Pricing Engine Endpoints (Owner only)
# ==========================================


@router.post(
    "/{product_id}/pricing",
    response_model=PriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Calculate and save price recommendation (Owner only)",
)
def create_pricing_recommendation(
    product_id: int,
    payload: Optional[PriceCreate] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate and record an explainable pricing recommendation for the user's product."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    if (
        product.raw_material_cost < 0
        or product.labour_cost < 0
        or product.packaging_cost < 0
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product contains invalid negative costs.",
        )

    calc = pricing_service.calculate_price(
        raw_material_cost=product.raw_material_cost,
        labour_cost=product.labour_cost,
        packaging_cost=product.packaging_cost,
        market_adjustment=payload.market_adjustment if payload else None,
        demand_adjustment=payload.demand_adjustment if payload else None,
        margin_percent=payload.get_margin_percent() if payload else None,
    )

    price_record = Price(
        product_id=product.id,
        recommended_price=calc["recommended_price"],
        minimum_price=calc["minimum_price"],
        maximum_price=calc["maximum_price"],
        reason=calc["reason"],
    )
    db.add(price_record)
    db.commit()
    db.refresh(price_record)

    return price_record


@router.get(
    "/{product_id}/pricing",
    response_model=PriceResponse,
    summary="Get current price recommendation (Owner only)",
)
def get_current_pricing(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve the most recent pricing recommendation for the user's product."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    latest_price = (
        db.query(Price)
        .filter(Price.product_id == product.id)
        .order_by(Price.created_at.desc(), Price.id.desc())
        .first()
    )
    if not latest_price:
        calc = pricing_service.calculate_price(
            raw_material_cost=product.raw_material_cost,
            labour_cost=product.labour_cost,
            packaging_cost=product.packaging_cost,
        )
        latest_price = Price(
            product_id=product.id,
            recommended_price=calc["recommended_price"],
            minimum_price=calc["minimum_price"],
            maximum_price=calc["maximum_price"],
            reason=calc["reason"],
        )
        db.add(latest_price)
        db.commit()
        db.refresh(latest_price)

    return latest_price


@router.get(
    "/{product_id}/pricing/history",
    response_model=List[PriceResponse],
    summary="Get pricing calculation history (Owner only)",
)
def get_pricing_history(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all historical pricing recommendations for the user's product."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    history = (
        db.query(Price)
        .filter(Price.product_id == product.id)
        .order_by(Price.created_at.desc(), Price.id.desc())
        .all()
    )
    return history


# ==========================================
# Product AI Processing Endpoint (Owner only)
# ==========================================


@router.post(
    "/{product_id}/process",
    response_model=ProductProcessResponse,
    summary="Process product with AI pipeline and pricing (Owner only)",
)
async def process_product_ai(
    product_id: int,
    payload: Optional[ProductProcessPayload] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Orchestrate the full AI processing pipeline for a product.

    Pipeline:
        1. Collect latest image URL and audio URL from the product record.
        2. Send to AI service (mock or Person 2's remote service).
        3. Save AI descriptions, SEO data, and voice transcriptions to the product.
        4. If AI returns a processed_image_url, persist it on the ProductImage record.
        5. Run PricingService and save the price recommendation.
        6. Return the combined product + pricing response.

    Audio is optional — if no audio recording exists, AI processes image only.
    """
    product = _get_user_product_or_404(product_id, current_user.id, db)

    # Prevent concurrent duplicate processing requests
    if product.status == "processing":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is currently being processed by the AI pipeline.",
        )

    # 1. Mark as processing
    product.status = "processing"
    db.commit()
    db.refresh(product)

    # 2. Gather latest image and audio URLs
    image_url = product.images[-1].original_url if product.images else None
    audio_url = None
    audio_language = payload.language if payload else "hi"
    if product.audio_recordings:
        latest_audio = product.audio_recordings[-1]
        audio_url = latest_audio.audio_url
        audio_language = latest_audio.language or audio_language

    # 3. Build AI request — audio_url is optional
    ai_request = AIProcessRequest(
        product_id=product.id,
        image_url=image_url,
        audio_url=audio_url,
        voice_text=payload.voice_text if payload else None,
        language=audio_language,
        raw_material_cost=product.raw_material_cost,
        labour_cost=product.labour_cost,
        packaging_cost=product.packaging_cost,
    )

    # 4. Invoke AI Service
    try:
        ai_result = await ai_service.process_product(ai_request)
    except Exception as exc:
        product.status = "processing_failed"
        db.commit()
        raise exc

    # 5. Update product with AI output
    product.name = ai_result.product_name
    product.description_en = ai_result.description_en
    product.description_hi = ai_result.description_hi
    product.category = ai_result.category
    product.material = ai_result.material
    product.seo_title = ai_result.seo_title
    product.seo_keywords = ai_result.seo_keywords

    # 6. Store voice transcription if AI returned them
    if ai_result.transcription:
        product.voice_transcription = ai_result.transcription
    if ai_result.translated_text:
        product.translated_voice_text = ai_result.translated_text

    product.status = "processed"

    # 7. If AI returned a processed image URL, save it on the latest ProductImage
    if ai_result.processed_image_url and product.images:
        latest_image = product.images[-1]
        latest_image.processed_url = ai_result.processed_image_url

    # 8. Calculate & persist pricing recommendation
    calc = pricing_service.calculate_price(
        raw_material_cost=product.raw_material_cost,
        labour_cost=product.labour_cost,
        packaging_cost=product.packaging_cost,
    )
    price_record = Price(
        product_id=product.id,
        recommended_price=calc["recommended_price"],
        minimum_price=calc["minimum_price"],
        maximum_price=calc["maximum_price"],
        reason=calc["reason"],
    )
    db.add(price_record)

    db.commit()
    db.refresh(product)
    db.refresh(price_record)

    return {
        "product": product,
        "pricing": price_record,
    }


# ==========================================
# Buyer Discovery & Enquiries (Owner only)
# ==========================================


@router.get(
    "/{product_id}/buyers",
    response_model=ProductBuyerMatchResult,
    summary="Find matching B2B wholesale buyers for a product (Owner only)",
)
def get_matching_buyers_for_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Rank prospective B2B wholesale buyers for a product owned by the current user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    all_buyers = db.query(Buyer).all()
    matched_buyers = market_service.find_matching_buyers(product=product, buyers=all_buyers)

    return ProductBuyerMatchResult(
        product_id=product.id,
        buyers=matched_buyers,
    )


@router.get(
    "/{product_id}/enquiries",
    response_model=List[EnquiryResponse],
    summary="Get all B2B enquiries for a product (Owner only)",
)
def get_product_enquiries(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all B2B enquiries associated with a product owned by the authenticated user."""
    product = _get_user_product_or_404(product_id, current_user.id, db)

    enquiries = (
        db.query(Enquiry)
        .filter(Enquiry.product_id == product.id)
        .order_by(Enquiry.created_at.desc())
        .all()
    )

    return [
        EnquiryResponse(
            id=e.id,
            buyer_id=e.buyer_id,
            product_id=e.product_id,
            message=e.message,
            status=e.status,
            artisan_response=e.artisan_response,
            buyer_company=e.buyer.company if e.buyer else None,
            product_name=product.name,
            created_at=e.created_at,
            updated_at=e.updated_at,
            responded_at=e.responded_at,
        )
        for e in enquiries
    ]
