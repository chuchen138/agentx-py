from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, unique=True, nullable=False, index=True)
    workflow_id = Column(String, ForeignKey("workflows.workflow_id"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    workflow = relationship("Workflow", back_populates="events")
    
    def __repr__(self):
        return f"<WorkflowEvent(id={self.id}, event_id={self.event_id}, type={self.event_type})>"
