from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime, UTC

# 基础模型基类
from app.core.database import Base


class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    avatar_url = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    system_prompt = Column(Text, nullable=True)
    welcome_message = Column(Text, nullable=True)
    tool_ids = Column(ARRAY(String), nullable=True, default=[])
    knowledge_base_ids = Column(ARRAY(String), nullable=True, default=[])
    tool_presets = Column(JSON, nullable=True, default={})
    multimodal_config = Column(JSON, nullable=True, default={})
    status = Column(String(20), nullable=False, default="ENABLED")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("UserModel", backref="agents")
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name}, status={self.status})>"
