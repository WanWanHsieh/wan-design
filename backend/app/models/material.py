from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class Material(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str | None] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit: Mapped[str] = mapped_column(String(20), nullable=False, default="yard")  # meter|yard|kg|piece
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    price_addon: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    quantity_on_hand: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=1)
    origin: Mapped[str | None] = mapped_column(String(100), default="韓國")
    supplier: Mapped[str | None] = mapped_column(String(255))
    notes: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)  # active|discontinued
    custom_attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"))

    images: Mapped[list["MaterialImage"]] = relationship(
        back_populates="material", cascade="all, delete-orphan", order_by="MaterialImage.sort_order"
    )


class MaterialImage(Base, TimestampMixin):
    __tablename__ = "material_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    material_id: Mapped[int] = mapped_column(
        ForeignKey("materials.id", ondelete="CASCADE"), nullable=False
    )
    storage_key: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_key: Mapped[str | None] = mapped_column(String(500))
    alt_text: Mapped[str | None] = mapped_column(String(255))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    image_type: Mapped[str] = mapped_column(String(20), default="fabric", nullable=False)  # fabric|showcase

    material: Mapped["Material"] = relationship(back_populates="images")
