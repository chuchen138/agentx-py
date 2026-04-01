from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.infrastructure.websocket.connection_manager import ConnectionManager

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/ws/agents/{agentId}/sessions")
async def websocket_endpoint(websocket: WebSocket, agentId: str):
    session_id = f"agent_{agentId}_ws_session"
    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", session_id)
    except WebSocketDisconnect:
        await manager.disconnect(session_id)