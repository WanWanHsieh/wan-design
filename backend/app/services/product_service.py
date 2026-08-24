from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.attribute import ProductAttributeValue
from app.models.category import Category
from app.models.product import Product
from app.models.product_image import ProductImage
from app.models.product_variant import ProductVariant
from app.schemas.category import CategoryCreate, CategoryUpdate
from app.schemas.product import AttributeValueIn, ProductCreate, ProductUpdate, ProductVariantIn


def _product_query(db: Session, include_attributes: bool = True):
    options = [selectinload(Product.images), selectinload(Product.variants)]
    if include_attributes:
        options.append(selectinload(Product.attribute_values))
    return db.query(Product).options(*options)


def list_products(
    db: Session,
    include_inactive: bool = True,
    track_stock: bool | None = None,
    include_attributes: bool = True,
) -> list[Product]:
    query = _product_query(db, include_attributes=include_attributes).filter(Product.deleted_at.is_(None))
    if not include_inactive:
        query = query.filter(Product.status == "active")
    if track_stock is not None:
        query = query.filter(Product.track_stock.is_(track_stock))
    return query.order_by(Product.id.desc()).all()


def get_product(db: Session, product_id: int) -> Product:
    product = _product_query(db).filter(Product.id == product_id).first()
    if product is None or product.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def get_product_by_slug(db: Session, slug: str) -> Product:
    product = _product_query(db).filter(Product.slug == slug, Product.status == "active").first()
    if product is None or product.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product


def _apply_attribute_values(
    db: Session, product: Product, attribute_values: list[AttributeValueIn]
) -> None:
    db.query(ProductAttributeValue).filter(
        ProductAttributeValue.product_id == product.id
    ).delete()
    for value in attribute_values:
        db.add(
            ProductAttributeValue(
                product_id=product.id,
                attribute_definition_id=value.attribute_definition_id,
                value_text=value.value_text,
                value_number=value.value_number,
                value_boolean=value.value_boolean,
            )
        )


def _apply_variants(db: Session, product: Product, variants: list[ProductVariantIn]) -> None:
    db.query(ProductVariant).filter(ProductVariant.product_id == product.id).delete()
    for variant in variants:
        db.add(
            ProductVariant(
                product_id=product.id,
                sku=variant.sku,
                name=variant.name,
                price=variant.price,
                track_stock=variant.track_stock,
                stock_quantity=variant.stock_quantity,
                sort_order=variant.sort_order,
                is_active=variant.is_active,
            )
        )
    db.flush()

    if variants:
        active_prices = [v.price for v in variants if v.is_active]
        if active_prices:
            product.base_price = min(active_prices)
        product.sale_price = None
        product.sale_starts_at = None
        product.sale_ends_at = None


def create_product(db: Session, data: ProductCreate, created_by: int) -> Product:
    if db.query(Product).filter(Product.sku == data.sku).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "SKU already exists")
    if db.query(Product).filter(Product.slug == data.slug).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    product = Product(
        sku=data.sku,
        name=data.name,
        slug=data.slug,
        description=data.description,
        category_id=data.category_id,
        base_price=data.base_price,
        status=data.status,
        custom_attributes=data.custom_attributes,
        track_stock=data.track_stock,
        stock_quantity=data.stock_quantity,
        is_featured=data.is_featured,
        sale_price=data.sale_price,
        sale_starts_at=data.sale_starts_at,
        sale_ends_at=data.sale_ends_at,
        created_by=created_by,
    )
    db.add(product)
    db.flush()
    _apply_attribute_values(db, product, data.attribute_values)
    _apply_variants(db, product, data.variants)
    db.commit()
    return get_product(db, product.id)


def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = get_product(db, product_id)
    updates = data.model_dump(exclude_unset=True, exclude={"attribute_values", "variants"})
    for field, value in updates.items():
        setattr(product, field, value)
    if data.attribute_values is not None:
        _apply_attribute_values(db, product, data.attribute_values)
    if data.variants is not None:
        _apply_variants(db, product, data.variants)
    db.commit()
    return get_product(db, product_id)


def delete_product(db: Session, product_id: int) -> None:
    from datetime import datetime, timezone

    product = get_product(db, product_id)
    product.deleted_at = datetime.now(timezone.utc)
    db.commit()


def add_product_image(
    db: Session,
    product_id: int,
    storage_key: str,
    thumbnail_key: str,
    is_primary: bool,
    sort_order: int,
    image_type: str = "main",
) -> ProductImage:
    product = get_product(db, product_id)
    if is_primary:
        db.query(ProductImage).filter(ProductImage.product_id == product.id).update(
            {"is_primary": False}
        )
    image = ProductImage(
        product_id=product.id,
        storage_key=storage_key,
        thumbnail_key=thumbnail_key,
        is_primary=is_primary,
        sort_order=sort_order,
        image_type=image_type,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_product_image(db: Session, product_id: int, image_id: int) -> None:
    image = (
        db.query(ProductImage)
        .filter(ProductImage.id == image_id, ProductImage.product_id == product_id)
        .first()
    )
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    db.delete(image)
    db.commit()


def list_categories(db: Session) -> list[Category]:
    return (
        db.query(Category)
        .filter(Category.deleted_at.is_(None))
        .order_by(Category.sort_order, Category.id)
        .all()
    )


def get_category(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None or category.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Category not found")
    return category


def create_category(db: Session, data: CategoryCreate) -> Category:
    if db.query(Category).filter(Category.slug == data.slug).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Slug already exists")
    category = Category(**data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, data: CategoryUpdate) -> Category:
    category = get_category(db, category_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    db.commit()
    return category


def delete_category(db: Session, category_id: int) -> None:
    from datetime import datetime, timezone

    category = get_category(db, category_id)
    category.deleted_at = datetime.now(timezone.utc)
    db.commit()
