from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.services.restaurant_service import RestaurantService, MenuService
from app.schemas.restaurant import (
    RestaurantCreate, RestaurantUpdate, RestaurantResponse, RestaurantListResponse,
    MenuCategoryCreate, MenuCategoryResponse,
    MenuItemCreate, MenuItemUpdate, MenuItemResponse,
)
from app.models.models import User

router = APIRouter(prefix="/restaurants", tags=["Restaurants"])


# ─────────────────────────── Restaurants ────────────────────────────

@router.get("")
def list_restaurants(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    city: Optional[str] = Query(None),
    cuisine_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    is_open: Optional[bool] = Query(None),
    db: Session = Depends(get_db),
):
    """List all active restaurants with optional filtering."""
    service = RestaurantService(db)
    restaurants, total = service.get_all(skip, limit, city, cuisine_type, search, is_open)
    return {
        "items": [RestaurantListResponse.model_validate(r).model_dump() for r in restaurants],
        "total": total,
        "page": skip // limit + 1,
        "per_page": limit,
    }


@router.get("/{restaurant_id}")
def get_restaurant(restaurant_id: str, db: Session = Depends(get_db)):
    """Get a restaurant by ID."""
    r = RestaurantService(db).get_by_id(restaurant_id)
    return RestaurantResponse.model_validate(r).model_dump()


@router.post("", status_code=201)
def create_restaurant(
    data: RestaurantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new restaurant."""
    r = RestaurantService(db).create(current_user, data)
    return RestaurantResponse.model_validate(r).model_dump()


@router.patch("/{restaurant_id}")
def update_restaurant(
    restaurant_id: str,
    data: RestaurantUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update restaurant details (owner or admin)."""
    r = RestaurantService(db).update(restaurant_id, current_user, data)
    return RestaurantResponse.model_validate(r).model_dump()


@router.delete("/{restaurant_id}")
def delete_restaurant(
    restaurant_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate a restaurant (owner or admin)."""
    return RestaurantService(db).delete(restaurant_id, current_user)


# ─────────────────────────── Menu ────────────────────────────

@router.get("/{restaurant_id}/menu")
def get_menu(restaurant_id: str, db: Session = Depends(get_db)):
    """Get full menu for a restaurant."""
    data = MenuService(db).get_menu(restaurant_id)
    return {
        "restaurant": RestaurantResponse.model_validate(data["restaurant"]).model_dump(),
        "categories": [MenuCategoryResponse.model_validate(c).model_dump() for c in data["categories"]],
        "items": [MenuItemResponse.model_validate(i).model_dump() for i in data["items"]],
    }


# ─────────────────────────── Menu Categories ────────────────────────────

menu_router = APIRouter(prefix="/menu", tags=["Menu"])


@menu_router.post("/categories", status_code=201)
def create_category(
    data: MenuCategoryCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new menu category (restaurant owner)."""
    c = MenuService(db).create_category(current_user, data)
    return MenuCategoryResponse.model_validate(c).model_dump()


# ─────────────────────────── Menu Items ────────────────────────────

@menu_router.post("/items", status_code=201)
def create_menu_item(
    data: MenuItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new menu item (restaurant owner)."""
    item = MenuService(db).create_menu_item(current_user, data)
    return MenuItemResponse.model_validate(item).model_dump()


@menu_router.patch("/items/{item_id}")
def update_menu_item(
    item_id: str,
    data: MenuItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a menu item (restaurant owner)."""
    item = MenuService(db).update_menu_item(item_id, current_user, data)
    return MenuItemResponse.model_validate(item).model_dump()


@menu_router.delete("/items/{item_id}")
def delete_menu_item(
    item_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a menu item (restaurant owner)."""
    return MenuService(db).delete_menu_item(item_id, current_user)