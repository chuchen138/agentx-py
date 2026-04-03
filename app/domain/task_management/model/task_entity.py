from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer, Index, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.core.database import Base
from app.domain.task_management.constant.task_status import TaskStatus, is_valid_status_transition


class TaskEntity(Base):
    __tablename__ = "tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String, nullable=False, index=True)
    user_id = Column(String, nullable=False, index=True)
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=True, index=True)
    task_name = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, nullable=False, default=TaskStatus.WAITING.value, index=True)
    progress = Column(Integer, default=0)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    task_result = Column(Text, nullable=True)
    version = Column(Integer, default=0)
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    parent_task = relationship("TaskEntity", remote_side=[id], backref="child_tasks")
    
    # 检查约束
    __table_args__ = (
        CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
        Index('idx_session_created', 'session_id', 'created_at', postgresql_using='btree', postgresql_descending=['created_at']),
        Index('idx_user_status', 'user_id', 'status'),
        Index('idx_parent_task', 'parent_task_id'),
        Index('idx_deleted_at', 'deleted_at'),
    )
    
    def __repr__(self):
        return f"<TaskEntity(id={self.id}, task_name={self.task_name}, status={self.status})>"
    
    def update_status(self, new_status: TaskStatus, expected_version: int):
        """更新任务状态，自动设置时间戳"""
        if self.version != expected_version:
            raise OptimisticLockException(f"Expected version {expected_version}, got {self.version}")
        
        current_status = TaskStatus(self.status)
        if not is_valid_status_transition(current_status, new_status):
            raise InvalidStatusTransitionException(f"Cannot transition from {current_status} to {new_status}")
        
        self.status = new_status.value
        
        if new_status == TaskStatus.IN_PROGRESS and not self.start_time:
            self.start_time = datetime.now()
        
        if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not self.end_time:
            self.end_time = datetime.now()
        
        self.version += 1
        self.updated_at = datetime.now()
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "parent_task_id": self.parent_task_id,
            "task_name": self.task_name,
            "description": self.description,
            "status": self.status,
            "progress": self.progress,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "task_result": self.task_result,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class OptimisticLockException(Exception):
    """乐观锁异常"""
    pass


class InvalidStatusTransitionException(Exception):
    """无效状态转换异常"""
    pass
