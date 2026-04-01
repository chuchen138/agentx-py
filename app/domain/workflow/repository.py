from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.domain.workflow.model.workflow import Workflow
from app.domain.workflow.model.task import Task
from app.domain.workflow.model.workflow_event import WorkflowEvent
from app.domain.workflow.model.summary import Summary


class WorkflowRepository(ABC):
    """工作流仓储接口"""
    
    @abstractmethod
    def create(self, workflow_data: Dict[str, Any]) -> Workflow:
        """创建工作流"""
        pass
    
    @abstractmethod
    def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        """根据ID获取工作流"""
        pass
    
    @abstractmethod
    def get_by_session_id(self, session_id: str) -> List[Workflow]:
        """根据会话ID获取工作流列表"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str, page: int, size: int) -> List[Workflow]:
        """根据用户ID获取工作流列表（分页）"""
        pass
    
    @abstractmethod
    def get_active_workflows(self) -> List[Workflow]:
        """获取活跃工作流列表"""
        pass
    
    @abstractmethod
    def update_status(self, workflow_id: str, status: str, state: str):
        """更新工作流状态"""
        pass
    
    @abstractmethod
    def complete_workflow(self, workflow_id: str, result_data: Dict[str, Any]):
        """完成工作流"""
        pass
    
    @abstractmethod
    def fail_workflow(self, workflow_id: str, error_message: str):
        """失败工作流"""
        pass
    
    @abstractmethod
    def delete(self, workflow_id: str):
        """删除工作流"""
        pass


class TaskRepository(ABC):
    """任务仓储接口"""
    
    @abstractmethod
    def create(self, task_data: Dict[str, Any]) -> Task:
        """创建任务"""
        pass
    
    @abstractmethod
    def get_by_id(self, task_id: str) -> Optional[Task]:
        """根据ID获取任务"""
        pass
    
    @abstractmethod
    def get_by_workflow_id(self, workflow_id: str) -> List[Task]:
        """根据工作流ID获取任务列表"""
        pass
    
    @abstractmethod
    def get_pending_tasks(self, workflow_id: str) -> List[Task]:
        """获取待执行任务列表"""
        pass
    
    @abstractmethod
    def get_completed_tasks(self, workflow_id: str) -> List[Task]:
        """获取已完成任务列表"""
        pass
    
    @abstractmethod
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        """获取任务依赖"""
        pass
    
    @abstractmethod
    def update_status(self, task_id: str, status: str, result_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
        """更新任务状态"""
        pass
    
    @abstractmethod
    def increment_retry(self, task_id: str):
        """增加重试次数"""
        pass
    
    @abstractmethod
    def count_by_workflow(self, workflow_id: str) -> int:
        """统计工作流任务数"""
        pass


class WorkflowEventRepository(ABC):
    """工作流事件仓储接口"""
    
    @abstractmethod
    def record_event(self, event_data: Dict[str, Any]) -> WorkflowEvent:
        """记录事件"""
        pass
    
    @abstractmethod
    def get_by_workflow_id(self, workflow_id: str, limit: int = 100) -> List[WorkflowEvent]:
        """根据工作流ID获取事件列表"""
        pass
    
    @abstractmethod
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[WorkflowEvent]:
        """根据事件类型获取事件列表"""
        pass
    
    @abstractmethod
    def clear_events(self, workflow_id: str):
        """清理工作流事件"""
        pass


class SummaryRepository(ABC):
    """摘要仓储接口"""
    
    @abstractmethod
    def save_summary(self, summary_data: Dict[str, Any]) -> Summary:
        """保存摘要"""
        pass
    
    @abstractmethod
    def get_by_session_id(self, session_id: str) -> Optional[Summary]:
        """根据会话ID获取摘要"""
        pass
    
    @abstractmethod
    def get_by_workflow_id(self, workflow_id: str) -> Optional[Summary]:
        """根据工作流ID获取摘要"""
        pass
    
    @abstractmethod
    def update_summary(self, summary_id: str, summary_text: str, token_count: int):
        """更新摘要"""
        pass


class SQLAlchemyWorkflowRepository(WorkflowRepository):
    """SQLAlchemy工作流仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, workflow_data: Dict[str, Any]) -> Workflow:
        workflow = Workflow(**workflow_data)
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)
        return workflow
    
    def get_by_id(self, workflow_id: str) -> Optional[Workflow]:
        return self.db.query(Workflow).filter(Workflow.workflow_id == workflow_id).first()
    
    def get_by_session_id(self, session_id: str) -> List[Workflow]:
        return self.db.query(Workflow).filter(Workflow.session_id == session_id).all()
    
    def get_by_user_id(self, user_id: str, page: int, size: int) -> List[Workflow]:
        offset = (page - 1) * size
        return self.db.query(Workflow).filter(Workflow.user_id == user_id).offset(offset).limit(size).all()
    
    def get_active_workflows(self) -> List[Workflow]:
        return self.db.query(Workflow).filter(Workflow.status == "ACTIVE").all()
    
    def update_status(self, workflow_id: str, status: str, state: str):
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.status = status
            workflow.current_state = state
            self.db.commit()
    
    def complete_workflow(self, workflow_id: str, result_data: Dict[str, Any]):
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.status = "COMPLETED"
            workflow.current_state = "COMPLETED"
            workflow.completed_at = datetime.now()
            self.db.commit()
    
    def fail_workflow(self, workflow_id: str, error_message: str):
        workflow = self.get_by_id(workflow_id)
        if workflow:
            workflow.status = "FAILED"
            workflow.current_state = "FAILED"
            self.db.commit()
    
    def delete(self, workflow_id: str):
        workflow = self.get_by_id(workflow_id)
        if workflow:
            self.db.delete(workflow)
            self.db.commit()


class SQLAlchemyTaskRepository(TaskRepository):
    """SQLAlchemy任务仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, task_data: Dict[str, Any]) -> Task:
        task = Task(**task_data)
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_by_id(self, task_id: str) -> Optional[Task]:
        return self.db.query(Task).filter(Task.task_id == task_id).first()
    
    def get_by_workflow_id(self, workflow_id: str) -> List[Task]:
        return self.db.query(Task).filter(Task.workflow_id == workflow_id).all()
    
    def get_pending_tasks(self, workflow_id: str) -> List[Task]:
        return self.db.query(Task).filter(
            and_(Task.workflow_id == workflow_id, Task.status == "PENDING")
        ).all()
    
    def get_completed_tasks(self, workflow_id: str) -> List[Task]:
        return self.db.query(Task).filter(
            and_(Task.workflow_id == workflow_id, Task.status == "COMPLETED")
        ).all()
    
    def get_task_dependencies(self, task_id: str) -> List[Task]:
        task = self.get_by_id(task_id)
        if not task or not task.depends_on:
            return []
        return self.db.query(Task).filter(Task.task_id.in_(task.depends_on)).all()
    
    def update_status(self, task_id: str, status: str, result_data: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
        task = self.get_by_id(task_id)
        if task:
            task.status = status
            if result_data:
                task.result_data = result_data
            if error_message:
                task.error_message = error_message
            if status == "RUNNING":
                task.started_at = datetime.now()
            elif status in ["COMPLETED", "FAILED", "CANCELLED"]:
                task.completed_at = datetime.now()
            self.db.commit()
    
    def increment_retry(self, task_id: str):
        task = self.get_by_id(task_id)
        if task:
            task.retry_count += 1
            self.db.commit()
    
    def count_by_workflow(self, workflow_id: str) -> int:
        return self.db.query(Task).filter(Task.workflow_id == workflow_id).count()


class SQLAlchemyWorkflowEventRepository(WorkflowEventRepository):
    """SQLAlchemy工作流事件仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_event(self, event_data: Dict[str, Any]) -> WorkflowEvent:
        event = WorkflowEvent(**event_data)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def get_by_workflow_id(self, workflow_id: str, limit: int = 100) -> List[WorkflowEvent]:
        return self.db.query(WorkflowEvent).filter(
            WorkflowEvent.workflow_id == workflow_id
        ).order_by(WorkflowEvent.created_at.desc()).limit(limit).all()
    
    def get_by_event_type(self, event_type: str, limit: int = 100) -> List[WorkflowEvent]:
        return self.db.query(WorkflowEvent).filter(
            WorkflowEvent.event_type == event_type
        ).order_by(WorkflowEvent.created_at.desc()).limit(limit).all()
    
    def clear_events(self, workflow_id: str):
        self.db.query(WorkflowEvent).filter(
            WorkflowEvent.workflow_id == workflow_id
        ).delete()
        self.db.commit()


class SQLAlchemySummaryRepository(SummaryRepository):
    """SQLAlchemy摘要仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_summary(self, summary_data: Dict[str, Any]) -> Summary:
        summary = Summary(**summary_data)
        self.db.add(summary)
        self.db.commit()
        self.db.refresh(summary)
        return summary
    
    def get_by_session_id(self, session_id: str) -> Optional[Summary]:
        return self.db.query(Summary).filter(
            Summary.session_id == session_id
        ).order_by(Summary.created_at.desc()).first()
    
    def get_by_workflow_id(self, workflow_id: str) -> Optional[Summary]:
        return self.db.query(Summary).filter(
            Summary.workflow_id == workflow_id
        ).order_by(Summary.created_at.desc()).first()
    
    def update_summary(self, summary_id: str, summary_text: str, token_count: int):
        summary = self.db.query(Summary).filter(Summary.summary_id == summary_id).first()
        if summary:
            summary.summary_text = summary_text
            summary.token_count = token_count
            self.db.commit()
