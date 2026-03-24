from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.repositories.order_repository import OrderRepository, CartRepository
from app.repositories.restaurant_repository import RestaurantRepository, MenuRepository
from app.core.exceptions import (
    NotFoundException, ForbiddenException, BadRequestException
)
from app.models.models import User, UserRole, OrderStatus, PaymentStatus, PaymentMethod
from app.schemas.order import CartItemAdd, CartItemUpdate, OrderCreate, OrderStatusUpdate


class CartService:
    def __init__(self, db: Session):
        self.db = db
        self.cart_repo = CartRepository(db)
        self.menu_repo = MenuRepository(db)

    def get_cart(self, user: User) -> dict:
        items = self.cart_repo.get_user_cart(user.id)
        cart_items_response = []
        subtotal = 0.0

        for item in items:
            item_total = item.quantity * item.menu_item.price
            subtotal += item_total
            cart_items_response.append({
                "id": item.id,
                "menu_item": item.menu_item,
                "quantity": item.quantity,
                "special_instructions": item.special_instructions,
                "item_total": round(item_total, 2),
            })

        return {
            "items": cart_items_response,
            "subtotal": round(subtotal, 2),
            "item_count": len(items),
        }

    def add_item(self, user: User, data: CartItemAdd) -> dict:
        menu_item = self.menu_repo.get_item_by_id(data.menu_item_id)
        if not menu_item:
            raise NotFoundException("Menu item")
        if not menu_item.is_available:
            raise BadRequestException("This menu item is currently unavailable")

        # Ensure cart items are from same restaurant (if cart not empty)
        cart_items = self.cart_repo.get_user_cart(user.id)
        if cart_items:
            existing_restaurant_id = cart_items[0].menu_item.restaurant_id
            if str(existing_restaurant_id) != str(menu_item.restaurant_id):
                raise BadRequestException(
                    "Cannot add items from different restaurants. Clear your cart first."
                )

        cart_item = self.cart_repo.add_or_update(
            user_id=user.id,
            menu_item_id=data.menu_item_id,
            quantity=data.quantity,
            special_instructions=data.special_instructions,
        )
        return {"message": "Item added to cart", "cart_item_id": str(cart_item.id)}

    def update_item(self, user: User, item_id: UUID, data: CartItemUpdate) -> dict:
        cart_item = self.cart_repo.get_cart_item(user.id, item_id)
        if not cart_item:
            raise NotFoundException("Cart item")

        self.cart_repo.update_item(cart_item, data.quantity, data.special_instructions)
        return {"message": "Cart item updated"}

    def remove_item(self, user: User, item_id: UUID) -> dict:
        cart_item = self.cart_repo.get_cart_item(user.id, item_id)
        if not cart_item:
            raise NotFoundException("Cart item")

        self.cart_repo.remove_item(cart_item)
        return {"message": "Item removed from cart"}

    def clear_cart(self, user: User) -> dict:
        self.cart_repo.clear_cart(user.id)
        return {"message": "Cart cleared"}


class OrderService:
    def __init__(self, db: Session):
        self.db = db
        self.order_repo = OrderRepository(db)
        self.cart_repo = CartRepository(db)
        self.restaurant_repo = RestaurantRepository(db)
        self.menu_repo = MenuRepository(db)

    def create_order(self, user: User, data: OrderCreate) -> dict:
        # Validate restaurant
        restaurant = self.restaurant_repo.get_by_id(data.restaurant_id)
        if not restaurant or not restaurant.is_active:
            raise NotFoundException("Restaurant")
        if not restaurant.is_open:
            raise BadRequestException("Restaurant is currently closed")

        # Determine order items
        if data.from_cart:
            cart_items = self.cart_repo.get_user_cart(user.id)
            if not cart_items:
                raise BadRequestException("Your cart is empty")

            # Validate all items belong to the specified restaurant
            for ci in cart_items:
                if str(ci.menu_item.restaurant_id) != str(data.restaurant_id):
                    raise BadRequestException("Cart items do not match the specified restaurant")

            order_items_data = [
                {
                    "menu_item_id": ci.menu_item_id,
                    "quantity": ci.quantity,
                    "unit_price": ci.menu_item.price,
                    "special_instructions": ci.special_instructions,
                }
                for ci in cart_items
            ]
        else:
            if not data.items:
                raise BadRequestException("No items provided")

            order_items_data = []
            for item in data.items:
                menu_item = self.menu_repo.get_item_by_id(item.menu_item_id)
                if not menu_item or not menu_item.is_available:
                    raise BadRequestException(f"Menu item {item.menu_item_id} is unavailable")
                if str(menu_item.restaurant_id) != str(data.restaurant_id):
                    raise BadRequestException("Menu item does not belong to this restaurant")

                order_items_data.append({
                    "menu_item_id": item.menu_item_id,
                    "quantity": item.quantity,
                    "unit_price": menu_item.price,
                    "special_instructions": item.special_instructions,
                })

        # Calculate pricing
        subtotal = sum(i["unit_price"] * i["quantity"] for i in order_items_data)

        if subtotal < restaurant.min_order_amount:
            raise BadRequestException(
                f"Minimum order amount is ${restaurant.min_order_amount:.2f}. "
                f"Your order is ${subtotal:.2f}."
            )

        delivery_fee = restaurant.delivery_fee
        tax = round(subtotal * 0.08, 2)  # 8% tax
        total_price = round(subtotal + delivery_fee + tax, 2)

        # Create order
        order = self.order_repo.create(
            user_id=user.id,
            restaurant_id=data.restaurant_id,
            delivery_address_id=data.delivery_address_id,
            payment_method=data.payment_method,
            subtotal=round(subtotal, 2),
            delivery_fee=delivery_fee,
            tax=tax,
            discount=0.0,
            total_price=total_price,
            special_instructions=data.special_instructions,
            estimated_delivery_time=restaurant.avg_delivery_time,
        )

        # Add order items
        for item_data in order_items_data:
            self.order_repo.add_item(
                order_id=order.id,
                menu_item_id=item_data["menu_item_id"],
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                special_instructions=item_data.get("special_instructions"),
            )

        self.order_repo.commit()

        # Clear cart if used
        if data.from_cart:
            self.cart_repo.clear_cart(user.id)

        return {"message": "Order placed successfully", "order_id": str(order.id)}

    def get_order(self, order_id: UUID, user: User) -> dict:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Order")

        # Only the owner or restaurant owner or admin can view
        is_customer_owner = str(order.user_id) == str(user.id)
        is_restaurant_owner = str(order.restaurant.owner_id) == str(user.id)
        is_admin = user.role == UserRole.ADMIN

        if not (is_customer_owner or is_restaurant_owner or is_admin):
            raise ForbiddenException()

        return self._serialize_order(order)

    def get_user_orders(self, user: User, skip: int = 0, limit: int = 20) -> List[dict]:
        orders = self.order_repo.get_user_orders(user.id, skip, limit)
        total = self.order_repo.count_user_orders(user.id)
        return orders, total

    def get_restaurant_orders(self, restaurant_id: UUID, user: User,
                               status: Optional[OrderStatus] = None,
                               skip: int = 0, limit: int = 20) -> List:
        restaurant = self.restaurant_repo.get_by_id(restaurant_id)
        if not restaurant:
            raise NotFoundException("Restaurant")

        if user.role != UserRole.ADMIN and str(restaurant.owner_id) != str(user.id):
            raise ForbiddenException()

        return self.order_repo.get_restaurant_orders(restaurant_id, status, skip, limit)

    def update_order_status(self, order_id: UUID, user: User, data: OrderStatusUpdate) -> dict:
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise NotFoundException("Order")

        # Only restaurant owner or admin can update status
        restaurant = self.restaurant_repo.get_by_id(order.restaurant_id)
        is_restaurant_owner = str(restaurant.owner_id) == str(user.id)
        is_admin = user.role == UserRole.ADMIN

        # Customers can only cancel their own pending orders
        if not is_restaurant_owner and not is_admin:
            if str(order.user_id) == str(user.id) and data.status == OrderStatus.CANCELLED:
                if order.status != OrderStatus.PENDING:
                    raise BadRequestException("Can only cancel pending orders")
            else:
                raise ForbiddenException("You cannot update this order's status")

        self.order_repo.update_status(order, data.status, data.note)
        return {"message": f"Order status updated to {data.status}"}

    def _serialize_order(self, order) -> dict:
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
                    "id": str(item.id),
                    "menu_item_id": str(item.menu_item_id),
                    "menu_item_name": item.menu_item.name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price,
                    "special_instructions": item.special_instructions,
                }
                for item in order.items
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