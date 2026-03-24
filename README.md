# 🍔 Food Ordering API

A **production-ready** REST API backend for a food ordering platform (think Uber Eats / DoorDash), built with **FastAPI**, **PostgreSQL**, **Redis**, and **Celery**.

---

## ✨ Feature Set

| Feature           | Details                                                        |
| ----------------- | -------------------------------------------------------------- |
| 🔐 **JWT Auth**    | Access + refresh tokens, role-based access                     |
| 🍽️ **Restaurants** | CRUD, filtering by city/cuisine, open status                   |
| 📋 **Menu**        | Categories + items, availability control, dietary flags        |
| 🛒 **Cart**        | Add/update/remove, cross-restaurant validation, totals         |
| 📦 **Orders**      | Full lifecycle, pricing breakdown (subtotal + tax + fee)       |
| 💳 **Payments**    | Stripe PaymentIntent + Webhook handler                         |
| 🔴 **Real-time**   | WebSocket order tracking per order                             |
| ⭐ **Reviews**     | Rating system with live restaurant score recalculation         |
| 📧 **Email**       | Celery + SMTP background jobs (confirmation, status updates)   |
| 🗄️ **Caching**     | Redis cache utility for menus and restaurant lists             |
| 👑 **RBAC**        | customer, restaurant_owner, admin roles                        |
| 🧪 **Tests**       | Full pytest suite (auth, restaurants, cart, orders)            |
| 🐳 **Docker**      | Full docker-compose stack (API + DB + Redis + Celery + Flower) |

---

## 🏗️ Architecture

```
food_ordering_api/
├── app/
│   ├── main.py                  # FastAPI app, middleware, exception handlers
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env vars)
│   │   ├── security.py          # JWT, password hashing
│   │   └── exceptions.py        # Custom HTTP exceptions
│   ├── db/
│   │   └── session.py           # SQLAlchemy engine + get_db dependency
│   ├── models/
│   │   └── models.py            # All SQLAlchemy ORM models
│   ├── schemas/
│   │   ├── user.py              # Pydantic request/response schemas
│   │   ├── restaurant.py
│   │   └── order.py
│   ├── repositories/            # DB abstraction layer (Repository Pattern)
│   │   ├── user_repository.py
│   │   ├── restaurant_repository.py
│   │   └── order_repository.py
│   ├── services/                # Business logic layer
│   │   ├── auth_service.py
│   │   ├── restaurant_service.py
│   │   └── order_service.py
│   ├── dependencies/
│   │   └── auth.py              # get_current_user, require_admin, etc.
│   ├── api/v1/endpoints/        # Route handlers
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── restaurants.py
│   │   ├── cart.py
│   │   ├── orders.py
│   │   ├── payments.py
│   │   ├── reviews.py
│   │   └── websocket.py
│   ├── workers/
│   │   ├── celery_app.py        # Celery configuration
│   │   └── tasks.py             # Background jobs (email, analytics)
│   └── utils/
│       └── cache.py             # Redis cache helper
├── tests/
│   └── test_api.py              # Full test suite
├── scripts/
│   └── seed.py                  # Sample data seeder
├── alembic/                     # Database migrations
├── docker-compose.yml
├── Dockerfile
├── Makefile
└── requirements.txt
```

---

## 🚀 Quick Start

### Option A — Docker (Recommended)

```bash
# 1. Clone and enter project
git clone <repo-url>
cd food_ordering_api

# 2. Copy env file
cp .env.example .env

# 3. Start full stack
make docker-up

# 4. Run migrations
docker exec food_ordering_api alembic upgrade head

# 5. Seed sample data
docker exec food_ordering_api python scripts/seed.py
```

API live at → **http://localhost:8000**
Swagger docs → **http://localhost:8000/docs**
Flower (Celery) → **http://localhost:5555**

---

### Option B — Local Development

**Prerequisites:** Python 3.11+, PostgreSQL, Redis

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with your DB/Redis credentials

# 3. Run migrations
alembic upgrade head

# 4. Seed sample data
python scripts/seed.py

# 5. Start API
make dev
```

---

## 🔑 Test Credentials (after seeding)

| Role             | Email                  | Password     |
| ---------------- | ---------------------- | ------------ |
| Admin            | admin@foodapp.com      | Admin123!    |
| Restaurant Owner | owner@burgerpalace.com | Owner123!    |
| Restaurant Owner | owner@sushizen.com     | Owner123!    |
| Restaurant Owner | owner@pizzaroma.com    | Owner123!    |
| Customer         | customer@test.com      | Customer123! |

---

## 📡 API Endpoints

### 🔐 Authentication
```
POST   /api/v1/auth/register         Register new account
POST   /api/v1/auth/login            Login → tokens
POST   /api/v1/auth/refresh          Refresh access token
GET    /api/v1/auth/me               Get current user
POST   /api/v1/auth/change-password  Change password
```

### 👤 Users
```
GET    /api/v1/users/me              Get profile
PATCH  /api/v1/users/me              Update profile
GET    /api/v1/users/me/addresses    List saved addresses
POST   /api/v1/users/me/addresses    Add address
DELETE /api/v1/users/me/addresses/{id}  Remove address
GET    /api/v1/users                 [Admin] List all users
GET    /api/v1/users/{id}            [Admin] Get user
DELETE /api/v1/users/{id}           [Admin] Deactivate user
```

### 🍽️ Restaurants
```
GET    /api/v1/restaurants           List (filter: city, cuisine, search, is_open)
GET    /api/v1/restaurants/{id}      Get restaurant
POST   /api/v1/restaurants           Create restaurant (auth)
PATCH  /api/v1/restaurants/{id}      Update restaurant (owner/admin)
DELETE /api/v1/restaurants/{id}      Deactivate (owner/admin)
GET    /api/v1/restaurants/{id}/menu Full menu with categories
```

### 📋 Menu
```
POST   /api/v1/menu/categories       Create category (owner)
POST   /api/v1/menu/items            Create item (owner)
PATCH  /api/v1/menu/items/{id}       Update item (owner)
DELETE /api/v1/menu/items/{id}       Delete item (owner)
```

### 🛒 Cart
```
GET    /api/v1/cart                  View cart with totals
POST   /api/v1/cart/add              Add item (merges if exists)
PATCH  /api/v1/cart/items/{id}       Update quantity/instructions
DELETE /api/v1/cart/items/{id}       Remove item
DELETE /api/v1/cart                  Clear entire cart
```

### 📦 Orders
```
POST   /api/v1/orders                Place order (from cart or item list)
GET    /api/v1/orders                My order history (paginated)
GET    /api/v1/orders/{id}           Order detail with tracking
PATCH  /api/v1/orders/{id}/status    Update status (owner/admin/customer cancel)
GET    /api/v1/orders/restaurant/{id} Restaurant's orders (owner/admin)
```

### 💳 Payments
```
POST   /api/v1/payments/create-intent/{order_id}  Create Stripe PaymentIntent
POST   /api/v1/payments/confirm                    Confirm payment
POST   /api/v1/payments/webhook                    Stripe webhook handler
```

### ⭐ Reviews
```
POST   /api/v1/reviews               Submit review (delivered orders only)
GET    /api/v1/reviews/restaurant/{id}  Get restaurant reviews
```

### 🔴 WebSocket
```
WS     /api/v1/ws/orders/{id}/track?token=<jwt>   Real-time order tracking
```

---

## 🔄 Order Lifecycle

```
PENDING → CONFIRMED → PREPARING → READY_FOR_PICKUP → OUT_FOR_DELIVERY → DELIVERED
                                                                       ↘ CANCELLED
```

Each transition is logged in `order_tracking` with an optional note.

---

## 🧪 Running Tests

```bash
# Run full test suite
make test

# With coverage report
make test-cov

# Run specific test class
pytest tests/test_api.py::TestOrders -v
```

---

## ⚙️ Key Design Decisions

### Repository Pattern
Database access is abstracted through repositories (`UserRepository`, `RestaurantRepository`, etc.), keeping route handlers and service layer clean.

### Service Layer
Business logic lives in service classes. Routes are thin — they validate input, call a service, and return. This mirrors Laravel's service/repository architecture.

### Cart Validation
- Items from different restaurants cannot coexist in the same cart
- Item availability is checked at cart add AND order creation time
- Minimum order amounts are enforced at checkout

### Pricing
Order total is calculated server-side (never trust client):
```
subtotal = sum(item.price × quantity)
tax      = subtotal × 0.08   (8%)
total    = subtotal + delivery_fee + tax - discount
```

### WebSocket Tracking
Each order gets its own WebSocket channel via `ConnectionManager`. Updates are pushed when restaurant owners change order status. Token auth via query param.

---

## 🔐 Environment Variables

| Variable                      | Description                   | Default                  |
| ----------------------------- | ----------------------------- | ------------------------ |
| `DATABASE_URL`                | PostgreSQL connection string  | —                        |
| `REDIS_URL`                   | Redis connection string       | redis://localhost:6379/0 |
| `SECRET_KEY`                  | JWT signing key (32+ chars)   | auto-generated           |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiry                    | 30                       |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | Refresh token expiry          | 7                        |
| `STRIPE_SECRET_KEY`           | Stripe secret key             | —                        |
| `STRIPE_WEBHOOK_SECRET`       | Stripe webhook signing secret | —                        |
| `SMTP_HOST`                   | Email SMTP host               | smtp.gmail.com           |
| `SMTP_PORT`                   | Email SMTP port               | 587                      |
| `SMTP_USER`                   | Email account                 | —                        |
| `SMTP_PASSWORD`               | Email password                | —                        |
| `ALLOWED_ORIGINS`             | CORS origins (JSON array)     | localhost                |

---

## 🐳 Docker Services

| Service         | Port | Description              |
| --------------- | ---- | ------------------------ |
| `api`           | 8000 | FastAPI application      |
| `db`            | 5432 | PostgreSQL 16            |
| `redis`         | 6379 | Redis 7                  |
| `celery_worker` | —    | Background job processor |
| `celery_beat`   | —    | Scheduled task scheduler |
| `flower`        | 5555 | Celery monitoring UI     |

---

## 📈 Scaling to Microservices (Phase 3)

When ready to scale, split by domain:

```
api-gateway/          → Nginx / Kong
auth-service/         → User auth only
restaurant-service/   → Restaurants + menus
order-service/        → Cart + orders
payment-service/      → Stripe integration
notification-service/ → Email + push + SMS
tracking-service/     → WebSocket + location
```

Each service gets its own DB and communicates via message queue (RabbitMQ / Kafka).

---

## 📜 License

MIT
# local-kai-fastAPI
