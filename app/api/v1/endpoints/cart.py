from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.services.order_service import CartService
from app.schemas.order import CartItemAdd, CartItemUpdate, CartItemResponse, CartResponse
from app.schemas.restaurant import MenuItemResponse
from app.models.models import User

router = APIRouter(prefix="/cart", tags=["Cart"])


def _serialize_cart(data: dict) -> dict:
    """Manually serialize cart since items contain nested SQLAlchemy objects."""
    items = []
    for item in data["items"]:
        items.append({
            "id": str(item["id"]),
            "menu_item": MenuItemResponse.model_validate(item["menu_item"]).model_dump(),
            "quantity": item["quantity"],
            "special_instructions": item["special_instructions"],
            "item_total": item["item_total"],
        })
    return {
        "items": items,
        "subtotal": data["subtotal"],
        "item_count": data["item_count"],
    }


@router.get("")
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current user's cart with totals."""
    data = CartService(db).get_cart(current_user)
    return _serialize_cart(data)


@router.post("/add")
def add_to_cart(
    data: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add an item to the cart. Merges quantity if item already exists."""
    return CartService(db).add_item(current_user, data)


@router.patch("/items/{item_id}")
def update_cart_item(
    item_id: str,
    data: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update quantity or instructions for a cart item."""
    return CartService(db).update_item(current_user, item_id, data)


@router.delete("/items/{item_id}")
def remove_from_cart(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove a specific item from the cart."""
    return CartService(db).remove_item(current_user, item_id)


@router.delete("")
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Clear all items from the cart."""
    return CartService(db).clear_cart(current_user)