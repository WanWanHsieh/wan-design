import csv
import io
import random
import zipfile
from zipfile import ZipFile

from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.material import Material, MaterialImage
from app.models.product import Product
from app.models.product_image import ProductImage
from app.schemas.bulk_import import BulkImportResult
from app.services import image_service, storage_service

UNAMBIGUOUS_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

UNIT_LABELS_TO_CODE = {
    "公尺": "meter",
    "碼": "yard",
    "公斤": "kg",
    "件": "piece",
}


class RowError(Exception):
    """Raised for a row-level problem that should skip just that row."""


def _random_token(length: int) -> str:
    return "".join(random.choice(UNAMBIGUOUS_CHARS) for _ in range(length))


def _generate_sku(prefix: str) -> str:
    return f"{prefix}-{_random_token(6)}"


def _generate_slug(prefix: str) -> str:
    return f"{prefix}-{_random_token(6).lower()}"


def _read_csv_rows(csv_bytes: bytes) -> list[dict]:
    text = csv_bytes.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for raw_row in reader:
        clean: dict[str, str] = {}
        for key, value in raw_row.items():
            if key is None:
                continue  # extra unnamed columns beyond the header
            if isinstance(value, list):
                value = value[0] if value else ""
            clean[key.strip()] = (value or "").strip()
        rows.append(clean)
    return rows


def _open_zip(zip_bytes: bytes | None) -> ZipFile | None:
    if not zip_bytes:
        return None
    try:
        return zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile:
        return None


def _filename_variants(name: str) -> set[str]:
    variants = {name.lower()}
    # Some zip tools mis-encode non-ASCII filenames; try the common cp437/utf-8 round-trips.
    try:
        variants.add(name.encode("cp437").decode("utf-8").lower())
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    try:
        variants.add(name.encode("utf-8").decode("cp437").lower())
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return variants


def _find_zip_entry(zf: ZipFile | None, filename: str) -> str | None:
    if zf is None or not filename:
        return None
    target = filename.strip().lower()
    for name in zf.namelist():
        base = name.rsplit("/", 1)[-1]
        if target in _filename_variants(base):
            return name
    return None


def _bool_from_text(text: str) -> bool:
    return text.strip() in {"是", "true", "True", "TRUE", "1", "yes"}


def _parse_float(text: str, field_label: str, default: float | None = None) -> float:
    text = text.strip()
    if not text:
        if default is not None:
            return default
        raise RowError(f"「{field_label}」是必填欄位")
    try:
        return float(text)
    except ValueError:
        raise RowError(f"「{field_label}」格式錯誤:{text!r}") from None


def _save_image_from_zip(
    zf: ZipFile | None, entry_name: str, entity_type: str, entity_id: int
) -> tuple[str, str] | None:
    extension = "." + entry_name.rsplit(".", 1)[-1].lower() if "." in entry_name else ""
    if extension not in ALLOWED_IMAGE_EXTENSIONS or zf is None:
        return None
    contents = zf.read(entry_name)
    resized_bytes, thumbnail_bytes, out_extension = image_service.process_upload(contents)
    file_id = _random_token(16).lower()
    storage_key = f"{entity_type}/{entity_id}/{file_id}{out_extension}"
    thumbnail_key = f"{entity_type}/{entity_id}/{file_id}_thumb{out_extension}"
    storage_service.save_file(storage_key, resized_bytes)
    storage_service.save_file(thumbnail_key, thumbnail_bytes)
    return storage_key, thumbnail_key


def import_products(
    db: Session, csv_bytes: bytes, zip_bytes: bytes | None, created_by: int
) -> BulkImportResult:
    rows = _read_csv_rows(csv_bytes)
    zf = _open_zip(zip_bytes)
    categories_by_name = {
        c.name.strip(): c
        for c in db.query(Category).filter(Category.deleted_at.is_(None)).all()
    }

    created = 0
    errors: list[dict] = []

    for index, row in enumerate(rows, start=2):  # row 1 is the header
        try:
            name = row.get("名稱", "")
            if not name:
                raise RowError("缺少「名稱」")
            base_price = _parse_float(row.get("價格", ""), "價格")

            category_name = row.get("分類", "")
            category = categories_by_name.get(category_name) if category_name else None
            if category_name and category is None:
                errors.append(
                    {"row": index, "message": f"找不到分類「{category_name}」,商品已建立但未設定分類"}
                )

            product = Product(
                sku=_generate_sku("PD"),
                name=name,
                slug=_generate_slug("pd"),
                description=row.get("描述") or None,
                category_id=category.id if category else None,
                base_price=base_price,
                status="active",
                track_stock=_bool_from_text(row.get("現貨", "")),
                stock_quantity=int(_parse_float(row.get("庫存數量", ""), "庫存數量", default=0)),
                created_by=created_by,
            )
            db.add(product)
            db.flush()

            image_filename = row.get("照片檔名", "")
            if image_filename:
                entry_name = _find_zip_entry(zf, image_filename)
                if entry_name is None:
                    errors.append(
                        {"row": index, "message": f"照片「{image_filename}」在 ZIP 裡找不到,商品已建立但無照片"}
                    )
                else:
                    saved = _save_image_from_zip(zf, entry_name, "products", product.id)
                    if saved:
                        storage_key, thumbnail_key = saved
                        db.add(
                            ProductImage(
                                product_id=product.id,
                                storage_key=storage_key,
                                thumbnail_key=thumbnail_key,
                                is_primary=True,
                                sort_order=0,
                            )
                        )

            db.commit()
            created += 1
        except RowError as exc:
            db.rollback()
            errors.append({"row": index, "message": f"{exc},已略過此列"})
        except Exception as exc:  # noqa: BLE001 - one bad row must not sink the batch
            db.rollback()
            errors.append({"row": index, "message": f"發生未預期的錯誤,已略過此列:{exc}"})

    return BulkImportResult(created=created, errors=errors)


def import_materials(
    db: Session, csv_bytes: bytes, zip_bytes: bytes | None, created_by: int
) -> BulkImportResult:
    rows = _read_csv_rows(csv_bytes)
    zf = _open_zip(zip_bytes)

    created = 0
    errors: list[dict] = []

    for index, row in enumerate(rows, start=2):
        try:
            name = row.get("名稱", "")
            if not name:
                raise RowError("缺少「名稱」")
            unit_cost = _parse_float(row.get("成本", ""), "成本")

            unit_label = row.get("單位", "")
            unit = UNIT_LABELS_TO_CODE.get(unit_label, "yard")

            material = Material(
                name=name,
                unit=unit,
                unit_cost=unit_cost,
                price_addon=_parse_float(row.get("加價", ""), "加價", default=0),
                quantity_on_hand=_parse_float(row.get("庫存量", ""), "庫存量", default=1),
                origin=row.get("產地") or "韓國",
                supplier=row.get("供應商") or None,
                notes=row.get("備註") or None,
                status="active",
                created_by=created_by,
            )
            db.add(material)
            db.flush()

            image_filename = row.get("照片檔名", "")
            if image_filename:
                entry_name = _find_zip_entry(zf, image_filename)
                if entry_name is None:
                    errors.append(
                        {"row": index, "message": f"照片「{image_filename}」在 ZIP 裡找不到,布料已建立但無照片"}
                    )
                else:
                    saved = _save_image_from_zip(zf, entry_name, "materials", material.id)
                    if saved:
                        storage_key, thumbnail_key = saved
                        db.add(
                            MaterialImage(
                                material_id=material.id,
                                storage_key=storage_key,
                                thumbnail_key=thumbnail_key,
                                is_primary=True,
                                sort_order=0,
                                image_type="fabric",
                            )
                        )

            db.commit()
            created += 1
        except RowError as exc:
            db.rollback()
            errors.append({"row": index, "message": f"{exc},已略過此列"})
        except Exception as exc:  # noqa: BLE001 - one bad row must not sink the batch
            db.rollback()
            errors.append({"row": index, "message": f"發生未預期的錯誤,已略過此列:{exc}"})

    return BulkImportResult(created=created, errors=errors)
