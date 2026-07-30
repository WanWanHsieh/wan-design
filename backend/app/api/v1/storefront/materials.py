from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.material import MaterialPublicOut
from app.services import material_service

router = APIRouter(prefix="/materials", tags=["storefront-materials"])


@router.get("", response_model=list[MaterialPublicOut])
def list_materials(db: Session = Depends(get_db)):
    materials = material_service.list_materials(db, include_inactive=False)
    return [material_service.to_public_out(m) for m in materials]


@router.get("/{material_id}", response_model=MaterialPublicOut)
def get_material(material_id: int, db: Session = Depends(get_db)):
    material = material_service.get_material(db, material_id)
    if material.status != "active":
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material not found")
    return material_service.to_public_out(material)
