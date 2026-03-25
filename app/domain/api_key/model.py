from __future__ import annotations
import uuid
from datetime import datetime, UTC
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime, func
from app.core.database import Base


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    api_key = Column(String(255), unique=True, nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    status = Column(Boolean, nullable=False, default=True)
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 确保默认值正确设置
        if self.usage_count is None:
            self.usage_count = 0
        if self.status is None:
            self.status = True
        if self.created_at is None:
            self.created_at = datetime.now(UTC)
        if self.updated_at is None:
            self.updated_at = datetime.now(UTC)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return datetime.now(UTC) > self.expires_at

    @property
    def is_available(self) -> bool:
        return self.status and not self.is_expired

    def update_usage(self) -> None:
        self.usage_count += 1
        self.last_used_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, status={self.status})>"
