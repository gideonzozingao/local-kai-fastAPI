"""
Seed script - populates the database with realistic sample data.
Run: python scripts/seed.py
"""
import sys
import os

_here = os.path.dirname(os.path.abspath(__file__))
_one_up = os.path.dirname(_here)
_two_up = os.path.dirname(_one_up)

for _candidate in (_one_up, _two_up):
    if os.path.isdir(os.path.join(_candidate, "app")):
        sys.path.insert(0, _candidate)
        break

from app.db.session import SessionLocal, engine, Base
from app.models.models import (
    User, Restaurant, MenuCategory, MenuItem, UserRole
)
from app.core.security import get_password_hash
import uuid
from app.main import app

Base.metadata.create_all(bind=engine)


def seed():

    db = SessionLocal()
    print("🌱 Seeding database...")

    # ─── Admin User ───
    admin = db.query(User).filter(User.email == "admin@foodapp.com").first()
    if not admin:
        admin = User(
            id=uuid.uuid4(),
            email="admin@foodapp.com",
            full_name="Super Admin",
            password_hash=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
        )
        db.add(admin)
        print("  ✅ Admin user: admin@foodapp.com / Admin123!")

    # ─── Restaurant Owner ───
    owner = db.query(User).filter(User.email == "owner@burgerpalace.com").first()
    if not owner:
        owner = User(
            id=uuid.uuid4(),
            email="owner@burgerpalace.com",
            full_name="Bob Burger",
            password_hash=get_password_hash("Owner123!"),
            role=UserRole.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
        )
        db.add(owner)

    # ─── Customer ───
    customer = db.query(User).filter(User.email == "customer@test.com").first()
    if not customer:
        customer = User(
            id=uuid.uuid4(),
            email="customer@test.com",
            full_name="Jane Doe",
            password_hash=get_password_hash("Customer123!"),
            role=UserRole.CUSTOMER,
            is_active=True,
            is_verified=True,
        )
        db.add(customer)

    db.flush()

    # ─── Restaurant 1: Burger Palace ───
    restaurant1 = db.query(Restaurant).filter(Restaurant.name == "Burger Palace").first()
    if not restaurant1:
        restaurant1 = Restaurant(
            id=uuid.uuid4(),
            owner_id=owner.id,
            name="Burger Palace",
            description="The finest burgers in the city, made fresh daily with locally sourced beef.",
            address="123 Main Street",
            city="New York",
            phone="+1 212-555-0101",
            email="info@burgerpalace.com",
            cuisine_type="American",
            rating=4.7,
            total_reviews=142,
            is_active=True,
            is_open=True,
            delivery_fee=2.99,
            min_order_amount=10.0,
            avg_delivery_time=25,
        )
        db.add(restaurant1)
        db.flush()

        # Categories
        burgers_cat = MenuCategory(
            id=uuid.uuid4(), restaurant_id=restaurant1.id,
            name="Burgers", display_order=1
        )
        sides_cat = MenuCategory(
            id=uuid.uuid4(), restaurant_id=restaurant1.id,
            name="Sides", display_order=2
        )
        drinks_cat = MenuCategory(
            id=uuid.uuid4(), restaurant_id=restaurant1.id,
            name="Drinks", display_order=3
        )
        db.add_all([burgers_cat, sides_cat, drinks_cat])
        db.flush()

        # Menu Items
        items = [
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=burgers_cat.id,
                     name="Classic Cheeseburger", description="Beef patty, cheddar, lettuce, tomato, special sauce",
                     price=12.99, is_available=True, calories=650, preparation_time=12),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=burgers_cat.id,
                     name="Bacon Double Stack", description="Two patties, crispy bacon, swiss cheese, pickles",
                     price=16.99, is_available=True, calories=920, preparation_time=15),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=burgers_cat.id,
                     name="Veggie Burger", description="Plant-based patty, avocado, sprouts, chipotle mayo",
                     price=13.99, is_available=True, is_vegetarian=True, is_vegan=True,
                     calories=480, preparation_time=10),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=sides_cat.id,
                     name="Loaded Fries", description="Crispy fries, cheese sauce, jalapeños, sour cream",
                     price=6.99, is_available=True, calories=420, preparation_time=8),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=sides_cat.id,
                     name="Onion Rings", description="Beer-battered, golden crispy rings",
                     price=5.99, is_available=True, calories=380, preparation_time=8),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=drinks_cat.id,
                     name="Craft Lemonade", description="Fresh-squeezed, house-made lemonade",
                     price=3.99, is_available=True, calories=120, preparation_time=2),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant1.id, category_id=drinks_cat.id,
                     name="Milkshake", description="Thick and creamy — vanilla, chocolate, or strawberry",
                     price=5.99, is_available=True, calories=550, preparation_time=5),
        ]
        db.add_all(items)
        print("  ✅ Restaurant: Burger Palace (7 menu items)")

    # ─── Restaurant 2: Sushi Zen ───
    owner2 = db.query(User).filter(User.email == "owner@sushizen.com").first()
    if not owner2:
        owner2 = User(
            id=uuid.uuid4(),
            email="owner@sushizen.com",
            full_name="Yuki Tanaka",
            password_hash=get_password_hash("Owner123!"),
            role=UserRole.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
        )
        db.add(owner2)
        db.flush()

    restaurant2 = db.query(Restaurant).filter(Restaurant.name == "Sushi Zen").first()
    if not restaurant2:
        restaurant2 = Restaurant(
            id=uuid.uuid4(),
            owner_id=owner2.id,
            name="Sushi Zen",
            description="Authentic Japanese cuisine. Fresh fish flown in daily from Japan.",
            address="456 Park Avenue",
            city="New York",
            phone="+1 212-555-0202",
            email="hello@sushizen.com",
            cuisine_type="Japanese",
            rating=4.9,
            total_reviews=318,
            is_active=True,
            is_open=True,
            delivery_fee=4.99,
            min_order_amount=25.0,
            avg_delivery_time=40,
        )
        db.add(restaurant2)
        db.flush()

        rolls_cat = MenuCategory(id=uuid.uuid4(), restaurant_id=restaurant2.id, name="Rolls", display_order=1)
        nigiri_cat = MenuCategory(id=uuid.uuid4(), restaurant_id=restaurant2.id, name="Nigiri", display_order=2)
        starters_cat = MenuCategory(id=uuid.uuid4(), restaurant_id=restaurant2.id, name="Starters", display_order=3)
        db.add_all([rolls_cat, nigiri_cat, starters_cat])
        db.flush()

        sushi_items = [
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=rolls_cat.id,
                     name="Dragon Roll", description="Shrimp tempura, avocado, eel sauce",
                     price=15.99, is_available=True, preparation_time=20),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=rolls_cat.id,
                     name="Spicy Tuna Roll", description="Fresh tuna, cucumber, spicy mayo, sesame",
                     price=13.99, is_available=True, preparation_time=15),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=rolls_cat.id,
                     name="California Roll", description="Crab, avocado, cucumber, tobiko",
                     price=11.99, is_available=True, preparation_time=12),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=nigiri_cat.id,
                     name="Salmon Nigiri (2pc)", description="Premium Atlantic salmon over seasoned rice",
                     price=7.99, is_available=True, preparation_time=10),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=nigiri_cat.id,
                     name="Tuna Nigiri (2pc)", description="Bluefin tuna over seasoned rice",
                     price=8.99, is_available=True, preparation_time=10),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=starters_cat.id,
                     name="Edamame", description="Steamed salted soybeans",
                     price=4.99, is_available=True, is_vegetarian=True, is_vegan=True, preparation_time=5),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant2.id, category_id=starters_cat.id,
                     name="Miso Soup", description="Traditional dashi broth, tofu, wakame, green onion",
                     price=3.99, is_available=True, is_vegetarian=True, preparation_time=5),
        ]
        db.add_all(sushi_items)
        print("  ✅ Restaurant: Sushi Zen (7 menu items)")

    # ─── Restaurant 3: Pizza Roma ───
    owner3 = db.query(User).filter(User.email == "owner@pizzaroma.com").first()
    if not owner3:
        owner3 = User(
            id=uuid.uuid4(),
            email="owner@pizzaroma.com",
            full_name="Marco Romano",
            password_hash=get_password_hash("Owner123!"),
            role=UserRole.RESTAURANT_OWNER,
            is_active=True,
            is_verified=True,
        )
        db.add(owner3)
        db.flush()

    restaurant3 = db.query(Restaurant).filter(Restaurant.name == "Pizza Roma").first()
    if not restaurant3:
        restaurant3 = Restaurant(
            id=uuid.uuid4(),
            owner_id=owner3.id,
            name="Pizza Roma",
            description="Authentic Neapolitan pizza, wood-fired oven, imported Italian ingredients.",
            address="789 Broadway",
            city="New York",
            phone="+1 212-555-0303",
            cuisine_type="Italian",
            rating=4.5,
            total_reviews=201,
            is_active=True,
            is_open=True,
            delivery_fee=1.99,
            min_order_amount=15.0,
            avg_delivery_time=35,
        )
        db.add(restaurant3)
        db.flush()

        pizza_cat = MenuCategory(id=uuid.uuid4(), restaurant_id=restaurant3.id, name="Pizzas", display_order=1)
        pasta_cat = MenuCategory(id=uuid.uuid4(), restaurant_id=restaurant3.id, name="Pasta", display_order=2)
        db.add_all([pizza_cat, pasta_cat])
        db.flush()

        pizza_items = [
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant3.id, category_id=pizza_cat.id,
                     name="Margherita", description="San Marzano tomato, fresh mozzarella, basil",
                     price=14.99, is_available=True, is_vegetarian=True, calories=720, preparation_time=18),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant3.id, category_id=pizza_cat.id,
                     name="Pepperoni Supreme", description="Tomato sauce, mozzarella, premium pepperoni",
                     price=16.99, is_available=True, calories=890, preparation_time=18),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant3.id, category_id=pizza_cat.id,
                     name="Quattro Formaggi", description="Mozzarella, gorgonzola, pecorino, parmigiano",
                     price=17.99, is_available=True, is_vegetarian=True, calories=980, preparation_time=20),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant3.id, category_id=pasta_cat.id,
                     name="Cacio e Pepe", description="Tonnarelli pasta, pecorino, black pepper",
                     price=13.99, is_available=True, is_vegetarian=True, calories=620, preparation_time=15),
            MenuItem(id=uuid.uuid4(), restaurant_id=restaurant3.id, category_id=pasta_cat.id,
                     name="Spaghetti Carbonara", description="Guanciale, egg yolk, pecorino, black pepper",
                     price=15.99, is_available=True, calories=750, preparation_time=15),
        ]
        db.add_all(pizza_items)
        print("  ✅ Restaurant: Pizza Roma (5 menu items)")

    db.commit()
    db.close()

    print("\n✅ Database seeded successfully!\n")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Test Accounts")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Admin    admin@foodapp.com      / Admin123!")
    print("  Owner 1  owner@burgerpalace.com / Owner123!")
    print("  Owner 2  owner@sushizen.com     / Owner123!")
    print("  Owner 3  owner@pizzaroma.com    / Owner123!")
    print("  Customer customer@test.com      / Customer123!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Docs: http://localhost:8000/docs")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == "__main__":
    seed()
