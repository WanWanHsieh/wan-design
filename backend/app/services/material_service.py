from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import exists, or_
from sqlalchemy.orm import Session, selectinload

from app.models.material import Material, MaterialImage
from app.schemas.material import MaterialCreate, MaterialImageOut, MaterialPublicOut, MaterialUpdate


def _material_query(db: Session):
    return db.query(Material).options(selectinload(Material.images))


def to_public_out(material: Material) -> MaterialPublicOut:
    return MaterialPublicOut(
        id=material.id,
        code=material.code,
        name=material.name,
        price_addon=material.price_addon,
        origin=material.origin,
        fabric_type=material.fabric_type,
        images=[MaterialImageOut.model_validate(img) for img in material.images],
    )


def list_materials(db: Session, include_inactive: bool = True) -> list[Material]:
    query = _material_query(db).filter(Material.deleted_at.is_(None))
    if not include_inactive:
        query = query.filter(Material.status == "active")
    return query.order_by(Material.id.desc()).all()


def _has_showcase_expr():
    return exists().where(
        MaterialImage.material_id == Material.id, MaterialImage.image_type == "showcase"
    )


def _apply_order(query, code_order: str | None, showcase_order: str | None):
    if code_order == "asc":
        return query.order_by(Material.code.asc(), Material.id.asc())
    if code_order == "desc":
        return query.order_by(Material.code.desc(), Material.id.desc())
    if showcase_order == "asc":
        return query.order_by(_has_showcase_expr().asc(), Material.id.desc())
    if showcase_order == "desc":
        return query.order_by(_has_showcase_expr().desc(), Material.id.desc())
    return query.order_by(Material.id.desc())


def list_materials_page(
    db: Session,
    search: str | None = None,
    fabric_type: str | None = None,
    origin: str | None = None,
    status: str | None = None,
    page: int = 1,
    page_size: int = 20,
    code_order: str | None = None,
    showcase_order: str | None = None,
) -> tuple[list[Material], int]:
    query = _material_query(db).filter(Material.deleted_at.is_(None))
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Material.name.ilike(pattern), Material.code.ilike(pattern)))
    if fabric_type:
        query = query.filter(Material.fabric_type == fabric_type)
    if origin:
        query = query.filter(Material.origin == origin)
    if status:
        query = query.filter(Material.status == status)

    total = query.order_by(None).count()
    items = (
        _apply_order(query, code_order, showcase_order)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def list_materials_public_page(
    db: Session,
    fabric_type: str | None = None,
    origin: str | None = None,
    page: int = 1,
    page_size: int = 20,
    code_order: str | None = None,
) -> tuple[list[Material], int]:
    query = _material_query(db).filter(Material.deleted_at.is_(None), Material.status == "active")
    if fabric_type:
        query = query.filter(Material.fabric_type == fabric_type)
    if origin:
        query = query.filter(Material.origin == origin)

    total = query.order_by(None).count()
    items = (
        _apply_order(query, code_order, None)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return items, total


def get_material(db: Session, material_id: int) -> Material:
    material = _material_query(db).filter(Material.id == material_id).first()
    if material is None or material.deleted_at is not None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Material not found")
    return material


def create_material(db: Session, data: MaterialCreate, created_by: int) -> Material:
    if data.code and db.query(Material).filter(Material.code == data.code).first() is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Material code already exists")
    material = Material(**data.model_dump(), created_by=created_by)
    db.add(material)
    db.commit()
    return get_material(db, material.id)


def update_material(db: Session, material_id: int, data: MaterialUpdate) -> Material:
    material = get_material(db, material_id)
    updates = data.model_dump(exclude_unset=True)
    if "code" in updates and updates["code"] and updates["code"] != material.code:
        if db.query(Material).filter(Material.code == updates["code"]).first() is not None:
            raise HTTPException(status.HTTP_409_CONFLICT, "Material code already exists")
    for field, value in updates.items():
        setattr(material, field, value)
    db.commit()
    return get_material(db, material_id)


def delete_material(db: Session, material_id: int) -> None:
    material = get_material(db, material_id)
    material.deleted_at = datetime.now(timezone.utc)
    db.commit()


def add_material_image(
    db: Session,
    material_id: int,
    storage_key: str,
    thumbnail_key: str,
    is_primary: bool,
    sort_order: int,
    image_type: str = "fabric",
) -> MaterialImage:
    material = get_material(db, material_id)
    if is_primary:
        db.query(MaterialImage).filter(
            MaterialImage.material_id == material.id, MaterialImage.image_type == image_type
        ).update({"is_primary": False})
    image = MaterialImage(
        material_id=material.id,
        storage_key=storage_key,
        thumbnail_key=thumbnail_key,
        is_primary=is_primary,
        sort_order=sort_order,
        image_type=image_type,
    )
    db.add(image)
    db.commit()
    db.refresh(image)
    return image


def delete_material_image(db: Session, material_id: int, image_id: int) -> None:
    image = (
        db.query(MaterialImage)
        .filter(MaterialImage.id == image_id, MaterialImage.material_id == material_id)
        .first()
    )
    if image is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Image not found")
    db.delete(image)
    db.commit()
