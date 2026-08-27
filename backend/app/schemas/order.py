from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

SHIPPING_METHODS = {"family_mart", "seven_eleven", "address"}
ORDER_STATUSES = {"pending", "shipped", "completed", "cancelled"}
CONTACT_SOURCES = {"ig", "line", "fb"}


class OrderItemIn(BaseModel):
    product_id: int
    variant_id: int | None = None
    material_id: int | None = None
    quantity: int = Field(gt=0)


class AdminOrderItemIn(OrderItemIn):
    custom_note: str | None = None
    extra_charge: float = 0


class OrderItemOut(BaseModel):
    id: int
    product_id: int | None
    product_name_snapshot: str
    product_thumbnail: str | None = None
    product_image: str | None = None
    variant_id: int | None = None
    variant_name_snapshot: str | None = None
    material_id: int | None
    material_name_snapshot: str | None
    material_thumbnail: str | None = None
    material_image: str | None = None
    unit_price: float
    quantity: int
    subtotal: float
    is_completed: bool
    custom_note: str | None = None
    extra_charge: float = 0

    class Config:
        from_attributes = True


class OrderItemCompletionUpdate(BaseModel):
    is_completed: bool


def check_shipping_fields(
    shipping_method: str, shipping_store_code: str | None, shipping_address: str | None
) -> None:
    if shipping_method not in SHIPPING_METHODS:
        raise ValueError("Invalid shipping_method")
    if shipping_method in {"family_mart", "seven_eleven"}:
        if not shipping_store_code:
            raise ValueError("shipping_store_code is required for this shipping method")
    elif shipping_method == "address":
        if not shipping_address:
            raise ValueError("shipping_address is required for address shipping")


class OrderCreate(BaseModel):
    real_name: str = Field(min_length=1, max_length=100)
    contact_source: str
    customer_name: str = Field(min_length=1, max_length=100)
    phone: str = Field(min_length=1, max_length=20)
    shipping_method: str
    shipping_store_code: str | None = None
    shipping_address: str | None = None
    expected_delivery_date: date
    notes: str | None = None
    items: list[OrderItemIn] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_shipping_fields(self) -> "OrderCreate":
        check_shipping_fields(self.shipping_method, self.shipping_store_code, self.shipping_address)
        if self.contact_source not in CONTACT_SOURCES:
            raise ValueError("Invalid contact_source")
        return self


class OrderUpdate(BaseModel):
    real_name: str | None = Field(default=None, min_length=1, max_length=100)
    contact_source: str | None = None
    customer_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, min_length=1, max_length=20)
    shipping_method: str | None = None
    shipping_store_code: str | None = None
    shipping_address: str | None = None
    expected_delivery_date: date | None = None
    status: str | None = None
    notes: str | None = None
    adjustment_amount: float | None = None
    adjustment_note: str | None = None
    items: list[AdminOrderItemIn] | None = Field(default=None, min_length=1)


class OrderOut(BaseModel):
    id: int
    order_no: str
    real_name: str | None = None
    contact_source: str | None = None
    customer_name: str
    phone: str
    shipping_method: str
    shipping_store_code: str | None
    shipping_address: str | None
    expected_delivery_date: date
    total_amount: float
    status: str
    notes: str | None
    adjustment_amount: float = 0
    adjustment_note: str | None = None
    created_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True


class OrderListItemOut(BaseModel):
    id: int
    order_no: str
    real_name: str | None = None
    contact_source: str | None = None
    customer_name: str
    phone: str
    shipping_method: str
    shipping_store_code: str | None
    shipping_address: str | None
    expected_delivery_date: date
    total_amount: float
    status: str
    notes: str | None
    adjustment_amount: float = 0
    adjustment_note: str | None = None
    created_at: datetime
    items: list[OrderItemOut] = []

    class Config:
        from_attributes = True
