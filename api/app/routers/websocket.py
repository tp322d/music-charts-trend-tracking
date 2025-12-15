"""
WebSocket router for real-time chart updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import List
import json
from app.core.security import decode_token

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        """Accept a new WebSocket connection."""
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send message to a specific connection."""
        await websocket.send_text(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients."""
        message_str = json.dumps(message)
        for connection in self.active_connections:
            try:
                await connection.send_text(message_str)
            except:
                # Connection might be closed, skip it
                pass


manager = ConnectionManager()


async def verify_websocket_token(token: str) -> bool:
    """Verify JWT token for WebSocket connection."""
    payload = decode_token(token)
    if payload and payload.get("type") == "access":
        return True
    return False


@router.websocket("/ws/live-charts")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(...)):
    """
    WebSocket endpoint for real-time chart updates.
    
    Requires valid JWT token in query parameter.
    Sends real-time updates for:
    - chart_update: New chart entry
    - rank_change: Position change
    - new_entry: Song enters chart
    """
    # Verify token
    if not await verify_websocket_token(token):
        await websocket.close(code=1008, reason="Invalid authentication token")
        return
    
    await manager.connect(websocket)
    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({"event": "connected", "message": "Connected to live charts"}),
            websocket
        )
        
        # Keep connection alive and listen for messages
        while True:
            data = await websocket.receive_text()
            # Echo back or process client messages if needed
            await manager.send_personal_message(
                json.dumps({"event": "echo", "data": data}),
                websocket
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket)

