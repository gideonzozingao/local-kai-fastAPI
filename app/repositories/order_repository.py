from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from app.models.models import Order, OrderItem, CartItem, OrderTracking, OrderStatus


class OrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, order_id: UUID) -> Optional[Order]:
        return (
            self.db.query(Order)
            .options(
                joinedload(Order.items).joinedload(OrderItem.menu_item),
                joinedload(Order.restaurant),
                joinedload(Order.tracking),
                joinedload(Order.delivery_address),
            )
            .filter(Order.id == order_id)
            .first()
        )

    def get_user_orders(self, user_id: UUID, skip: int = 0, limit: int = 20) -> List[Order]:
        return (
            self.db.query(Order)
            .options(
                joinedload(Order.items),
                joinedload(Order.restaurant),
            )
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_restaurant_orders(self, restaurant_id: UUID,
                               status: Optional[OrderStatus] = None,
                               skip: int = 0, limit: int = 20) -> List[Order]:
        query = (
            self.db.query(Order)
            .options(joinedload(Order.items).joinedload(OrderItem.menu_item))
            .filter(Order.restaurant_id == restaurant_id)
        )
        if status:
            query = query.filter(Order.status == status)
        return query.order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    def count_user_orders(self, user_id: UUID) -> int:
        return self.db.query(Order).filter(Order.user_id == user_id).count()

    def create(self, user_id: UUID, restaurant_id: UUID, **kwargs) -> Order:
        order = Order(user_id=user_id, restaurant_id=restaurant_id, **kwargs)
        self.db.add(order)
        self.db.flush()  # Get ID without committing
        return order

    def add_item(self, order_id: UUID, menu_item_id: UUID, quantity: int,
                 unit_price: float, special_instructions: Optional[str] = None) -> OrderItem:
        item = OrderItem(
            order_id=order_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            unit_price=unit_price,
            total_price=unit_price * quantity,
            special_instructions=special_instructions,
        )
        self.db.add(item)
        return item

    def update_status(self, order: Order, status: OrderStatus, note: Optional[str] = None) -> Order:
        order.status = status
        tracking = OrderTracking(order_id=order.id, status=status, note=note)
        self.db.add(tracking)
        self.db.commit()
        self.db.refresh(order)
        return order

    def update(self, order: Order, **kwargs) -> Order:
        for key, value in kwargs.items():
            if value is not None:
                setattr(order, key, value)
        self.db.commit()
        self.db.refresh(order)
        return order

    def commit(self):
        self.db.commit()


class CartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_cart(self, user_id: UUID) -> List[CartItem]:
        return (
            self.db.query(CartItem)
            .options(joinedload(CartItem.menu_item))
            .filter(CartItem.user_id == user_id)
            .all()
        )

    def get_cart_item(self, user_id: UUID, item_id: UUID) -> Optional[CartItem]:
        return self.db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.id == item_id
        ).first()

    def get_cart_item_by_menu_item(self, user_id: UUID, menu_item_id: UUID) -> Optional[CartItem]:
        return self.db.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.menu_item_id == menu_item_id,
        ).first()

    def add_or_update(self, user_id: UUID, menu_item_id: UUID,
                      quantity: int, special_instructions: Optional[str] = None) -> CartItem:
        existing = self.get_cart_item_by_menu_item(user_id, menu_item_id)
        if existing:
            existing.quantity += quantity
            if special_instructions:
                existing.special_instructions = special_instructions
            self.db.commit()
            self.db.refresh(existing)
            return existing

        item = CartItem(
            user_id=user_id,
            menu_item_id=menu_item_id,
            quantity=quantity,
            special_instructions=special_instructions,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def update_item(self, cart_item: CartItem, quantity: int,
                    special_instructions: Optional[str] = None) -> CartItem:
        cart_item.quantity = quantity
        if special_instructions is not None:
            cart_item.special_instructions = special_instructions
        self.db.commit()
        self.db.refresh(cart_item)
        return cart_item

    def remove_item(self, cart_item: CartItem) -> None:
        self.db.delete(cart_item)
        self.db.commit()

    def clear_cart(self, user_id: UUID) -> None:
        self.db.query(CartItem).filter(CartItem.user_id == user_id).delete()
        self.db.commit()
