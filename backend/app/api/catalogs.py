from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.catalog import Catalog
from app.models.product import Product
from app.schemas.catalog import (
    CatalogCreate,
    CatalogUpdate,
    CatalogResponse,
    CatalogProductItem,
)
from app.schemas.product_image import ProductImageItem
from app.api.dependencies import get_current_user

router = APIRouter(
    prefix="/catalogs",
    tags=["Catalogs"],
)


def _build_catalog_response(catalog: Catalog) -> CatalogResponse:
    """Helper to transform a Catalog SQLAlchemy model into a rich CatalogResponse."""
    product_items = []
    for p in catalog.products:
        rec_price = p.prices[0].recommended_price if p.prices else None
        product_items.append(
            CatalogProductItem(
                id=p.id,
                name=p.name,
                category=p.category,
                material=p.material,
                recommended_price=rec_price,
                status=p.status,
                images=[ProductImageItem.model_validate(img) for img in p.images],
            )
        )

    return CatalogResponse(
        id=catalog.id,
        user_id=catalog.user_id,
        title=catalog.title,
        description=catalog.description,
        status=catalog.status,
        products=product_items,
        created_at=catalog.created_at,
        updated_at=catalog.updated_at,
    )


def _get_user_catalog_or_404(catalog_id: int, user_id: int, db: Session) -> Catalog:
    """Helper to verify catalog existence and user ownership."""
    catalog = (
        db.query(Catalog)
        .filter(Catalog.id == catalog_id, Catalog.user_id == user_id)
        .first()
    )
    if not catalog:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Catalog not found",
        )
    return catalog


@router.post(
    "",
    response_model=CatalogResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new digital catalog (Owner only)",
)
def create_catalog(
    payload: CatalogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new digital collection/catalog owned by the authenticated user."""
    catalog = Catalog(
        title=payload.title.strip(),
        description=payload.description,
        user_id=current_user.id,
        status="draft",
    )
    db.add(catalog)
    db.commit()
    db.refresh(catalog)
    return _build_catalog_response(catalog)


@router.get(
    "",
    response_model=List[CatalogResponse],
    summary="List digital catalogs owned by current user",
)
def list_catalogs(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve all digital catalogs created by the authenticated user with pagination."""
    safe_limit = min(max(1, limit), 100)
    catalogs = (
        db.query(Catalog)
        .filter(Catalog.user_id == current_user.id)
        .order_by(Catalog.id.desc())
        .offset(offset)
        .limit(safe_limit)
        .all()
    )
    return [_build_catalog_response(c) for c in catalogs]


@router.get(
    "/{catalog_id}",
    response_model=CatalogResponse,
    summary="Get a catalog by ID (Owner only)",
)
def get_catalog(
    catalog_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a single catalog and its included products if owned by current user."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)
    return _build_catalog_response(catalog)


@router.put(
    "/{catalog_id}",
    response_model=CatalogResponse,
    summary="Update catalog details (Owner only)",
)
def update_catalog(
    catalog_id: int,
    payload: CatalogUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update title, description, or status of an existing digital catalog."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)

    if payload.title is not None:
        cleaned_title = payload.title.strip()
        if not cleaned_title:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Catalog title cannot be empty",
            )
        catalog.title = cleaned_title

    if payload.description is not None:
        catalog.description = payload.description

    if payload.status is not None:
        valid_statuses = {"draft", "published", "archived"}
        if payload.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid catalog status '{payload.status}'. Must be one of: {', '.join(sorted(valid_statuses))}",
            )
        if payload.status == "published":
            # Publishing integrity rule: must contain at least 1 valid processed product
            valid_products = [p for p in catalog.products if p.status in ("processed", "published")]
            if not valid_products:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot publish a catalog without at least one valid processed product",
                )
        catalog.status = payload.status

    db.commit()
    db.refresh(catalog)
    return _build_catalog_response(catalog)


@router.post(
    "/{catalog_id}/publish",
    response_model=CatalogResponse,
    summary="Publish a digital catalog to the marketplace (Owner only)",
)
def publish_catalog(
    catalog_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Publish a catalog. Enforces that the catalog contains at least 1 valid processed/published product."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)

    valid_products = [p for p in catalog.products if p.status in ("processed", "published")]
    if not valid_products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot publish an empty catalog or catalog without processed products",
        )

    catalog.status = "published"
    db.commit()
    db.refresh(catalog)
    return _build_catalog_response(catalog)


@router.delete(
    "/{catalog_id}",
    summary="Delete a catalog (Owner only)",
)
def delete_catalog(
    catalog_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a digital catalog owned by the current user."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)

    db.delete(catalog)
    db.commit()
    return {
        "status": "success",
        "message": f"Catalog {catalog_id} deleted successfully",
    }


# ==========================================
# Catalog Products Association Endpoints
# ==========================================


@router.post(
    "/{catalog_id}/products/{product_id}",
    response_model=CatalogResponse,
    summary="Add a product to a catalog (Verifies ownership of both)",
)
def add_product_to_catalog(
    catalog_id: int,
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Associate an artisan product with a digital catalog. Verifies user owns both."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)

    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == current_user.id)
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or not owned by current user",
        )

    # Check for existing association to prevent duplicates
    if product in catalog.products:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product is already in this catalog",
        )

    catalog.products.append(product)
    db.commit()
    db.refresh(catalog)
    return _build_catalog_response(catalog)


@router.delete(
    "/{catalog_id}/products/{product_id}",
    response_model=CatalogResponse,
    summary="Remove a product from a catalog (Owner only)",
)
def remove_product_from_catalog(
    catalog_id: int,
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Disassociate a product from a user's digital catalog."""
    catalog = _get_user_catalog_or_404(catalog_id, current_user.id, db)

    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.user_id == current_user.id)
        .first()
    )
    if not product or product not in catalog.products:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product is not in this catalog",
        )

    catalog.products.remove(product)
    db.commit()
    db.refresh(catalog)
    return _build_catalog_response(catalog)
