"""
Live betting router with WebSocket support
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.models.user import User
from app.routers.auth import get_current_user
import json

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.get("/opportunities")
async def get_live_opportunities(current_user: User = Depends(get_current_user)):
    """Get current live betting opportunities"""
    return {
        "live_games": [],
        "opportunities": [],
        "best_bet": None
    }

@router.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for live updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for any message from client
            data = await websocket.receive_text()
            
            # Send updates (this would be triggered by live data)
            await websocket.send_text(json.dumps({
                "type": "live_update",
                "data": "Live betting update"
            }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)