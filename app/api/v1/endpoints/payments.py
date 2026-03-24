from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.core.config import settings
from app.core.exceptions import NotFoundException, BadRequestException
from app.models.models import User, PaymentStatus, OrderStatus
from app.repositories.order_repository import OrderRepository
from app.schemas.order import PaymentIntentResponse, PaymentConfirmRequest
import stripe

router = APIRouter(prefix="/payments", tags=["Payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/create-intent/{order_id}", response_model=PaymentIntentResponse)
def create_payment_intent(
    order_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create a Stripe PaymentIntent for an order.
    Returns `client_secret` to complete payment on the frontend.
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)

    if not order:
        raise NotFoundException("Order")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your order")
    if order.payment_status == PaymentStatus.PAID:
        raise BadRequestException("Order is already paid")

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(order.total_price * 100),  # Stripe uses cents
            currency="usd",
            metadata={"order_id": str(order.id), "user_id": str(current_user.id)},
        )

        # Store intent ID on the order
        repo.update(order, stripe_payment_intent_id=intent.id)

        return PaymentIntentResponse(
            client_secret=intent.client_secret,
            payment_intent_id=intent.id,
            amount=order.total_price,
        )

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))


@router.post("/confirm")
def confirm_payment(
    data: PaymentConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Confirm payment was successful and update the order.
    In production, use the webhook below instead.
    """
    repo = OrderRepository(db)
    order = repo.get_by_id(data.order_id)

    if not order:
        raise NotFoundException("Order")
    if str(order.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not your order")

    try:
        intent = stripe.PaymentIntent.retrieve(data.payment_intent_id)

        if intent.status == "succeeded":
            repo.update(order, payment_status=PaymentStatus.PAID)
            repo.update_status(order, OrderStatus.CONFIRMED, note="Payment confirmed")
            return {"message": "Payment confirmed", "order_id": str(order.id)}
        else:
            raise BadRequestException(f"Payment not completed. Status: {intent.status}")

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e.user_message))


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Stripe webhook endpoint.
    Configure this URL in your Stripe Dashboard → Webhooks.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Handle payment_intent.succeeded
    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")

        if order_id:
            repo = OrderRepository(db)
            order = repo.get_by_id(order_id)
            if order:
                repo.update(order, payment_status=PaymentStatus.PAID)
                repo.update_status(order, OrderStatus.CONFIRMED, note="Payment confirmed via webhook")

    # Handle payment_intent.payment_failed
    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        order_id = intent["metadata"].get("order_id")

        if order_id:
            repo = OrderRepository(db)
            order = repo.get_by_id(order_id)
            if order:
                repo.update(order, payment_status=PaymentStatus.FAILED)

    return {"received": True}
