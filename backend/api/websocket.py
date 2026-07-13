"""WebSocket endpoint for real-time order status updates.

This module implements the Observer pattern: when an order status changes,
all connected WebSocket clients receive a push notification. This is critical
for the frontend timeline component that shows live agent decisions.

WebSocket Protocol:
    Client → Server: connect to /ws/orders/{order_id}
    Server → Client: push events {event, order_id, data}
    Client → Server: any text (echoed as pong — keeps connection alive)
    
Connection Lifecycle:
    1. Client opens WebSocket connection
    2. ConnectionManager stores {order_id: websocket} mapping
    3. OrderService sends_order_update() during processing
    4. Client receives push and updates React state
    5. Client disconnects → manager removes mapping

Interview Note:
    Q: Why WebSocket instead of Server-Sent Events (SSE) or polling?
    A: WebSocket is bidirectional, which lets us implement heartbeat/pong
       for connection health. SSE is simpler but only server→client. Polling
       wastes bandwidth and adds latency for time-sensitive order updates.
       
    Q: What happens if the client disconnects mid-processing?
    A: The order still completes and persists to the DB. The WebSocket is
       fire-and-forget; the client can reconnect and poll /orders/{id} to
       catch up on missed events.
    
    Q: How would you scale this to multiple backend instances?
    A: Use Redis Pub/Sub as the broadcast layer. Each instance subscribes to
       a Redis channel for order updates, so all instances can push to their
       local WebSocket connections. The event_bus.py already supports this.
"""

from typing import Dict

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

class ConnectionManager:
    """Manage WebSocket connections for real-time order updates.
    
    Currently stores connections in an in-memory dict. For horizontal scaling
    (multiple backend instances), this should be backed by Redis or a shared
    memory store so any instance can push to any connected client.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, order_id: str):
        """Accept connection and register for this order_id."""
        await websocket.accept()
        self.active_connections[order_id] = websocket
    
    def disconnect(self, order_id: str):
        """Remove connection from the registry."""
        self.active_connections.pop(order_id, None)
    
    async def send_order_update(self, order_id: str, data: dict):
        """Push an event to the client watching this order.
        
        If the client is not connected (e.g., disconnected), the event is
        silently dropped. This is intentional — WebSocket is best-effort
        and the client must handle reconnection or fallback polling.
        """
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)

manager = ConnectionManager()

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: str):
    """WebSocket endpoint for live order status updates.
    
    The client connects here and waits for push events. We keep the connection
    alive by echoing any client message as a pong heartbeat.
    """
    await manager.connect(websocket, order_id)
    try:
        while True:
            # Keep connection alive; optionally echo client messages
            data = await websocket.receive_text()
            # Reply with pong
            await websocket.send_json({"event": "pong", "order_id": order_id})
    except WebSocketDisconnect:
        manager.disconnect(order_id)
