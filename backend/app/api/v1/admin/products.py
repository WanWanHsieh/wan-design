import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_admin_user, get_db, require_permission
from app.models.attribute import AttributeDefinition
from app.schemas.product import (
    AttributeDefinitionCreate,
    AttributeDefinitionOut,
    ProductCreate,
    ProductImageOut,
    ProductOut,
    ProductUpdate,
)
from app.services import image_service, product_service, storage_service

router = APIRouter(prefix="/products", tags=["admin-products"])

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


@router.get(
    "", response_model=list[ProductOut], dependencies=[Depends(require_permission("products.read"))]
)
def list_products(track_stock: bool | None = None, db: Session = Depends(get_db)):
    return product_service.list_products(db, track_stock=track_stock)


@router.get(
    "/attribute-definitions",
    response_model=list[AttributeDefinitionOut],
    dependencies=[Depends(require_permission("products.read"))],
)
def list_attribute_definitions(db: Session = Depends(get_db)):
    return db.query(AttributeDefinition).order_by(AttributeDefinition.sort_order).all()


@router.post(
    "/attribute-definitions",
    response_model=AttributeDefinitionOut,
    status_code=201,
    dependencies=[Depends(require_permission("products.write"))],
)
def create_attribute_definition(payload: AttributeDefinitionCreate, db: Session = Depends(get_db)):
    definition = AttributeDefinition(**payload.model_dump())
    db.add(definition)
    db.commit()
    db.refresh(definition)
    return definition


@router.get(
    "/{product_id}", response_model=ProductOut,
    dependencies=[Depends(require_permission("products.read"))],
)
def get_product(product_id: int, db: Session = Depends(get_db)):
    return product_service.get_product(db, product_id)


@router.post(
    "", response_model=ProductOut, status_code=201,
    dependencies=[Depends(require_permission("products.write"))],
)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    admin_user=Depends(get_current_admin_user),
):
    return product_service.create_product(db, payload, created_by=admin_user.id)


@router.put(
    "/{product_id}", response_model=ProductOut,
    dependencies=[Depends(require_permission("products.write"))],
)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    return product_service.update_product(db, product_id, payload)


@router.delete(
    "/{product_id}", status_code=204, dependencies=[Depends(require_permission("products.write"))]
)
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product_service.delete_product(db, product_id)


@router.post(
    "/{product_id}/images",
    response_model=ProductImageOut,
    status_code=201,
    dependencies=[Depends(require_permission("products.write"))],
)
def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = Form(False),
    sort_order: int = Form(0),
    db: Session = Depends(get_db),
):
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

    storage_key = f"products/{product_id}/{filename}"
    thumbnail_key = f"products/{product_id}/{thumbnail_filename}"
    storage_service.save_file(storage_key, resized_bytes)
    storage_service.save_file(thumbnail_key, thumbnail_bytes)
    return product_service.add_product_image(
        db, product_id, storage_key, thumbnail_key, is_primary, sort_order
    )


@router.delete(
    "/{product_id}/images/{image_id}",
    status_code=204,
    dependencies=[Depends(require_permission("products.write"))],
)
def delete_product_image(product_id: int, image_id: int, db: Session = Depends(get_db)):
    product_service.delete_product_image(db, product_id, image_id)
