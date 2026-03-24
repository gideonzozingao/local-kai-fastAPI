from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime
from app.models.models import OrderStatus, PaymentStatus, PaymentMethod
from app.schemas.restaurant import MenuItemResponse


# ─────────────────────────── Cart ────────────────────────────

class CartItemAdd(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(..., ge=1, le=50)
    special_instructions: Optional[str] = None


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=50)
    special_instructions: Optional[str] = None


class CartItemResponse(BaseModel):
    id: UUID
    menu_item: MenuItemResponse
    quantity: int
    special_instructions: Optional[str] = None
    item_total: float  # computed field

    class Config:
        from_attributes = True


class CartResponse(BaseModel):
    items: List[CartItemResponse]
    subtotal: float
    item_count: int


# ─────────────────────────── Order ────────────────────────────

class OrderItemCreate(BaseModel):
    menu_item_id: UUID
    quantity: int = Field(..., ge=1)
    special_instructions: Optional[str] = None


class OrderCreate(BaseModel):
    restaurant_id: UUID
    delivery_address_id: Optional[UUID] = None
    payment_method: PaymentMethod = PaymentMethod.CASH
    special_instructions: Optional[str] = None
    # If True, pull from cart; if False, use items directly
    from_cart: bool = True
    items: Optional[List[OrderItemCreate]] = None  # used when from_cart=False


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    note: Optional[str] = None


class OrderItemResponse(BaseModel):
    id: UUID
    menu_item_id: UUID
    menu_item_name: str
    quantity: int
    unit_price: float
    total_price: float
    special_instructions: Optional[str] = None

    class Config:
        from_attributes = True


class OrderTrackingResponse(BaseModel):
    id: UUID
    status: OrderStatus
    note: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    restaurant_id: UUID
    restaurant_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    payment_method: PaymentMethod
    subtotal: float
    delivery_fee: float
    tax: float
    discount: float
    total_price: float
    special_instructions: Optional[str] = None
    estimated_delivery_time: Optional[int] = None
    items: List[OrderItemResponse]
    tracking: List[OrderTrackingResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    id: UUID
    restaurant_name: str
    status: OrderStatus
    payment_status: PaymentStatus
    total_price: float
    item_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── Payment ────────────────────────────

class PaymentIntentResponse(BaseModel):
    client_secret: str
    payment_intent_id: str
    amount: float


class PaymentConfirmRequest(BaseModel):
    order_id: UUID
    payment_intent_id: str


# ─────────────────────────── Review ────────────────────────────

class ReviewCreate(BaseModel):
    restaurant_id: UUID
    order_id: Optional[UUID] = None
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: UUID
    user_id: UUID
    restaurant_id: UUID
    rating: int
    comment: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── Common ────────────────────────────

class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    per_page: int
    total_pages: int


class MessageResponse(BaseModel):
    message: str
    success: bool = True
