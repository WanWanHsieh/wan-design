from datetime import date

from pydantic import BaseModel, Field


class ProductImageOut(BaseModel):
    id: int
    storage_key: str
    thumbnail_key: str | None
    alt_text: str | None
    sort_order: int
    is_primary: bool
    image_type: str

    class Config:
        from_attributes = True


class AttributeValueIn(BaseModel):
    attribute_definition_id: int
    value_text: str | None = None
    value_number: float | None = None
    value_boolean: bool | None = None


class AttributeValueOut(AttributeValueIn):
    id: int

    class Config:
        from_attributes = True


class ProductVariantIn(BaseModel):
    sku: str | None = None
    name: str = Field(min_length=1, max_length=100)
    price: float
    track_stock: bool = False
    stock_quantity: int = Field(default=0, ge=0)
    sort_order: int = 0
    is_active: bool = True


class ProductVariantOut(ProductVariantIn):
    id: int

    class Config:
        from_attributes = True


class ProductBase(BaseModel):
    sku: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    slug: str = Field(min_length=1, max_length=255)
    description: str | None = None
    category_id: int | None = None
    base_price: float
    status: str = "draft"
    custom_attributes: dict = Field(default_factory=dict)
    track_stock: bool = False
    stock_quantity: int = Field(default=0, ge=0)
    requires_material: bool = True
    is_featured: bool = False
    sale_price: float | None = None
    sale_starts_at: date | None = None
    sale_ends_at: date | None = None


class ProductCreate(ProductBase):
    attribute_values: list[AttributeValueIn] = []
    variants: list[ProductVariantIn] = []


class ProductUpdate(BaseModel):
    sku: str | None = None
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    category_id: int | None = None
    base_price: float | None = None
    status: str | None = None
    custom_attributes: dict | None = None
    track_stock: bool | None = None
    stock_quantity: int | None = Field(default=None, ge=0)
    requires_material: bool | None = None
    is_featured: bool | None = None
    sale_price: float | None = None
    sale_starts_at: date | None = None
    sale_ends_at: date | None = None
    attribute_values: list[AttributeValueIn] | None = None
    variants: list[ProductVariantIn] | None = None


class ProductOut(ProductBase):
    id: int
    is_on_sale: bool = False
    effective_price: float
    has_variants: bool = False
    images: list[ProductImageOut] = []
    attribute_values: list[AttributeValueOut] = []
    variants: list[ProductVariantOut] = []

    class Config:
        from_attributes = True


class ProductListItemOut(BaseModel):
    id: int
    sku: str
    name: str
    slug: str
    base_price: float
    status: str
    category_id: int | None
    track_stock: bool
    stock_quantity: int
    is_featured: bool
    requires_material: bool = True
    sale_price: float | None = None
    sale_starts_at: date | None = None
    sale_ends_at: date | None = None
    is_on_sale: bool = False
    effective_price: float
    has_variants: bool = False
    variants: list[ProductVariantOut] = []
    primary_image: str | None = None
    primary_thumbnail: str | None = None

    class Config:
        from_attributes = True


class AttributeDefinitionOut(BaseModel):
    id: int
    category_id: int | None
    name: str
    code: str
    input_type: str
    is_required: bool
    sort_order: int

    class Config:
        from_attributes = True


class AttributeDefinitionCreate(BaseModel):
    category_id: int | None = None
    name: str
    code: str
    input_type: str
    is_required: bool = False
    sort_order: int = 0
