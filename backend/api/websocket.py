from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json

class ConnectionManager:
    """Manage WebSocket connections for real-time order updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, order_id: str):
        await websocket.accept()
        self.active_connections[order_id] = websocket
    
    def disconnect(self, order_id: str):
        self.active_connections.pop(order_id, None)
    
    async def send_order_update(self, order_id: str, data: dict):
        if order_id in self.active_connections:
            await self.active_connections[order_id].send_json(data)

manager = ConnectionManager()

router = APIRouter(tags=["websocket"])

@router.websocket("/ws/orders/{order_id}")
async def websocket_endpoint(websocket: WebSocket, order_id: str):
    await manager.connect(websocket, order_id)
    try:
        while True:
            # Keep connection alive; optionally echo client messages
            data = await websocket.receive_text()
            # Reply with pong
            await websocket.send_json({"event": "pong", "order_id": order_id})
    except WebSocketDisconnect:
        manager.disconnect(order_id)
