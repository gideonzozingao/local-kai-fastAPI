from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging

from app.core.config import settings
from app.core.exceptions import AppException
from app.api.v1.router import api_router

# ─────────────────────────── Logging ────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ─────────────────────────── App Instance ────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Local Kai API

A production-ready food ordering backend similar to Uber Eats / DoorDash.

### Features
- **JWT Authentication** — register, login, refresh tokens
- **Restaurants** — create, browse, filter by city/cuisine
- **Menu Management** — categories and items with availability control
- **Cart System** — add/update/remove items, cross-restaurant validation
- **Order Processing** — full lifecycle from pending → delivered
- **Real-time Tracking** — WebSocket connection per order
- **Stripe Payments** — payment intents + webhook handling
- **Reviews** — rating system with auto-recalculation
- **Background Jobs** — Celery + Redis for emails & notifications
- **RBAC** — customer, restaurant_owner, admin roles

### Quick Start
1. `POST /api/v1/auth/register` — create account
2. `POST /api/v1/auth/login` — get tokens
3. `GET /api/v1/restaurants` — browse restaurants
4. `POST /api/v1/cart/add` — add to cart
5. `POST /api/v1/orders` — place order
6. `WS /api/v1/ws/orders/{id}/track` — track in real-time
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ─────────────────────────── Middleware ────────────────────────────

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.ALLOWED_ORIGINS,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])


@app.middleware("http")
async def request_timing_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = round((time.time() - start) * 1000, 2)
    response.headers["X-Response-Time"] = f"{duration}ms"
    logger.info(f"{request.method} {request.url.path} → {response.status_code} ({duration}ms)")
    return response


# ─────────────────────────── Exception Handlers ────────────────────────────

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail},
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "An unexpected error occurred"},
    )


# ─────────────────────────── Routes ────────────────────────────

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Health"])
def root():
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "version": settings.APP_VERSION}
