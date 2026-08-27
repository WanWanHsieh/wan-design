from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.order import OrderCreate, OrderOut
from app.services import order_service

router = APIRouter(prefix="/orders", tags=["storefront-orders"])


@router.post("", response_model=OrderOut, status_code=201)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    return order_service.create_order(db, payload)


@router.get("/lookup", response_model=list[OrderOut])
def lookup_orders(phone: str, real_name: str, db: Session = Depends(get_db)):
    return order_service.lookup_orders(db, phone, real_name)
