from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, select

from app.database import get_db
from app.models.catalog import Catalog, catalog_products
from app.models.product import Product
from app.schemas.catalog import CatalogResponse, CatalogProductItem
from app.schemas.product import ProductResponse, ProductPriceItem, ProductAudioItem
from app.schemas.product_image import ProductImageItem

router = APIRouter(
    prefix="/marketplace",
    tags=["Marketplace"],
)


@router.get(
    "/products",
    response_model=List[ProductResponse],
    summary="List publicly available marketplace products (Public)",
)
def list_marketplace_products(
    category: Optional[str] = Query(default=None, description="Filter by product category"),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve publicly visible marketplace products.

    Visibility rules:
    - Products with status 'published' are visible.
    - Products with status 'processed' that belong to an active published catalog are visible.
    - Products with status 'draft', 'uploaded', 'processing', 'processing_failed', or 'archived' are strictly HIDDEN.
    """
    safe_limit = min(max(1, limit), 100)

    # Subquery: products in published catalogs
    published_catalog_ids = select(Catalog.id).where(Catalog.status == "published")
    catalog_product_ids = (
        select(catalog_products.c.product_id)
        .where(catalog_products.c.catalog_id.in_(published_catalog_ids))
    )

    query = db.query(Product).filter(
        or_(
            Product.status == "published",
            (Product.status == "processed") & (Product.id.in_(catalog_product_ids)),
        )
    )

    if category:
        query = query.filter(Product.category.ilike(f"%{category.strip()}%"))

    products = query.order_by(Product.id.desc()).offset(offset).limit(safe_limit).all()

    # Transform to ProductResponse
    result = []
    for p in products:
        result.append(
            ProductResponse(
                id=p.id,
                user_id=p.user_id,
                name=p.name,
                description_en=p.description_en,
                description_hi=p.description_hi,
                category=p.category,
                material=p.material,
                raw_material_cost=p.raw_material_cost,
                labour_cost=p.labour_cost,
                packaging_cost=p.packaging_cost,
                status=p.status,
                seo_title=p.seo_title,
                seo_keywords=p.seo_keywords,
                voice_transcription=p.voice_transcription,
                translated_voice_text=p.translated_voice_text,
                images=[ProductImageItem.model_validate(img) for img in p.images],
                audio_recordings=[ProductAudioItem.model_validate(aud) for aud in p.audio_recordings],
                prices=[ProductPriceItem.model_validate(pr) for pr in p.prices],
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )
    return result


@router.get(
    "/catalogs",
    response_model=List[CatalogResponse],
    summary="List publicly available marketplace catalogs (Public)",
)
def list_marketplace_catalogs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Retrieve published digital catalogs on the marketplace with valid products."""
    safe_limit = min(max(1, limit), 100)
    catalogs = (
        db.query(Catalog)
        .filter(Catalog.status == "published")
        .order_by(Catalog.id.desc())
        .offset(offset)
        .limit(safe_limit)
        .all()
    )

    result = []
    for c in catalogs:
        # Filter products in catalog: only include processed/published products
        valid_products = [p for p in c.products if p.status in ("processed", "published")]
        product_items = []
        for p in valid_products:
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
        result.append(
            CatalogResponse(
                id=c.id,
                user_id=c.user_id,
                title=c.title,
                description=c.description,
                status=c.status,
                products=product_items,
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
        )
    return result
