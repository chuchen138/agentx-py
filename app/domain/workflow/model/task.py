from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, ARRAY, Index, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, unique=True, nullable=False, index=True)
    workflow_id = Column(String, ForeignKey("workflows.workflow_id"), nullable=False, index=True)
    parent_task_id = Column(String, ForeignKey("tasks.task_id"), nullable=True, index=True)
    task_name = Column(String(200), nullable=False)
    task_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(20), nullable=False, default="PENDING", index=True)
    priority = Column(Integer, nullable=False, default=0)
    depends_on = Column(ARRAY(String), nullable=True, default=[])
    result_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # 关系
    workflow = relationship("Workflow", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[task_id], backref="child_tasks")
    
    def __repr__(self):
        return f"<Task(id={self.id}, task_id={self.task_id}, name={self.task_name}, status={self.status})>"
