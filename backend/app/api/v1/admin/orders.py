from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_permission
from app.schemas.order import (
    OrderItemCompletionUpdate,
    OrderItemOut,
    OrderListItemOut,
    OrderOut,
    OrderUpdate,
)
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["admin-orders"])


@router.get(
    "", response_model=list[OrderListItemOut], dependencies=[Depends(require_permission("orders.read"))]
)
def list_orders(db: Session = Depends(get_db)):
    return order_service.list_orders(db)


@router.get(
    "/{order_id}", response_model=OrderOut, dependencies=[Depends(require_permission("orders.read"))]
)
def get_order(order_id: int, db: Session = Depends(get_db)):
    return order_service.get_order(db, order_id)


@router.put(
    "/{order_id}", response_model=OrderOut, dependencies=[Depends(require_permission("orders.write"))]
)
def update_order(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    return order_service.update_order(db, order_id, payload)


@router.delete(
    "/{order_id}", status_code=204, dependencies=[Depends(require_permission("orders.write"))]
)
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order_service.delete_order(db, order_id)


@router.put(
    "/{order_id}/items/{item_id}/completion",
    response_model=OrderItemOut,
    dependencies=[Depends(require_permission("orders.write"))],
)
def set_item_completed(
    order_id: int, item_id: int, payload: OrderItemCompletionUpdate, db: Session = Depends(get_db)
):
    return order_service.set_item_completed(db, order_id, item_id, payload.is_completed)
