from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
import uuid
from typing import Optional, Dict, Any

from app.core.database import Base
from app.domain.scheduledtask.constant import RepeatType, ScheduleTaskStatus


class ScheduledTask(Base):
    """定时任务实体"""
    __tablename__ = "scheduled_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    content = Column(String(10000), nullable=False)
    repeat_type = Column(SQLEnum(RepeatType), nullable=False)
    repeat_config = Column(JSON, nullable=False, default={})
    status = Column(SQLEnum(ScheduleTaskStatus), nullable=False, default=ScheduleTaskStatus.PENDING)
    last_execute_time = Column(DateTime, nullable=True)
    next_execute_time = Column(DateTime, nullable=False, index=True)
    max_retry_count = Column(Integer, default=3)
    timeout_minutes = Column(Integer, default=30)
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    notify_on_failure = Column(Boolean, default=True)
    docker_image = Column(String(255), default="agentx/task-sandbox:latest")
    resource_quota = Column(JSON, default={"cpu_limit": 1.0, "memory_limit": "512M"})
    version = Column(Integer, default=0)  # 乐观锁
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ScheduledTask(id={self.id}, status={self.status}, next_execute={self.next_execute_time})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "agent_id": self.agent_id,
            "session_id": self.session_id,
            "content": self.content,
            "repeat_type": self.repeat_type.value if self.repeat_type else None,
            "repeat_config": self.repeat_config,
            "status": self.status.value if self.status else None,
            "last_execute_time": self.last_execute_time.isoformat() if self.last_execute_time else None,
            "next_execute_time": self.next_execute_time.isoformat() if self.next_execute_time else None,
            "max_retry_count": self.max_retry_count,
            "timeout_minutes": self.timeout_minutes,
            "last_error": self.last_error,
            "retry_count": self.retry_count,
            "notify_on_failure": self.notify_on_failure,
            "docker_image": self.docker_image,
            "resource_quota": self.resource_quota,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class TaskExecutionLog(Base):
    """任务执行日志实体"""
    __tablename__ = "task_execution_logs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), nullable=False, index=True)
    execute_time = Column(DateTime, nullable=False)
    status = Column(String(20), nullable=False)  # SUCCESS/FAILED/TIMEOUT
    result = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration = Column(Integer, nullable=True)  # 毫秒
    container_id = Column(String(64), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<TaskExecutionLog(task_id={self.task_id}, status={self.status}, execute_time={self.execute_time})>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "task_id": self.task_id,
            "execute_time": self.execute_time.isoformat() if self.execute_time else None,
            "status": self.status,
            "result": self.result,
            "error_message": self.error_message,
            "duration": self.duration,
            "container_id": self.container_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
