from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.session.entities import SessionEntity, MessageEntity, ContextEntity
import secrets
import asyncio

class SessionService:
    def __init__(self):
        self.sessions: Dict[str, SessionEntity] = {}
        self.messages: Dict[str, List[MessageEntity]] = {}
        self.contexts: Dict[str, ContextEntity] = {}
        self._lock = asyncio.Lock()

    async def create_session(self, user_id: str, agent_id: str) -> SessionEntity:
        session_id = f"sess_{secrets.token_hex(16)}"
        session = SessionEntity(session_id, user_id, agent_id)
        
        async with self._lock:
            self.sessions[session_id] = session
            self.messages[session_id] = []
        
        return session

    async def get_session(self, session_id: str) -> Optional[SessionEntity]:
        async with self._lock:
            return self.sessions.get(session_id)

    async def interrupt_session(self, session_id: str) -> bool:
        async with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].status = "interrupted"
                self.sessions[session_id].updated_at = datetime.utcnow()
                return True
            return False

    async def add_message(self, session_id: str, role: str, content: str) -> MessageEntity:
        message_id = f"msg_{secrets.token_hex(16)}"
        message = MessageEntity(message_id, session_id, role, content)
        
        async with self._lock:
            if session_id in self.messages:
                self.messages[session_id].append(message)
            else:
                self.messages[session_id] = [message]
        
        return message

    async def get_messages(self, session_id: str, limit: int = 100) -> List[MessageEntity]:
        async with self._lock:
            if session_id in self.messages:
                return self.messages[session_id][-limit:]
            return []

    async def update_context(self, session_id: str, message_ids: List[str], total_tokens: int) -> ContextEntity:
        context_id = f"ctx_{secrets.token_hex(16)}"
        context = ContextEntity(
            context_id=context_id,
            session_id=session_id,
            message_ids=message_ids,
            total_tokens=total_tokens
        )
        
        async with self._lock:
            self.contexts[session_id] = context
        
        return context

    async def get_context(self, session_id: str) -> Optional[ContextEntity]:
        async with self._lock:
            return self.contexts.get(session_id)

    async def cleanup_timeout_sessions(self, timeout_seconds: int = 1800):
        async with self._lock:
            current_time = datetime.utcnow()
            expired_sessions = []
            
            for session_id, session in self.sessions.items():
                time_diff = (current_time - session.updated_at).total_seconds()
                if time_diff > timeout_seconds:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]
                if session_id in self.messages:
                    del self.messages[session_id]
                if session_id in self.contexts:
                    del self.contexts[session_id]

    async def get_active_session_count(self) -> int:
        async with self._lock:
            return sum(1 for session in self.sessions.values() if session.status == "active")