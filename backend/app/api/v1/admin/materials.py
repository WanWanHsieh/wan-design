import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.schemas.bulk_import import BulkImportResult
from app.schemas.material import MaterialCreate, MaterialImageOut, MaterialOut, MaterialUpdate
from app.services import bulk_import_service, image_service, material_service, storage_service

router = APIRouter(prefix="/materials", tags=["admin-materials"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


@router.get(
    "", response_model=list[MaterialOut], dependencies=[Depends(require_permission("materials.read"))]
)
def list_materials(db: Session = Depends(get_db)):
    return material_service.list_materials(db)


@router.get(
    "/{material_id}", response_model=MaterialOut,
    dependencies=[Depends(require_permission("materials.read"))],
)
def get_material(material_id: int, db: Session = Depends(get_db)):
    return material_service.get_material(db, material_id)


@router.post(
    "/bulk-import",
    response_model=BulkImportResult,
    dependencies=[Depends(require_permission("materials.write"))],
)
def bulk_import_materials(
    csv_file: UploadFile = File(...),
    zip_file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    csv_bytes = csv_file.file.read()
    zip_bytes = zip_file.file.read() if zip_file is not None else None
    return bulk_import_service.import_materials(db, csv_bytes, zip_bytes, admin_user.id)


@router.post(
    "", response_model=MaterialOut, status_code=201,
    dependencies=[Depends(require_permission("materials.write"))],
)
def create_material(
    payload: MaterialCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    return material_service.create_material(db, payload, created_by=admin_user.id)


@router.put(
    "/{material_id}", response_model=MaterialOut,
    dependencies=[Depends(require_permission("materials.write"))],
)
def update_material(material_id: int, payload: MaterialUpdate, db: Session = Depends(get_db)):
    return material_service.update_material(db, material_id, payload)


@router.delete(
    "/{material_id}", status_code=204, dependencies=[Depends(require_permission("materials.write"))]
)
def delete_material(material_id: int, db: Session = Depends(get_db)):
    material_service.delete_material(db, material_id)


@router.post(
    "/{material_id}/images",
    response_model=MaterialImageOut,
    status_code=201,
    dependencies=[Depends(require_permission("materials.write"))],
)
def upload_material_image(
    material_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    sort_order: int = Form(0),
    image_type: str = Form("fabric"),
    db: Session = Depends(get_db),
):
    if image_type not in {"fabric", "showcase"}:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid image_type")

    extension = Path(file.filename or "").suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unsupported image type")

    contents = file.file.read()
    if len(contents) > MAX_IMAGE_BYTES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Image exceeds 15MB limit")

    try:
        resized_bytes, thumbnail_bytes, out_extension = image_service.process_upload(contents)
    except Exception as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Could not process image file") from exc

    file_id = uuid.uuid4().hex
    filename = f"{file_id}{out_extension}"
    thumbnail_filename = f"{file_id}_thumb{out_extension}"

    storage_key = f"materials/{material_id}/{filename}"
    thumbnail_key = f"materials/{material_id}/{thumbnail_filename}"
    storage_service.save_file(storage_key, resized_bytes)
    storage_service.save_file(thumbnail_key, thumbnail_bytes)
    return material_service.add_material_image(
        db, material_id, storage_key, thumbnail_key, is_primary, sort_order, image_type
    )


@router.delete(
    "/{material_id}/images/{image_id}",
    status_code=204,
    dependencies=[Depends(require_permission("materials.write"))],
)
def delete_material_image(material_id: int, image_id: int, db: Session = Depends(get_db)):
    material_service.delete_material_image(db, material_id, image_id)
