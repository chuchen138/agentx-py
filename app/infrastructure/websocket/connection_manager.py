from typing import Dict, Set
from fastapi import WebSocket
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.heartbeat_tasks[session_id] = asyncio.create_task(self._heartbeat(session_id))

    async def disconnect(self, session_id: str):
        if session_id in self.heartbeat_tasks:
            self.heartbeat_tasks[session_id].cancel()
            del self.heartbeat_tasks[session_id]
        if session_id in self.active_connections:
            del self.active_connections[session_id]

    async def send_personal_message(self, message: str, session_id: str):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections.values():
            await connection.send_text(message)

    async def _heartbeat(self, session_id: str):
        try:
            while True:
                await asyncio.sleep(30)
                if session_id in self.active_connections:
                    await self.active_connections[session_id].send_text('ping')
        except asyncio.CancelledError:
            pass
        except Exception:
            await self.disconnect(session_id)

    def get_active_connections_count(self) -> int:
        return len(self.active_connections)