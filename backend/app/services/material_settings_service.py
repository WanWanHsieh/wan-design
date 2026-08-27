from sqlalchemy.orm import Session

from app.models.material_settings import MaterialSettings
from app.schemas.material_settings import MaterialSettingsUpdate


def get_material_settings(db: Session) -> MaterialSettings:
    settings = db.query(MaterialSettings).order_by(MaterialSettings.id.asc()).first()
    if settings is None:
        settings = MaterialSettings(default_code_order="desc")
        db.add(settings)
        db.commit()
    return settings


def update_material_settings(db: Session, data: MaterialSettingsUpdate) -> MaterialSettings:
    settings = get_material_settings(db)
    settings.default_code_order = data.default_code_order
    db.commit()
    return settings
