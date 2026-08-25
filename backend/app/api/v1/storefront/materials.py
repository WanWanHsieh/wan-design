from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.material import MaterialPublicOut, MaterialPublicPageOut
from app.services import material_service

router = APIRouter(prefix="/materials", tags=["storefront-materials"])


@router.get("", response_model=MaterialPublicPageOut)
def list_materials(
    fabric_type: str | None = None,
    origin: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    code_order: str | None = Query(None, pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
):
    items, total = material_service.list_materials_public_page(
        db, fabric_type=fabric_type, origin=origin, page=page, page_size=page_size, code_order=code_order
    )
    return MaterialPublicPageOut(
        items=[material_service.to_public_out(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{material_id}", response_model=MaterialPublicOut)
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = material_service.get_material(db, material_id)
    if material.status != "active":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material not found")
    return material_service.to_public_out(material)
