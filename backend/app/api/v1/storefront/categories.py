from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.category import CategoryOut
from app.services import product_service

router = APIRouter(prefix="/categories", tags=["storefront-categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    return [c for c in product_service.list_categories(db) if c.is_active]
