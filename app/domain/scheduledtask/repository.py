from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.domain.scheduledtask.model import ScheduledTask, TaskExecutionLog
from app.domain.scheduledtask.constant import ScheduleTaskStatus


class ScheduledTaskRepository(ABC):
    """定时任务仓储接口"""

    @abstractmethod
    def create(self, task: ScheduledTask) -> ScheduledTask:
        """创建任务"""
        pass

    @abstractmethod
    def update(self, task: ScheduledTask) -> ScheduledTask:
        """更新任务"""
        pass

    @abstractmethod
    def delete(self, task_id: str) -> bool:
        """删除任务"""
        pass

    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[ScheduledTask]:
        """根据ID获取任务"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str, page: int = 1, page_size: int = 10, status: Optional[ScheduleTaskStatus] = None) -> Dict[str, Any]:
        """根据用户ID获取任务列表"""
        pass

    @abstractmethod
    def get_by_agent_id(self, agent_id: str) -> List[ScheduledTask]:
        """根据Agent ID获取任务列表"""
        pass

    @abstractmethod
    def get_by_session_id(self, session_id: str) -> List[ScheduledTask]:
        """根据会话ID获取任务列表"""
        pass

    @abstractmethod
    def get_by_status(self, status: ScheduleTaskStatus) -> List[ScheduledTask]:
        """根据状态获取任务列表"""
        pass

    @abstractmethod
    def get_due_tasks(self, before_time: datetime) -> List[ScheduledTask]:
        """获取到期的任务（next_execute_time <= before_time）"""
        pass

    @abstractmethod
    def update_status(self, task_id: str, status: ScheduleTaskStatus, version: int) -> bool:
        """更新任务状态（带乐观锁）"""
        pass


class TaskExecutionLogRepository(ABC):
    """任务执行日志仓储接口"""

    @abstractmethod
    def create(self, log: TaskExecutionLog) -> TaskExecutionLog:
        """创建执行日志"""
        pass

    @abstractmethod
    def get_by_task_id(self, task_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """根据任务ID获取执行日志列表"""
        pass

    @abstractmethod
    def get_by_id(self, log_id: str) -> Optional[TaskExecutionLog]:
        """根据ID获取执行日志"""
        pass


class SQLAlchemyScheduledTaskRepository(ScheduledTaskRepository):
    """SQLAlchemy 定时任务仓储实现"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, task: ScheduledTask) -> ScheduledTask:
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task

    def update(self, task: ScheduledTask) -> ScheduledTask:
        self.db.commit()
        self.db.refresh(task)
        return task

    def delete(self, task_id: str) -> bool:
        task = self.get_by_id(task_id)
        if task:
            self.db.delete(task)
            self.db.commit()
            return True
        return False

    def get_by_id(self, task_id: str) -> Optional[ScheduledTask]:
        return self.db.query(ScheduledTask).filter(ScheduledTask.id == task_id).first()

    def get_by_user_id(self, user_id: str, page: int = 1, page_size: int = 10, status: Optional[ScheduleTaskStatus] = None) -> Dict[str, Any]:
        query = self.db.query(ScheduledTask).filter(ScheduledTask.user_id == user_id)

        if status:
            query = query.filter(ScheduledTask.status == status)

        total = query.count()
        items = query.order_by(desc(ScheduledTask.created_at)).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_by_agent_id(self, agent_id: str) -> List[ScheduledTask]:
        return self.db.query(ScheduledTask).filter(ScheduledTask.agent_id == agent_id).all()

    def get_by_session_id(self, session_id: str) -> List[ScheduledTask]:
        return self.db.query(ScheduledTask).filter(ScheduledTask.session_id == session_id).all()

    def get_by_status(self, status: ScheduleTaskStatus) -> List[ScheduledTask]:
        return self.db.query(ScheduledTask).filter(ScheduledTask.status == status).all()

    def get_due_tasks(self, before_time: datetime) -> List[ScheduledTask]:
        return self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.next_execute_time <= before_time,
                ScheduledTask.status == ScheduleTaskStatus.PENDING
            )
        ).all()

    def update_status(self, task_id: str, status: ScheduleTaskStatus, version: int) -> bool:
        """更新任务状态（带乐观锁）"""
        result = self.db.query(ScheduledTask).filter(
            and_(
                ScheduledTask.id == task_id,
                ScheduledTask.version == version
            )
        ).update({
            "status": status,
            "version": version + 1
        })
        self.db.commit()
        return result > 0


class SQLAlchemyTaskExecutionLogRepository(TaskExecutionLogRepository):
    """SQLAlchemy 任务执行日志仓储实现"""

    def __init__(self, db: Session):
        self.db = db

    def create(self, log: TaskExecutionLog) -> TaskExecutionLog:
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def get_by_task_id(self, task_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        query = self.db.query(TaskExecutionLog).filter(TaskExecutionLog.task_id == task_id)
        total = query.count()
        items = query.order_by(desc(TaskExecutionLog.execute_time)).offset((page - 1) * page_size).limit(page_size).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    def get_by_id(self, log_id: str) -> Optional[TaskExecutionLog]:
        return self.db.query(TaskExecutionLog).filter(TaskExecutionLog.id == log_id).first()
