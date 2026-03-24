from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.restaurant_repository import RestaurantRepository, MenuRepository
from app.core.exceptions import NotFoundException, ForbiddenException, ConflictException
from app.models.models import User, UserRole, Restaurant, MenuItem
from app.schemas.restaurant import (
    RestaurantCreate, RestaurantUpdate, MenuCategoryCreate,
    MenuItemCreate, MenuItemUpdate, MenuResponse,
)


class RestaurantService:
    def __init__(self, db: Session):
        self.db = db
        self.restaurant_repo = RestaurantRepository(db)

    def get_all(self, skip: int = 0, limit: int = 20, city: Optional[str] = None,
                cuisine_type: Optional[str] = None, search: Optional[str] = None,
                is_open: Optional[bool] = None):
        restaurants = self.restaurant_repo.get_all(skip, limit, city, cuisine_type, search, is_open)
        total = self.restaurant_repo.count(city, cuisine_type)
        return restaurants, total

    def get_by_id(self, restaurant_id: UUID) -> Restaurant:
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant or not restaurant.is_active:
            raise NotFoundException("Restaurant")
        return restaurant

    def create(self, current_user: User, data: RestaurantCreate) -> Restaurant:
        # Only restaurant owners can create, and they can only have one
        if current_user.role == UserRole.RESTAURANT_OWNER:
            existing = self.restaurant_repo.get_by_owner(current_user.id)
            if existing:
                raise ConflictException("You already have a registered restaurant")

        restaurant = self.restaurant_repo.create(
            owner_id=current_user.id,
            name=data.name,
            description=data.description,
            address=data.address,
            city=data.city,
            phone=data.phone,
            email=data.email,
            cuisine_type=data.cuisine_type,
            delivery_fee=data.delivery_fee,
            min_order_amount=data.min_order_amount,
            avg_delivery_time=data.avg_delivery_time,
        )

        # Promote user to restaurant owner if they're a customer
        if current_user.role == UserRole.CUSTOMER:
            current_user.role = UserRole.RESTAURANT_OWNER
            self.db.commit()

        return restaurant

    def update(self, restaurant_id: UUID, current_user: User, data: RestaurantUpdate) -> Restaurant:
        restaurant = self.get_by_id(restaurant_id)
        self._check_ownership(restaurant, current_user)

        update_data = data.model_dump(exclude_none=True)
        return self.restaurant_repo.update(restaurant, **update_data)

    def delete(self, restaurant_id: UUID, current_user: User) -> dict:
        restaurant = self.get_by_id(restaurant_id)
        self._check_ownership(restaurant, current_user)
        self.restaurant_repo.delete(restaurant)
        return {"message": "Restaurant deactivated successfully"}

    def _check_ownership(self, restaurant: Restaurant, user: User):
        if user.role != UserRole.ADMIN and str(restaurant.owner_id) != str(user.id):
            raise ForbiddenException("You do not own this restaurant")


class MenuService:
    def __init__(self, db: Session):
        self.db = db
        self.restaurant_repo = RestaurantRepository(db)
        self.menu_repo = MenuRepository(db)

    def get_menu(self, restaurant_id: UUID) -> dict:
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant or not restaurant.is_active:
            raise NotFoundException("Restaurant")

        categories = self.menu_repo.get_categories_by_restaurant(restaurant_id)
        items = self.menu_repo.get_items_by_restaurant(restaurant_id)

        return {
            "restaurant": restaurant,
            "categories": categories,
            "items": items,
        }

    def create_category(self, current_user: User, data: MenuCategoryCreate) -> dict:
        restaurant = self.restaurant_repo.get_by_id(data.restaurant_id)
        if not restaurant:
            raise NotFoundException("Restaurant")
        self._check_ownership(restaurant, current_user)

        return self.menu_repo.create_category(
            restaurant_id=data.restaurant_id,
            name=data.name,
            description=data.description,
            display_order=data.display_order,
        )

    def create_menu_item(self, current_user: User, data: MenuItemCreate) -> MenuItem:
        restaurant = self.restaurant_repo.get_by_id(data.restaurant_id)
        if not restaurant:
            raise NotFoundException("Restaurant")
        self._check_ownership(restaurant, current_user)

        return self.menu_repo.create_item(
            restaurant_id=data.restaurant_id,
            name=data.name,
            description=data.description,
            price=data.price,
            image_url=data.image_url,
            is_available=data.is_available,
            is_vegetarian=data.is_vegetarian,
            is_vegan=data.is_vegan,
            calories=data.calories,
            preparation_time=data.preparation_time,
            category_id=data.category_id,
        )

    def update_menu_item(self, item_id: UUID, current_user: User, data: MenuItemUpdate) -> MenuItem:
        item = self.menu_repo.get_item_by_id(item_id)
        if not item:
            raise NotFoundException("Menu item")

        restaurant = self.restaurant_repo.get_by_id(item.restaurant_id)
        self._check_ownership(restaurant, current_user)

        update_data = data.model_dump(exclude_none=True)
        return self.menu_repo.update_item(item, **update_data)

    def delete_menu_item(self, item_id: UUID, current_user: User) -> dict:
        item = self.menu_repo.get_item_by_id(item_id)
        if not item:
            raise NotFoundException("Menu item")

        restaurant = self.restaurant_repo.get_by_id(item.restaurant_id)
        self._check_ownership(restaurant, current_user)

        self.menu_repo.delete_item(item)
        return {"message": "Menu item deleted"}

    def _check_ownership(self, restaurant: Restaurant, user: User):
        if user.role != UserRole.ADMIN and str(restaurant.owner_id) != str(user.id):
            raise ForbiddenException("You do not own this restaurant")
