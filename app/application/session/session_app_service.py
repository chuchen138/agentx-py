from typing import List, Optional, Dict, Any
from app.domain.session.service import SessionService
from app.domain.session.entities import SessionEntity, MessageEntity, ContextEntity
import asyncio

class SessionAppService:
    def __init__(self):
        self.session_service = SessionService()
        self.sse_connections: Dict[str, asyncio.Queue] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, user_id: str, agent_id: str) -> Dict[str, Any]:
        session = await self.session_service.create_session(user_id, agent_id)
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "agent_id": session.agent_id,
            "status": session.status,
            "created_at": session.created_at.isoformat()
        }

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = await self.session_service.get_session(session_id)
        if not session:
            return None
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "agent_id": session.agent_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat()
        }

    async def interrupt_session(self, session_id: str) -> bool:
        success = await self.session_service.interrupt_session(session_id)
        if success:
            await self._close_sse_connection(session_id)
        return success

    async def add_message(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        message = await self.session_service.add_message(session_id, role, content)
        await self._push_message(session_id, message)
        return {
            "message_id": message.message_id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "token_count": message.token_count,
            "created_at": message.created_at.isoformat()
        }

    async def get_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        messages = await self.session_service.get_messages(session_id, limit)
        return [{
            "message_id": msg.message_id,
            "session_id": msg.session_id,
            "role": msg.role,
            "content": msg.content,
            "token_count": msg.token_count,
            "created_at": msg.created_at.isoformat()
        } for msg in messages]

    async def register_sse_connection(self, session_id: str) -> asyncio.Queue:
        queue = asyncio.Queue()
        async with self._lock:
            self.sse_connections[session_id] = queue
        return queue

    async def unregister_sse_connection(self, session_id: str):
        async with self._lock:
            if session_id in self.sse_connections:
                del self.sse_connections[session_id]

    async def _push_message(self, session_id: str, message: MessageEntity):
        async with self._lock:
            if session_id in self.sse_connections:
                try:
                    await self.sse_connections[session_id].put({
                        "event": "message",
                        "data": {
                            "type": message.role,
                            "content": message.content,
                            "session_id": message.session_id,
                            "timestamp": int(message.created_at.timestamp() * 1000)
                        },
                        "id": message.message_id
                    })
                except Exception:
                    pass

    async def _close_sse_connection(self, session_id: str):
        async with self._lock:
            if session_id in self.sse_connections:
                try:
                    await self.sse_connections[session_id].put({
                        "event": "session_end",
                        "data": {
                            "reason": "user_interrupted",
                            "duration_seconds": 0,
                            "message_count": 0
                        },
                        "id": f"evt_{session_id}"
                    })
                except Exception:
                    pass
                del self.sse_connections[session_id]

    async def cleanup_timeout_sessions(self):
        await self.session_service.cleanup_timeout_sessions()
        async with self._lock:
            expired_sessions = []
            for session_id in self.sse_connections:
                session = await self.session_service.get_session(session_id)
                if not session or session.status != "active":
                    expired_sessions.append(session_id)
            for session_id in expired_sessions:
                del self.sse_connections[session_id]

    async def get_active_session_count(self) -> int:
        return await self.session_service.get_active_session_count()