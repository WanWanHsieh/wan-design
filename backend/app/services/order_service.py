import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app.models.material import Material
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.schemas.order import ORDER_STATUSES, OrderCreate, OrderItemIn, OrderUpdate, check_shipping_fields


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
        product = db.query(Product).filter(Product.id == item.product_id).with_for_update().first()
        if product is not None and product.track_stock:
            product.stock_quantity += item.quantity


def _build_order_items(db: Session, items: list[OrderItemIn]) -> tuple[list[OrderItem], float]:
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

        if item.material_id is None:
            if not product.track_stock:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」非現貨販售商品"
                )
            if product.stock_quantity < item.quantity:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST, f"商品「{product.name}」庫存不足"
                )
            product.stock_quantity -= item.quantity

            unit_price = float(product.base_price)
            subtotal = round(unit_price * item.quantity, 2)
            total_amount += subtotal

            order_items.append(
                OrderItem(
                    product_id=product.id,
                    product_name_snapshot=product.name,
                    material_id=None,
                    material_name_snapshot=None,
                    unit_price=unit_price,
                    quantity=item.quantity,
                    subtotal=subtotal,
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

        unit_price = float(product.base_price) + float(material.price_addon)
        subtotal = round(unit_price * item.quantity, 2)
        total_amount += subtotal

        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name_snapshot=product.name,
                material_id=material.id,
                material_name_snapshot=material.name,
                unit_price=unit_price,
                quantity=item.quantity,
                subtotal=subtotal,
            )
        )

    return order_items, round(total_amount, 2)


def create_order(db: Session, data: OrderCreate) -> Order:
    order_items, total_amount = _build_order_items(db, data.items)

    order = Order(
        order_no=_generate_order_no(),
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
    return get_order(db, order.id)


def list_orders(db: Session) -> list[Order]:
    return _order_query(db).order_by(Order.id.desc()).all()


def get_order(db: Session, order_id: int) -> Order:
    order = _order_query(db).filter(Order.id == order_id).first()
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order


def update_order(db: Session, order_id: int, data: OrderUpdate) -> Order:
    order = get_order(db, order_id)

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

    if data.items is not None:
        _restore_stock_for_items(db, order.items)
        order_items, total_amount = _build_order_items(db, data.items)
        order.items = order_items
        order.total_amount = total_amount

    try:
        check_shipping_fields(order.shipping_method, order.shipping_store_code, order.shipping_address)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc

    db.commit()
    return get_order(db, order_id)


def delete_order(db: Session, order_id: int) -> None:
    order = get_order(db, order_id)
    _restore_stock_for_items(db, order.items)
    db.delete(order)
    db.commit()


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
