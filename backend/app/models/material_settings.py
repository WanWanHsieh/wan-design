from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MaterialSettings(Base):
    __tablename__ = "material_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    default_code_order: Mapped[str] = mapped_column(String(4), nullable=False, default="desc")
