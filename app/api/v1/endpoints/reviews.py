from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.core.exceptions import BadRequestException, ConflictException
from app.models.models import User, Review, Order, OrderStatus
from app.schemas.order import ReviewCreate, ReviewResponse
from app.repositories.restaurant_repository import RestaurantRepository

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("", status_code=201)
def create_review(
    data: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if data.order_id:
        order = db.query(Order).filter(
            Order.id == data.order_id,
            Order.user_id == current_user.id,
            Order.restaurant_id == data.restaurant_id,
        ).first()
        if not order:
            raise BadRequestException("Order not found or does not belong to you")
        if order.status != OrderStatus.DELIVERED:
            raise BadRequestException("You can only review delivered orders")
        existing = db.query(Review).filter(Review.order_id == data.order_id).first()
        if existing:
            raise ConflictException("You have already reviewed this order")

    review = Review(
        user_id=current_user.id,
        restaurant_id=data.restaurant_id,
        order_id=data.order_id,
        rating=data.rating,
        comment=data.comment,
    )
    db.add(review)

    repo = RestaurantRepository(db)
    restaurant = repo.get_by_id(data.restaurant_id)
    if restaurant:
        db.flush()
        all_reviews = db.query(Review).filter(Review.restaurant_id == data.restaurant_id).all()
        new_avg = sum(r.rating for r in all_reviews) / len(all_reviews)
        repo.update_rating(restaurant, round(new_avg, 2), len(all_reviews))

    db.commit()
    db.refresh(review)
    return ReviewResponse.model_validate(review).model_dump()


@router.get("/restaurant/{restaurant_id}")
def get_restaurant_reviews(
    restaurant_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    reviews = (
        db.query(Review)
        .filter(Review.restaurant_id == restaurant_id)
        .order_by(Review.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [ReviewResponse.model_validate(r).model_dump() for r in reviews]