"""
Full test suite for the Food Ordering API.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db

# ─────────────────────────── Test DB Setup ────────────────────────────

SQLALCHEMY_TEST_URL = "sqlite:///./test.db"

engine = create_engine(SQLALCHEMY_TEST_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def override_dependency():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client():
    return TestClient(app)


# ─────────────────────────── Fixtures ────────────────────────────

CUSTOMER = {
    "email": "customer@test.com",
    "full_name": "Test Customer",
    "password": "Secure123!",
}

OWNER = {
    "email": "owner@test.com",
    "full_name": "Restaurant Owner",
    "password": "Secure123!",
}

RESTAURANT_DATA = {
    "name": "Burger Palace",
    "description": "Best burgers in town",
    "address": "123 Main St",
    "city": "New York",
    "cuisine_type": "American",
    "delivery_fee": 2.99,
    "min_order_amount": 10.0,
    "avg_delivery_time": 30,
}


def register_and_login(client, user_data) -> str:
    """Helper: register user and return access token."""
    client.post("/api/v1/auth/register", json=user_data)
    resp = client.post("/api/v1/auth/login", json={
        "email": user_data["email"],
        "password": user_data["password"],
    })
    return resp.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────── Auth Tests ────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/api/v1/auth/register", json=CUSTOMER)
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == CUSTOMER["email"]

    def test_register_duplicate_email(self, client):
        client.post("/api/v1/auth/register", json=CUSTOMER)
        resp = client.post("/api/v1/auth/register", json=CUSTOMER)
        assert resp.status_code == 409

    def test_login_success(self, client):
        client.post("/api/v1/auth/register", json=CUSTOMER)
        resp = client.post("/api/v1/auth/login", json={
            "email": CUSTOMER["email"],
            "password": CUSTOMER["password"],
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        client.post("/api/v1/auth/register", json=CUSTOMER)
        resp = client.post("/api/v1/auth/login", json={
            "email": CUSTOMER["email"],
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    def test_get_me(self, client):
        token = register_and_login(client, CUSTOMER)
        resp = client.get("/api/v1/auth/me", headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["email"] == CUSTOMER["email"]

    def test_refresh_token(self, client):
        client.post("/api/v1/auth/register", json=CUSTOMER)
        login_resp = client.post("/api/v1/auth/login", json={
            "email": CUSTOMER["email"],
            "password": CUSTOMER["password"],
        })
        refresh_token = login_resp.json()["refresh_token"]
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_invalid_token_rejected(self, client):
        resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})
        assert resp.status_code == 401


# ─────────────────────────── Restaurant Tests ────────────────────────────

class TestRestaurants:
    def test_list_restaurants(self, client):
        resp = client.get("/api/v1/restaurants")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_create_restaurant(self, client):
        token = register_and_login(client, OWNER)
        resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(token))
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == RESTAURANT_DATA["name"]
        assert data["city"] == RESTAURANT_DATA["city"]

    def test_get_restaurant_by_id(self, client):
        token = register_and_login(client, OWNER)
        create_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(token))
        restaurant_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/restaurants/{restaurant_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == restaurant_id

    def test_get_nonexistent_restaurant(self, client):
        resp = client.get("/api/v1/restaurants/00000000-0000-0000-0000-000000000000")
        assert resp.status_code == 404

    def test_update_restaurant_as_owner(self, client):
        token = register_and_login(client, OWNER)
        create_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(token))
        restaurant_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/restaurants/{restaurant_id}",
            json={"name": "Updated Burger Palace"},
            headers=auth_headers(token),
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Burger Palace"

    def test_update_restaurant_as_non_owner_fails(self, client):
        owner_token = register_and_login(client, OWNER)
        other_token = register_and_login(client, {
            "email": "other@test.com",
            "full_name": "Other User",
            "password": "Secure123!",
        })

        create_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(owner_token))
        restaurant_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v1/restaurants/{restaurant_id}",
            json={"name": "Hijacked"},
            headers=auth_headers(other_token),
        )
        assert resp.status_code == 403


# ─────────────────────────── Menu Tests ────────────────────────────

class TestMenu:
    def setup_restaurant(self, client) -> tuple:
        token = register_and_login(client, OWNER)
        create_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(token))
        return create_resp.json()["id"], token

    def test_create_menu_item(self, client):
        restaurant_id, token = self.setup_restaurant(client)
        resp = client.post("/api/v1/menu/items", json={
            "restaurant_id": restaurant_id,
            "name": "Classic Burger",
            "description": "Juicy beef patty",
            "price": 12.99,
            "preparation_time": 15,
        }, headers=auth_headers(token))
        assert resp.status_code == 201
        assert resp.json()["name"] == "Classic Burger"
        assert resp.json()["price"] == 12.99

    def test_get_menu(self, client):
        restaurant_id, token = self.setup_restaurant(client)
        client.post("/api/v1/menu/items", json={
            "restaurant_id": restaurant_id,
            "name": "Fries",
            "price": 4.99,
        }, headers=auth_headers(token))

        resp = client.get(f"/api/v1/restaurants/{restaurant_id}/menu")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_update_menu_item(self, client):
        restaurant_id, token = self.setup_restaurant(client)
        item_resp = client.post("/api/v1/menu/items", json={
            "restaurant_id": restaurant_id,
            "name": "Soda",
            "price": 2.99,
        }, headers=auth_headers(token))
        item_id = item_resp.json()["id"]

        resp = client.patch(f"/api/v1/menu/items/{item_id}", json={"price": 3.49}, headers=auth_headers(token))
        assert resp.status_code == 200
        assert resp.json()["price"] == 3.49


# ─────────────────────────── Cart Tests ────────────────────────────

class TestCart:
    def setup(self, client) -> tuple:
        """Create restaurant + menu item + customer. Return (item_id, customer_token)."""
        owner_token = register_and_login(client, OWNER)
        rest_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(owner_token))
        restaurant_id = rest_resp.json()["id"]

        item_resp = client.post("/api/v1/menu/items", json={
            "restaurant_id": restaurant_id,
            "name": "Cheeseburger",
            "price": 9.99,
        }, headers=auth_headers(owner_token))
        item_id = item_resp.json()["id"]

        customer_token = register_and_login(client, CUSTOMER)
        return restaurant_id, item_id, customer_token

    def test_add_to_cart(self, client):
        _, item_id, token = self.setup(client)
        resp = client.post("/api/v1/cart/add", json={
            "menu_item_id": item_id,
            "quantity": 2,
        }, headers=auth_headers(token))
        assert resp.status_code == 200

    def test_get_cart(self, client):
        _, item_id, token = self.setup(client)
        client.post("/api/v1/cart/add", json={"menu_item_id": item_id, "quantity": 1}, headers=auth_headers(token))
        resp = client.get("/api/v1/cart", headers=auth_headers(token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["item_count"] >= 1
        assert data["subtotal"] > 0

    def test_clear_cart(self, client):
        _, item_id, token = self.setup(client)
        client.post("/api/v1/cart/add", json={"menu_item_id": item_id, "quantity": 1}, headers=auth_headers(token))
        resp = client.delete("/api/v1/cart", headers=auth_headers(token))
        assert resp.status_code == 200

        cart = client.get("/api/v1/cart", headers=auth_headers(token)).json()
        assert cart["item_count"] == 0


# ─────────────────────────── Order Tests ────────────────────────────

class TestOrders:
    def full_setup(self, client):
        """Full setup: restaurant, menu item, customer with item in cart."""
        owner_token = register_and_login(client, {
            "email": "ordowner@test.com",
            "full_name": "Order Owner",
            "password": "Secure123!",
        })
        rest_resp = client.post("/api/v1/restaurants", json=RESTAURANT_DATA, headers=auth_headers(owner_token))
        restaurant_id = rest_resp.json()["id"]

        item_resp = client.post("/api/v1/menu/items", json={
            "restaurant_id": restaurant_id,
            "name": "Test Burger",
            "price": 11.99,
        }, headers=auth_headers(owner_token))
        item_id = item_resp.json()["id"]

        customer_token = register_and_login(client, {
            "email": "ordcustomer@test.com",
            "full_name": "Order Customer",
            "password": "Secure123!",
        })
        client.post("/api/v1/cart/add", json={"menu_item_id": item_id, "quantity": 2},
                    headers=auth_headers(customer_token))

        return restaurant_id, item_id, customer_token, owner_token

    def test_create_order_from_cart(self, client):
        restaurant_id, _, customer_token, _ = self.full_setup(client)
        resp = client.post("/api/v1/orders", json={
            "restaurant_id": restaurant_id,
            "payment_method": "cash",
            "from_cart": True,
        }, headers=auth_headers(customer_token))
        assert resp.status_code == 201
        assert "order_id" in resp.json()

    def test_get_order_details(self, client):
        restaurant_id, _, customer_token, _ = self.full_setup(client)
        order_resp = client.post("/api/v1/orders", json={
            "restaurant_id": restaurant_id,
            "payment_method": "cash",
            "from_cart": True,
        }, headers=auth_headers(customer_token))
        order_id = order_resp.json()["order_id"]

        resp = client.get(f"/api/v1/orders/{order_id}", headers=auth_headers(customer_token))
        assert resp.status_code == 200
        assert resp.json()["id"] == order_id

    def test_order_status_update_by_owner(self, client):
        restaurant_id, _, customer_token, owner_token = self.full_setup(client)
        order_resp = client.post("/api/v1/orders", json={
            "restaurant_id": restaurant_id,
            "payment_method": "cash",
            "from_cart": True,
        }, headers=auth_headers(customer_token))
        order_id = order_resp.json()["order_id"]

        resp = client.patch(f"/api/v1/orders/{order_id}/status",
                            json={"status": "confirmed", "note": "Order accepted"},
                            headers=auth_headers(owner_token))
        assert resp.status_code == 200

    def test_list_my_orders(self, client):
        restaurant_id, _, customer_token, _ = self.full_setup(client)
        client.post("/api/v1/orders", json={
            "restaurant_id": restaurant_id,
            "payment_method": "cash",
            "from_cart": True,
        }, headers=auth_headers(customer_token))

        resp = client.get("/api/v1/orders", headers=auth_headers(customer_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1


# ─────────────────────────── Health Tests ────────────────────────────

class TestHealth:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_health_check(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
