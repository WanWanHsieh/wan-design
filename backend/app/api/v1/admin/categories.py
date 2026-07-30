from fastapi import APIRouter, Depends

from app.api.deps import get_db, require_permission
from app.schemas.category import CategoryCreate, CategoryOut, CategoryUpdate
from app.services import product_service
from sqlalchemy.orm import Session

router = APIRouter(prefix="/categories", tags=["admin-categories"])


@router.get(
    "", response_model=list[CategoryOut], dependencies=[Depends(require_permission("categories.read"))]
)
def list_categories(db: Session = Depends(get_db)):
    return product_service.list_categories(db)


@router.post(
    "", response_model=CategoryOut, status_code=201,
    dependencies=[Depends(require_permission("categories.write"))],
)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    return product_service.create_category(db, payload)


@router.put(
    "/{category_id}", response_model=CategoryOut,
    dependencies=[Depends(require_permission("categories.write"))],
)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    return product_service.update_category(db, category_id, payload)


@router.delete(
    "/{category_id}", status_code=204, dependencies=[Depends(require_permission("categories.write"))]
)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    product_service.delete_category(db, category_id)
