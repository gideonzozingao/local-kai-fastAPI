from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, restaurants, cart, orders, payments, reviews, websocket
from app.api.v1.endpoints.restaurants import menu_router

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(restaurants.router)
api_router.include_router(menu_router)
api_router.include_router(cart.router)
api_router.include_router(orders.router)
api_router.include_router(payments.router)
api_router.include_router(reviews.router)
api_router.include_router(websocket.router)
