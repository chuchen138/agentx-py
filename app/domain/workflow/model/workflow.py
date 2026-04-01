from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Workflow(Base):
    __tablename__ = "workflows"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    workflow_id = Column(String, unique=True, nullable=False, index=True)
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    status = Column(String(20), nullable=False, default="ACTIVE", index=True)
    current_state = Column(String(20), nullable=False, default="INIT")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    user = relationship("UserModel", backref="workflows")
    agent = relationship("Agent", backref="workflows")
    tasks = relationship("Task", back_populates="workflow", cascade="all, delete-orphan")
    events = relationship("WorkflowEvent", back_populates="workflow", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Workflow(id={self.id}, workflow_id={self.workflow_id}, status={self.status}, state={self.current_state})>"
