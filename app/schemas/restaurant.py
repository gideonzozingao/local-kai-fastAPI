from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


# ─────────────────────────── Address ────────────────────────────

class AddressBase(BaseModel):
    label: str = "Home"
    street: str
    city: str
    state: str
    zip_code: str
    country: str = "US"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: bool = False


class AddressCreate(AddressBase):
    pass


class AddressResponse(AddressBase):
    id: UUID
    user_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────── Restaurant ────────────────────────────

class RestaurantBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    address: str
    city: str
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    cuisine_type: Optional[str] = None
    delivery_fee: float = Field(0.0, ge=0)
    min_order_amount: float = Field(0.0, ge=0)
    avg_delivery_time: int = Field(30, ge=5, le=120)


class RestaurantCreate(RestaurantBase):
    pass


class RestaurantUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    cuisine_type: Optional[str] = None
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    delivery_fee: Optional[float] = Field(None, ge=0)
    min_order_amount: Optional[float] = Field(None, ge=0)
    avg_delivery_time: Optional[int] = Field(None, ge=5, le=120)
    is_open: Optional[bool] = None


class RestaurantResponse(RestaurantBase):
    id: UUID
    owner_id: UUID
    logo_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    rating: float
    total_reviews: int
    is_active: bool
    is_open: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RestaurantListResponse(BaseModel):
    id: UUID
    name: str
    cuisine_type: Optional[str]
    rating: float
    total_reviews: int
    delivery_fee: float
    min_order_amount: float
    avg_delivery_time: int
    is_open: bool
    logo_url: Optional[str] = None

    class Config:
        from_attributes = True


# ─────────────────────────── Menu Category ────────────────────────────

class MenuCategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    display_order: int = 0


class MenuCategoryCreate(MenuCategoryBase):
    restaurant_id: UUID


class MenuCategoryResponse(MenuCategoryBase):
    id: UUID
    restaurant_id: UUID
    is_active: bool

    class Config:
        from_attributes = True


# ─────────────────────────── Menu Item ────────────────────────────

class MenuItemBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    image_url: Optional[str] = None
    is_available: bool = True
    is_vegetarian: bool = False
    is_vegan: bool = False
    calories: Optional[int] = None
    preparation_time: int = Field(15, ge=1)
    category_id: Optional[UUID] = None


class MenuItemCreate(MenuItemBase):
    restaurant_id: UUID


class MenuItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    image_url: Optional[str] = None
    is_available: Optional[bool] = None
    is_vegetarian: Optional[bool] = None
    is_vegan: Optional[bool] = None
    calories: Optional[int] = None
    preparation_time: Optional[int] = None
    category_id: Optional[UUID] = None


class MenuItemResponse(MenuItemBase):
    id: UUID
    restaurant_id: UUID

    class Config:
        from_attributes = True


class MenuResponse(BaseModel):
    restaurant: RestaurantResponse
    categories: List[MenuCategoryResponse]
    items: List[MenuItemResponse]
