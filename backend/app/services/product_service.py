from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.attribute import ProductAttributeValue
from app.models.category import Category
from app.models.order import OrderItem
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


_VARIANT_FIELDS = {"sku", "name", "price", "track_stock", "stock_quantity", "sort_order", "is_active"}


def _apply_variants(db: Session, product: Product, variants: list[ProductVariantIn]) -> None:
    # 規格 ID 要保持穩定(訂單的 variant_id、取消時退庫存都靠它),所以不能整批刪除重建:
    # 有帶 id = 就地更新(只動請求實際提供的欄位);沒帶 id = 新增;請求中沒出現的現有規格
    # 有被訂單參照就停用(保留歷史),否則刪除。
    existing = {
        v.id: v
        for v in db.query(ProductVariant)
        .filter(ProductVariant.product_id == product.id)
        .with_for_update()
        .all()
    }

    requested_ids = [v.id for v in variants if v.id is not None]
    if len(requested_ids) != len(set(requested_ids)):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "規格 id 重複")
    unknown_ids = [i for i in requested_ids if i not in existing]
    if unknown_ids:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, f"規格 id {unknown_ids} 不屬於此商品"
        )

    # 要求移除全部規格時,若其中有被訂單參照者,無法刪除只能停用,
    # 會變成「規格全停用但商品仍視為有規格」而無法下單,所以直接拒絕(在任何修改之前)
    if not variants and existing:
        referenced_any = (
            db.query(OrderItem.id).filter(OrderItem.variant_id.in_(list(existing))).first() is not None
        )
        if referenced_any:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                "這些規格已被訂單使用,不可全部移除,請改為停用個別規格",
            )

    final_variants: list[ProductVariant] = []
    for variant in variants:
        if variant.id is not None:
            target = existing[variant.id]
            # 沒提供的欄位(特別是 stock_quantity、track_stock)維持原值
            for field in variant.model_fields_set & _VARIANT_FIELDS:
                setattr(target, field, getattr(variant, field))
        else:
            target = ProductVariant(
                product_id=product.id, **variant.model_dump(exclude={"id"})
            )
            db.add(target)
        final_variants.append(target)

    requested = set(requested_ids)
    for variant_id, old in existing.items():
        if variant_id in requested:
            continue
        referenced = (
            db.query(OrderItem.id).filter(OrderItem.variant_id == variant_id).first() is not None
        )
        if referenced:
            old.is_active = False
        else:
            db.delete(old)
    db.flush()

    if final_variants:
        active_prices = [float(v.price) for v in final_variants if v.is_active]
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
        requires_material=data.requires_material,
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
    # 庫存欄位:沒帶(exclude_unset)或明確帶 null 都視為不更新,避免覆寫庫存或違反 NOT NULL
    for field in ("stock_quantity", "track_stock"):
        if field in updates and updates[field] is None:
            del updates[field]
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
