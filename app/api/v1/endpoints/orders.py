from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate, OrderStatusUpdate
from app.models.models import User, OrderStatus
import uuid

router = APIRouter(prefix="/orders", tags=["Orders"])


def _serialize_order(order) -> dict:
    """Serialize a full order object (SQLAlchemy) to a plain dict."""
    return {
        "id": str(order.id),
        "restaurant_id": str(order.restaurant_id),
        "restaurant_name": order.restaurant.name,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": order.payment_method,
        "subtotal": order.subtotal,
        "delivery_fee": order.delivery_fee,
        "tax": order.tax,
        "discount": order.discount,
        "total_price": order.total_price,
        "special_instructions": order.special_instructions,
        "estimated_delivery_time": order.estimated_delivery_time,
        "items": [
            {
                "id": str(i.id),
                "menu_item_id": str(i.menu_item_id),
                "menu_item_name": i.menu_item.name,
                "quantity": i.quantity,
                "unit_price": i.unit_price,
                "total_price": i.total_price,
                "special_instructions": i.special_instructions,
            }
            for i in order.items
        ],
        "tracking": [
            {
                "id": str(t.id),
                "status": t.status,
                "note": t.note,
                "created_at": t.created_at.isoformat(),
            }
            for t in order.tracking
        ],
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


def _serialize_order_list(order) -> dict:
    """Serialize a lightweight order summary."""
    return {
        "id": str(order.id),
        "restaurant_name": order.restaurant.name,
        "status": order.status,
        "payment_status": order.payment_status,
        "total_price": order.total_price,
        "item_count": len(order.items),
        "created_at": order.created_at.isoformat(),
    }


@router.post("", status_code=201)
def create_order(
    data: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Place a new order from cart or explicit item list."""
    return OrderService(db).create_order(current_user, data)


@router.get("")
def list_my_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated list of the current user's orders."""
    orders, total = OrderService(db).get_user_orders(current_user, skip, limit)
    return {
        "items": [_serialize_order_list(o) for o in orders],
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    }


@router.get("/restaurant/{restaurant_id}")
def get_restaurant_orders(
    restaurant_id: str,
    status: Optional[OrderStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get orders for a specific restaurant (owner or admin only)."""
    orders = OrderService(db).get_restaurant_orders(restaurant_id, current_user, status, skip, limit)
    return {"items": [_serialize_order_list(o) for o in orders], "count": len(orders)}


@router.get("/{order_id}")
def get_order(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full order details including items and tracking history."""
    order_data = OrderService(db).get_order(order_id, current_user)
    # get_order already returns a dict from _serialize_order in the service
    # but we need to handle UUIDs/datetimes — convert any remaining non-serializable values
    return order_data


@router.patch("/{order_id}/status")
def update_order_status(
    order_id: str,
    data: OrderStatusUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update order status (restaurant owner/admin, or customer cancel)."""
    return OrderService(db).update_order_status(order_id, current_user, data)