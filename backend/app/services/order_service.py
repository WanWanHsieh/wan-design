import uuid
from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.material import Material
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.product_variant import ProductVariant
from app.schemas.order import ORDER_STATUSES, OrderCreate, OrderItemIn, OrderUpdate, check_shipping_fields
from app.services import line_service, notification_service


def _order_query(db: Session):
    items = selectinload(Order.items)
    return db.query(Order).options(
        items.selectinload(OrderItem.material).selectinload(Material.images),
        items.selectinload(OrderItem.product).selectinload(Product.images),
    )


def _generate_order_no() -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ORD-{today}-{uuid.uuid4().hex[:6].upper()}"


def _restore_stock_for_items(db: Session, items: list[OrderItem]) -> None:
    for item in items:
        if item.material_id is not None or item.product_id is None:
            continue
        if item.variant_id is not None:
            variant = (
                db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).with_for_update().first()
            )
            if variant is not None and variant.track_stock:
                variant.stock_quantity += item.quantity
            continue
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if product is not None and product.track_stock:
            product.stock_quantity += item.quantity


def _decrement_stock_for_items(db: Session, items: list[OrderItem]) -> None:
    for item in items:
        if item.material_id is not None or item.product_id is None:
            continue
        if item.variant_id is not None:
            variant = (
                db.query(ProductVariant).filter(ProductVariant.id == item.variant_id).with_for_update().first()
            )
            if variant is not None and variant.track_stock:
                if variant.stock_quantity < item.quantity:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, f"規格「{variant.name}」庫存不足,無法恢復此訂單"
                    )
                variant.stock_quantity -= item.quantity
            continue
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if product is not None and product.track_stock:
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」庫存不足,無法恢復此訂單"
                )
            product.stock_quantity -= item.quantity


def _item_key(
    product_id: int | None,
    variant_id: int | None,
    material_id: int | None,
    quantity: int,
    custom_note: str | None,
    extra_charge,
) -> tuple:
    # extra_charge 以數值(兩位小數)比較;custom_note 空字串視同 None
    extra = Decimal(str(extra_charge or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (product_id, variant_id, material_id, int(quantity), custom_note or None, extra)


def _diff_order_items(
    existing: list[OrderItem], incoming: list[OrderItemIn]
) -> tuple[list[OrderItem], list[OrderItem], list[OrderItemIn]]:
    """以多重集合比對,回傳 (保留的現有品項, 被移除的現有品項, 新增的傳入品項)。"""
    pool: dict[tuple, list[OrderItem]] = {}
    for item in existing:
        key = _item_key(
            item.product_id, item.variant_id, item.material_id,
            item.quantity, item.custom_note, item.extra_charge,
        )
        pool.setdefault(key, []).append(item)

    kept: list[OrderItem] = []
    added: list[OrderItemIn] = []
    for new in incoming:
        key = _item_key(
            new.product_id, new.variant_id, new.material_id,
            new.quantity, getattr(new, "custom_note", None), getattr(new, "extra_charge", 0),
        )
        bucket = pool.get(key)
        if bucket:
            kept.append(bucket.pop(0))
        else:
            added.append(new)

    removed = [item for bucket in pool.values() for item in bucket]
    return kept, removed, added


def _resolve_variant(db: Session, product: Product, variant_id: int | None) -> ProductVariant | None:
    if not product.has_variants:
        return None
    if variant_id is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」需要選擇規格")
    variant = (
        db.query(ProductVariant)
        .filter(
            ProductVariant.id == variant_id,
            ProductVariant.product_id == product.id,
            ProductVariant.is_active.is_(True),
        )
        .with_for_update()
        .first()
    )
    if variant is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」的規格不存在或已停用")
    return variant


def _build_order_items(
    db: Session, items: list[OrderItemIn], adjust_stock: bool = True
) -> tuple[list[OrderItem], float]:
    order_items = []
    total_amount = 0.0

    for item in items:
        product = (
            db.query(Product)
            .filter(Product.id == item.product_id, Product.deleted_at.is_(None), Product.status == "active")
            .with_for_update()
            .first()
        )
        if product is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Product {item.product_id} not found")

        variant = _resolve_variant(db, product, item.variant_id)
        stock_target = variant if variant is not None else product
        extra_charge = float(getattr(item, "extra_charge", 0) or 0)
        custom_note = getattr(item, "custom_note", None)

        # 現貨商品(商品本身 track_stock)與加購商品不使用布料;帶布料會走訂製分支而繞過庫存檢查。
        # 只看商品層級:訂製商品的規格可各自勾庫存追蹤,但仍須選布料,不能被擋
        if item.material_id is not None and (product.track_stock or not product.requires_material):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」不需選擇布料")

        if item.material_id is None:
            if not stock_target.track_stock and product.requires_material:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」需要選擇布料"
                )
            if stock_target.track_stock and adjust_stock:
                if stock_target.stock_quantity < item.quantity:
                    raise HTTPException(
                        status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」庫存不足"
                    )
                stock_target.stock_quantity -= item.quantity

            base_price = float(variant.price) if variant is not None else float(product.effective_price)
            unit_price = base_price + extra_charge
            subtotal = round(unit_price * item.quantity, 2)
            total_amount += subtotal

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    variant_id=variant.id if variant is not None else None,
                    variant_name_snapshot=variant.name if variant is not None else None,
                    material_id=None,
                    material_name_snapshot=None,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    subtotal=subtotal,
                    custom_note=custom_note,
                    extra_charge=extra_charge,
                )
            )
            continue

        material = (
            db.query(Material)
            .filter(
                Material.id == item.material_id,
                Material.deleted_at.is_(None),
                Material.status == "active",
            )
            .first()
        )
        if material is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, f"Material {item.material_id} not found")

        base_price = float(variant.price) if variant is not None else float(product.effective_price)
        unit_price = base_price + float(material.price_addon) + extra_charge
        subtotal = round(unit_price * item.quantity, 2)
        total_amount += subtotal

        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name_snapshot=product.name,
                variant_id=variant.id if variant is not None else None,
                variant_name_snapshot=variant.name if variant is not None else None,
                material_id=material.id,
                material_name_snapshot=material.name,
                unit_price=unit_price,
                quantity=item.quantity,
                subtotal=subtotal,
                custom_note=custom_note,
                extra_charge=extra_charge,
            )
        )

    return order_items, round(total_amount, 2)


def create_order(db: Session, data: OrderCreate) -> Order:
    order_items, total_amount = _build_order_items(db, data.items)

    order = Order(
        order_no=_generate_order_no(),
        real_name=data.real_name,
        contact_source=data.contact_source,
        customer_name=data.customer_name,
        phone=data.phone,
        shipping_method=data.shipping_method,
        shipping_store_code=data.shipping_store_code,
        shipping_address=data.shipping_address,
        expected_delivery_date=data.expected_delivery_date,
        total_amount=total_amount,
        notes=data.notes,
        items=order_items,
    )
    db.add(order)
    db.commit()
    created_order = get_order(db, order.id)
    notification_service.notify_new_order(created_order)
    summary = notification_service.build_order_summary(created_order)
    line_service.push_message(settings.LINE_ADMIN_USER_ID, f"🔔新訂單通知\n\n{summary}")
    return created_order


def list_orders(db: Session) -> list[Order]:
    return _order_query(db).order_by(Order.id.desc()).all()


def get_order(db: Session, order_id: int) -> Order:
    order = _order_query(db).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def update_order(db: Session, order_id: int, data: OrderUpdate) -> Order:
    order = get_order(db, order_id)
    previous_status = order.status
    stock_was_reserved = previous_status != "cancelled"

    if data.status is not None and data.status not in ORDER_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid status")

    updates = data.model_dump(exclude_unset=True, exclude={"items"})
    for field, value in updates.items():
        setattr(order, field, value)

    if "shipping_method" in updates:
        if order.shipping_method == "address":
            order.shipping_store_code = None
        else:
            order.shipping_address = None

    will_reserve = order.status != "cancelled"

    # 把傳入品項與現有品項比對:相同的原樣保留(不重算價格、不動庫存),
    # 只有被移除/新增的品項才影響庫存與金額
    if data.items is not None:
        kept, removed, added_inputs = _diff_order_items(order.items, data.items)
    else:
        kept, removed, added_inputs = list(order.items), [], []

    # 庫存不變式:訂單非 cancelled 時,所有現貨品項(material_id 為空且 track_stock)都已預留
    if stock_was_reserved:
        # 被移除的品項一定退回;若訂單同時改為取消,保留的品項也退回
        _restore_stock_for_items(db, removed if will_reserve else removed + kept)
    elif will_reserve:
        # 從取消恢復:現有且保留的品項重新預留(被移除的本來就沒預留)
        _decrement_stock_for_items(db, kept)

    # 新增品項:才檢查商品/布料是否上架,並依 will_reserve 決定是否扣庫存
    added_items: list[OrderItem] = []
    if added_inputs:
        added_items, _ = _build_order_items(db, added_inputs, adjust_stock=will_reserve)

    if removed or added_items:
        order.items = kept + added_items

    order.total_amount = round(
        sum(float(item.subtotal) for item in order.items) + float(order.adjustment_amount), 2
    )

    try:
        check_shipping_fields(order.shipping_method, order.shipping_store_code, order.shipping_address)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.commit()
    return get_order(db, order_id)


def merge_orders(db: Session, primary_order_id: int, secondary_order_id: int) -> Order:
    if primary_order_id == secondary_order_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "不能合併同一張訂單")

    primary = get_order(db, primary_order_id)
    secondary = get_order(db, secondary_order_id)

    if primary.status == "cancelled" or secondary.status == "cancelled":
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "已取消的訂單無法合併")

    for item in list(secondary.items):
        secondary.items.remove(item)
        primary.items.append(item)

    primary.adjustment_amount = round(
        float(primary.adjustment_amount) + float(secondary.adjustment_amount), 2
    )
    primary.adjustment_note = "\n".join(
        note for note in [primary.adjustment_note, secondary.adjustment_note] if note
    ) or None
    merge_note = f"【已合併訂單 {secondary.order_no}】"
    primary.notes = "\n".join(note for note in [primary.notes, secondary.notes, merge_note] if note)
    primary.total_amount = round(
        sum(float(item.subtotal) for item in primary.items) + float(primary.adjustment_amount), 2
    )

    db.delete(secondary)
    db.commit()
    return get_order(db, primary.id)


def delete_order(db: Session, order_id: int) -> None:
    order = get_order(db, order_id)
    if order.status != "cancelled":
        _restore_stock_for_items(db, order.items)
    db.delete(order)
    db.commit()


def lookup_orders(db: Session, phone: str, real_name: str) -> list[Order]:
    # Orders placed before the real_name field existed have no real_name on file,
    # so fall back to customer_name for those so old orders stay findable.
    name_on_file = func.lower(func.coalesce(Order.real_name, Order.customer_name))
    orders = (
        _order_query(db)
        .filter(
            Order.phone == phone.strip(),
            name_on_file == real_name.strip().lower(),
        )
        .order_by(Order.id.desc())
        .all()
    )
    if not orders:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "找不到符合的訂單,請確認姓名與電話是否正確")
    return orders


def set_item_completed(db: Session, order_id: int, item_id: int, is_completed: bool) -> OrderItem:
    item = (
        db.query(OrderItem)
        .filter(OrderItem.id == item_id, OrderItem.order_id == order_id)
        .first()
    )
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order item not found")
    item.is_completed = is_completed
    db.commit()
    db.refresh(item)
    return item
