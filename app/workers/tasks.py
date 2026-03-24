import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.workers.celery_app import celery_app
from app.core.config import settings

logger = logging.getLogger(__name__)


# ─────────────────────────── Email Tasks ────────────────────────────

@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, user_email: str, user_name: str, order_id: str, total: float):
    """Send order confirmation email to customer."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Order Confirmed! #{order_id[:8].upper()}"
        msg["From"] = settings.EMAILS_FROM
        msg["To"] = user_email

        html = f"""
        <html><body>
        <h2>Hey {user_name}, your order is confirmed! 🎉</h2>
        <p>Order ID: <strong>{order_id}</strong></p>
        <p>Total: <strong>${total:.2f}</strong></p>
        <p>We'll notify you when your food is on the way.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))

        _send_email(user_email, msg)
        logger.info(f"Order confirmation sent to {user_email}")

    except Exception as exc:
        logger.error(f"Failed to send confirmation email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_status_update_email(self, user_email: str, user_name: str, order_id: str, new_status: str):
    """Notify customer of order status change."""
    status_messages = {
        "confirmed": "Your order has been confirmed by the restaurant! 👨‍🍳",
        "preparing": "The kitchen is preparing your order! 🍳",
        "ready_for_pickup": "Your order is ready for pickup! 📦",
        "out_for_delivery": "Your order is on the way! 🚗",
        "delivered": "Your order has been delivered! Enjoy! 🎉",
        "cancelled": "Your order has been cancelled. 😔",
    }
    message = status_messages.get(new_status, f"Order status: {new_status}")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"Order Update #{order_id[:8].upper()}"
        msg["From"] = settings.EMAILS_FROM
        msg["To"] = user_email

        html = f"""
        <html><body>
        <h2>Order Update</h2>
        <p>Hey {user_name}!</p>
        <p>{message}</p>
        <p>Order ID: <strong>{order_id}</strong></p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))
        _send_email(user_email, msg)

    except Exception as exc:
        logger.error(f"Failed to send status update email: {exc}")
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3)
def send_new_order_notification_to_restaurant(self, restaurant_email: str, order_id: str, total: float, item_count: int):
    """Notify restaurant of a new incoming order."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"🔔 New Order! #{order_id[:8].upper()}"
        msg["From"] = settings.EMAILS_FROM
        msg["To"] = restaurant_email

        html = f"""
        <html><body>
        <h2>New Order Received! 🔔</h2>
        <p>Order ID: <strong>{order_id}</strong></p>
        <p>Items: <strong>{item_count}</strong></p>
        <p>Total: <strong>${total:.2f}</strong></p>
        <p>Please confirm the order in your dashboard.</p>
        </body></html>
        """
        msg.attach(MIMEText(html, "html"))
        _send_email(restaurant_email, msg)

    except Exception as exc:
        logger.error(f"Failed to notify restaurant: {exc}")
        raise self.retry(exc=exc)


# ─────────────────────────── Analytics Tasks ────────────────────────────

@celery_app.task
def update_restaurant_analytics(restaurant_id: str):
    """Recalculate and cache restaurant analytics (called after each order)."""
    # TODO: Implement caching with Redis
    logger.info(f"Updating analytics for restaurant {restaurant_id}")


# ─────────────────────────── Internal Helpers ────────────────────────────

def _send_email(to_email: str, msg: MIMEMultipart):
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(settings.EMAILS_FROM, to_email, msg.as_string())
