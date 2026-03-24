from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.models import Restaurant, MenuItem, MenuCategory


class RestaurantRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, restaurant_id: UUID) -> Optional[Restaurant]:
        return self.db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    def get_by_owner(self, owner_id: UUID) -> Optional[Restaurant]:
        return self.db.query(Restaurant).filter(Restaurant.owner_id == owner_id).first()

    def get_all(self, skip: int = 0, limit: int = 20, city: Optional[str] = None,
                cuisine_type: Optional[str] = None, search: Optional[str] = None,
                is_open: Optional[bool] = None) -> List[Restaurant]:
        query = self.db.query(Restaurant).filter(Restaurant.is_active == True)

        if city:
            query = query.filter(Restaurant.city.ilike(f"%{city}%"))
        if cuisine_type:
            query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
        if search:
            query = query.filter(
                or_(
                    Restaurant.name.ilike(f"%{search}%"),
                    Restaurant.cuisine_type.ilike(f"%{search}%"),
                )
            )
        if is_open is not None:
            query = query.filter(Restaurant.is_open == is_open)

        return query.offset(skip).limit(limit).all()

    def count(self, city: Optional[str] = None, cuisine_type: Optional[str] = None) -> int:
        query = self.db.query(Restaurant).filter(Restaurant.is_active == True)
        if city:
            query = query.filter(Restaurant.city.ilike(f"%{city}%"))
        if cuisine_type:
            query = query.filter(Restaurant.cuisine_type.ilike(f"%{cuisine_type}%"))
        return query.count()

    def create(self, owner_id: UUID, **kwargs) -> Restaurant:
        restaurant = Restaurant(owner_id=owner_id, **kwargs)
        self.db.add(restaurant)
        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant

    def update(self, restaurant: Restaurant, **kwargs) -> Restaurant:
        for key, value in kwargs.items():
            if value is not None:
                setattr(restaurant, key, value)
        self.db.commit()
        self.db.refresh(restaurant)
        return restaurant

    def update_rating(self, restaurant: Restaurant, rating: float, total_reviews: int) -> Restaurant:
        restaurant.rating = rating
        restaurant.total_reviews = total_reviews
        self.db.commit()
        return restaurant

    def delete(self, restaurant: Restaurant) -> None:
        restaurant.is_active = False
        self.db.commit()


class MenuRepository:
    def __init__(self, db: Session):
        self.db = db

    # ─── Categories ───

    def get_category_by_id(self, category_id: UUID) -> Optional[MenuCategory]:
        return self.db.query(MenuCategory).filter(MenuCategory.id == category_id).first()

    def get_categories_by_restaurant(self, restaurant_id: UUID) -> List[MenuCategory]:
        return (
            self.db.query(MenuCategory)
            .filter(MenuCategory.restaurant_id == restaurant_id, MenuCategory.is_active == True)
            .order_by(MenuCategory.display_order)
            .all()
        )

    def create_category(self, restaurant_id: UUID, **kwargs) -> MenuCategory:
        category = MenuCategory(restaurant_id=restaurant_id, **kwargs)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category

    # ─── Menu Items ───

    def get_item_by_id(self, item_id: UUID) -> Optional[MenuItem]:
        return self.db.query(MenuItem).filter(MenuItem.id == item_id).first()

    def get_items_by_restaurant(self, restaurant_id: UUID,
                                category_id: Optional[UUID] = None,
                                available_only: bool = True) -> List[MenuItem]:
        query = self.db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id)
        if category_id:
            query = query.filter(MenuItem.category_id == category_id)
        if available_only:
            query = query.filter(MenuItem.is_available == True)
        return query.all()

    def create_item(self, restaurant_id: UUID, **kwargs) -> MenuItem:
        item = MenuItem(restaurant_id=restaurant_id, **kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, item: MenuItem, **kwargs) -> MenuItem:
        for key, value in kwargs.items():
            if value is not None:
                setattr(item, key, value)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_item(self, item: MenuItem) -> None:
        self.db.delete(item)
        self.db.commit()
