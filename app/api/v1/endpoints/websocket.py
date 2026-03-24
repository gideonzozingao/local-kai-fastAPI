from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from sqlalchemy.orm import Session
from typing import Dict, List
import json
import asyncio
from app.db.session import get_db
from app.core.security import decode_token
from app.repositories.order_repository import OrderRepository

router = APIRouter(prefix="/ws", tags=["WebSocket"])


class ConnectionManager:
    """Manages active WebSocket connections grouped by order ID."""

    def __init__(self):
        # order_id -> list of websockets
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        if order_id not in self.active_connections:
            self.active_connections[order_id] = []
        self.active_connections[order_id].append(websocket)

    def disconnect(self, websocket: WebSocket, order_id: str):
        if order_id in self.active_connections:
            self.active_connections[order_id].remove(websocket)
            if not self.active_connections[order_id]:
                del self.active_connections[order_id]

    async def send_order_update(self, order_id: str, data: dict):
        """Broadcast an order update to all subscribers."""
        if order_id in self.active_connections:
            message = json.dumps(data, default=str)
            dead = []
            for ws in self.active_connections[order_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[order_id].remove(ws)


manager = ConnectionManager()


@router.websocket("/orders/{order_id}/track")
async def track_order(
    websocket: WebSocket,
    order_id: str,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    WebSocket endpoint for real-time order tracking.

    Connect with:
        ws://localhost:8000/api/v1/ws/orders/{order_id}/track?token=<access_token>

    Receives JSON messages whenever the order status changes:
        {
            "event": "order_update",
            "order_id": "...",
            "status": "preparing",
            "note": "Your order is being prepared",
            "timestamp": "2024-01-01T12:00:00"
        }
    """
    # Validate token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=4001, reason="Invalid token")
        return

    user_id = payload.get("sub")

    # Validate order exists and belongs to user
    repo = OrderRepository(db)
    order = repo.get_by_id(order_id)

    if not order:
        await websocket.close(code=4004, reason="Order not found")
        return

    if str(order.user_id) != user_id:
        await websocket.close(code=4003, reason="Forbidden")
        return

    await manager.connect(websocket, order_id)

    try:
        # Send current status immediately on connect
        await websocket.send_text(json.dumps({
            "event": "connected",
            "order_id": order_id,
            "status": order.status,
            "message": "Connected to order tracking",
        }, default=str))

        # Keep connection alive, listening for pings
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                if data == "ping":
                    await websocket.send_text(json.dumps({"event": "pong"}))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"event": "heartbeat"}))

    except WebSocketDisconnect:
        manager.disconnect(websocket, order_id)


async def notify_order_update(order_id: str, status: str, note: str = None):
    """
    Call this from the order service when status changes.
    Usage:
        await notify_order_update(str(order.id), order.status, "Your order is ready!")
    """
    from datetime import datetime
    await manager.send_order_update(order_id, {
        "event": "order_update",
        "order_id": order_id,
        "status": status,
        "note": note,
        "timestamp": datetime.utcnow().isoformat(),
    })
