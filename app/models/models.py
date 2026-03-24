import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import (
    Column, String, Boolean, Float, Integer,
    ForeignKey, Text, Enum, DateTime
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.session import Base


# ─────────────────────────── Enums ────────────────────────────

class UserRole(str, PyEnum):
    CUSTOMER = "customer"
    ADMIN = "admin"
    RESTAURANT_OWNER = "restaurant_owner"
    DELIVERY_AGENT = "delivery_agent"


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    READY_FOR_PICKUP = "ready_for_pickup"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, PyEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class PaymentMethod(str, PyEnum):
    CASH = "cash"
    CARD = "card"
    STRIPE = "stripe"


# ─────────────────────────── User ────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True)
    full_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    profile_picture = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    addresses = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user")
    restaurant = relationship("Restaurant", back_populates="owner", uselist=False)


# ─────────────────────────── Address ────────────────────────────

class Address(Base):
    __tablename__ = "addresses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    label = Column(String(100), default="Home")  # Home, Work, Other
    street = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), default="US")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="addresses")


# ─────────────────────────── Restaurant ────────────────────────────

class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    logo_url = Column(String(500), nullable=True)
    cover_image_url = Column(String(500), nullable=True)
    cuisine_type = Column(String(100), nullable=True)
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_open = Column(Boolean, default=True)
    delivery_fee = Column(Float, default=0.0)
    min_order_amount = Column(Float, default=0.0)
    avg_delivery_time = Column(Integer, default=30)  # minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="restaurant")
    menu_categories = relationship("MenuCategory", back_populates="restaurant", cascade="all, delete-orphan")
    menu_items = relationship("MenuItem", back_populates="restaurant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="restaurant")


# ─────────────────────────── Menu Category ────────────────────────────

class MenuCategory(Base):
    __tablename__ = "menu_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_categories")
    menu_items = relationship("MenuItem", back_populates="category")


# ─────────────────────────── Menu Item ────────────────────────────

class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("menu_categories.id"), nullable=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    image_url = Column(String(500), nullable=True)
    is_available = Column(Boolean, default=True)
    is_vegetarian = Column(Boolean, default=False)
    is_vegan = Column(Boolean, default=False)
    calories = Column(Integer, nullable=True)
    preparation_time = Column(Integer, default=15)  # minutes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    restaurant = relationship("Restaurant", back_populates="menu_items")
    category = relationship("MenuCategory", back_populates="menu_items")
    cart_items = relationship("CartItem", back_populates="menu_item")
    order_items = relationship("OrderItem", back_populates="menu_item")


# ─────────────────────────── Cart ────────────────────────────

class CartItem(Base):
    __tablename__ = "cart_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    special_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cart_items")
    menu_item = relationship("MenuItem", back_populates="cart_items")


# ─────────────────────────── Order ────────────────────────────

class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    delivery_address_id = Column(UUID(as_uuid=True), ForeignKey("addresses.id"), nullable=True)

    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.UNPAID, nullable=False)
    payment_method = Column(Enum(PaymentMethod), default=PaymentMethod.CASH, nullable=False)

    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0.0)
    tax = Column(Float, default=0.0)
    discount = Column(Float, default=0.0)
    total_price = Column(Float, nullable=False)

    special_instructions = Column(Text, nullable=True)
    estimated_delivery_time = Column(Integer, nullable=True)  # minutes
    stripe_payment_intent_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="orders")
    restaurant = relationship("Restaurant", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    delivery_address = relationship("Address")
    tracking = relationship("OrderTracking", back_populates="order", cascade="all, delete-orphan")


# ─────────────────────────── Order Item ────────────────────────────

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    menu_item_id = Column(UUID(as_uuid=True), ForeignKey("menu_items.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)  # Price at time of order
    total_price = Column(Float, nullable=False)
    special_instructions = Column(Text, nullable=True)

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")


# ─────────────────────────── Order Tracking ────────────────────────────

class OrderTracking(Base):
    __tablename__ = "order_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    status = Column(Enum(OrderStatus), nullable=False)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="tracking")


# ─────────────────────────── Review ────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    restaurant_id = Column(UUID(as_uuid=True), ForeignKey("restaurants.id"), nullable=False)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=True)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")
    restaurant = relationship("Restaurant")
    order = relationship("Order")
