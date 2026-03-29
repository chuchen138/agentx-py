from datetime import datetime
from typing import List, Optional, Dict, Any

class SessionEntity:
    def __init__(self,
                 session_id: str,
                 user_id: str,
                 agent_id: str,
                 status: str = "active",
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None):
        self.session_id = session_id
        self.user_id = user_id
        self.agent_id = agent_id
        self.status = status
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

class MessageEntity:
    def __init__(self,
                 message_id: str,
                 session_id: str,
                 role: str,
                 content: str,
                 token_count: int = 0,
                 created_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.message_id = message_id
        self.session_id = session_id
        self.role = role
        self.content = content
        self.token_count = token_count
        self.created_at = created_at or datetime.utcnow()
        self.metadata = metadata or {}

class ContextEntity:
    def __init__(self,
                 context_id: str,
                 session_id: str,
                 message_ids: List[str],
                 total_tokens: int = 0,
                 max_tokens: int = 8000,
                 summary: Optional[str] = None,
                 version: int = 1,
                 created_at: Optional[datetime] = None):
        self.context_id = context_id
        self.session_id = session_id
        self.message_ids = message_ids
        self.total_tokens = total_tokens
        self.max_tokens = max_tokens
        self.summary = summary
        self.version = version
        self.created_at = created_at or datetime.utcnow()