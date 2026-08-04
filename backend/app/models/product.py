from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, SoftDeleteMixin, TimestampMixin


class Product(Base, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    custom_attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    track_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id"))

    category: Mapped["Category | None"] = relationship()  # noqa: F821
    images: Mapped[list["ProductImage"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan", order_by="ProductImage.sort_order"
    )
    attribute_values: Mapped[list["ProductAttributeValue"]] = relationship(  # noqa: F821
        back_populates="product", cascade="all, delete-orphan"
    )
