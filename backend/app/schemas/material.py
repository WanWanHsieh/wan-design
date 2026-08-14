from pydantic import BaseModel, Field


class MaterialImageOut(BaseModel):
    id: int
    storage_key: str
    thumbnail_key: str | None
    alt_text: str | None
    sort_order: int
    is_primary: bool
    image_type: str

    class Config:
        from_attributes = True


class MaterialBase(BaseModel):
    code: str | None = None
    name: str = Field(min_length=1, max_length=255)
    unit: str = "yard"
    unit_cost: float
    price_addon: float = 0
    quantity_on_hand: float = 1
    origin: str | None = "韓國"
    fabric_type: str | None = None
    supplier: str | None = None
    notes: str | None = None
    status: str = "active"
    custom_attributes: dict = Field(default_factory=dict)


class MaterialCreate(MaterialBase):
    pass


class MaterialUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    unit: str | None = None
    unit_cost: float | None = None
    price_addon: float | None = None
    quantity_on_hand: float | None = None
    origin: str | None = None
    fabric_type: str | None = None
    supplier: str | None = None
    notes: str | None = None
    status: str | None = None
    custom_attributes: dict | None = None


class MaterialOut(MaterialBase):
    id: int
    images: list[MaterialImageOut] = []

    class Config:
        from_attributes = True


class MaterialPageOut(BaseModel):
    items: list[MaterialOut]
    total: int
    page: int
    page_size: int


class MaterialPublicOut(BaseModel):
    """Customer-facing view: name, photos, and the customer-facing price add-on only — no cost/supplier/stock data."""

    id: int
    name: str
    price_addon: float
    origin: str | None = None
    fabric_type: str | None = None
    images: list[MaterialImageOut] = []

    class Config:
        from_attributes = True
