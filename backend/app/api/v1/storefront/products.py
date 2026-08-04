from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.product import ProductListItemOut, ProductOut
from app.services import product_service

router = APIRouter(prefix="/products", tags=["storefront-products"])


@router.get("", response_model=list[ProductListItemOut])
def list_products(track_stock: bool = False, db: Session = Depends(get_db)):
    products = product_service.list_products(
        db, include_inactive=False, track_stock=track_stock
    )
    result = []
    for p in products:
        primary = next((img for img in p.images if img.is_primary), p.images[0] if p.images else None)
        result.append(
            ProductListItemOut(
                id=p.id,
                sku=p.sku,
                name=p.name,
                slug=p.slug,
                base_price=p.base_price,
                status=p.status,
                category_id=p.category_id,
                track_stock=p.track_stock,
                stock_quantity=p.stock_quantity,
                is_featured=p.is_featured,
                primary_image=primary.storage_key if primary else None,
                primary_thumbnail=primary.thumbnail_key if primary else None,
            )
        )
    return result


@router.get("/{slug}", response_model=ProductOut)
def get_product_by_slug(slug: str, db: Session = Depends(get_db)):
    return product_service.get_product_by_slug(db, slug)
