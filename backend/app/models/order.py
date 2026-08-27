from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    real_name: Mapped[str | None] = mapped_column(String(100))
    contact_source: Mapped[str | None] = mapped_column(String(20))  # ig|line|fb
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_method: Mapped[str] = mapped_column(String(20), nullable=False)  # family_mart|seven_eleven|address
    shipping_store_code: Mapped[str | None] = mapped_column(String(50))
    shipping_address: Mapped[str | None] = mapped_column(String(255))
    expected_delivery_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    adjustment_amount: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)
    adjustment_note: Mapped[str | None] = mapped_column(Text)

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan"
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)
    variant_id: Mapped[int | None] = mapped_column(
        ForeignKey("product_variants.id", ondelete="SET NULL")
    )
    variant_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    material_id: Mapped[int | None] = mapped_column(ForeignKey("materials.id", ondelete="SET NULL"))
    material_name_snapshot: Mapped[str | None] = mapped_column(String(255))
    unit_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_note: Mapped[str | None] = mapped_column(Text)
    extra_charge: Mapped[float] = mapped_column(Numeric(12, 2), default=0, nullable=False)

    order: Mapped["Order"] = relationship(back_populates="items")
    material: Mapped["Material | None"] = relationship()  # noqa: F821
    product: Mapped["Product | None"] = relationship()  # noqa: F821
    variant: Mapped["ProductVariant | None"] = relationship()  # noqa: F821

    def _primary_fabric_image(self):
        if not self.material:
            return None
        fabric_images = [img for img in self.material.images if img.image_type == "fabric"]
        return next((img for img in fabric_images if img.is_primary), fabric_images[0] if fabric_images else None)

    def _primary_product_image(self):
        if not self.product or not self.product.images:
            return None
        return next(
            (img for img in self.product.images if img.is_primary), self.product.images[0]
        )

    @property
    def material_thumbnail(self) -> str | None:
        image = self._primary_fabric_image()
        if image is None:
            return None
        return image.thumbnail_key or image.storage_key

    @property
    def material_image(self) -> str | None:
        image = self._primary_fabric_image()
        return image.storage_key if image else None

    @property
    def product_thumbnail(self) -> str | None:
        image = self._primary_product_image()
        if image is None:
            return None
        return image.thumbnail_key or image.storage_key

    @property
    def product_image(self) -> str | None:
        image = self._primary_product_image()
        return image.storage_key if image else None
