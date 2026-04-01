from typing import List, Optional, Dict, Any

from app.domain.workflow.model.schemas import TaskDTO, TaskStatusDTO
from app.domain.workflow.repository import TaskRepository
from app.domain.workflow.constant.task_status import TaskStatus


class TaskAppService:
    """任务应用服务"""
    
    def __init__(self, task_repository: TaskRepository):
        self.task_repository = task_repository
    
    def get_task(self, task_id: str) -> Optional[TaskDTO]:
        """获取任务详情"""
        task = self.task_repository.get_by_id(task_id)
        if task:
            return TaskDTO.model_validate(task)
        return None
    
    def list_workflow_tasks(self, workflow_id: str) -> List[TaskDTO]:
        """获取工作流任务列表"""
        tasks = self.task_repository.get_by_workflow_id(workflow_id)
        return [TaskDTO.model_validate(task) for task in tasks]
    
    def get_task_status(self, task_id: str) -> TaskStatusDTO:
        """获取任务状态"""
        task = self.task_repository.get_by_id(task_id)
        if task:
            return TaskStatusDTO(
                task_id=task.task_id,
                status=task.status,
                error_message=task.error_message
            )
        raise ValueError(f"Task {task_id} not found")
    
    def retry_task(self, task_id: str) -> TaskDTO:
        """重试任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError(f"Task {task_id} not found")
        
        # 重置任务状态为待执行
        self.task_repository.update_status(
            task_id,
            TaskStatus.PENDING.value,
            error_message=None
        )
        
        # 增加重试次数
        self.task_repository.increment_retry(task_id)
        
        # 返回更新后的任务
        updated_task = self.task_repository.get_by_id(task_id)
        return TaskDTO.model_validate(updated_task)
    
    def cancel_task(self, task_id: str):
        """取消任务"""
        self.task_repository.update_status(
            task_id,
            TaskStatus.CANCELLED.value,
            error_message="Task cancelled by user"
        )
    
    def get_task_dependencies(self, task_id: str) -> List[TaskDTO]:
        """获取任务依赖"""
        dependencies = self.task_repository.get_task_dependencies(task_id)
        return [TaskDTO.model_validate(task) for task in dependencies]
    
    def get_task_dependents(self, task_id: str) -> List[TaskDTO]:
        """获取依赖该任务的任务列表"""
        # 这里需要实现查询依赖该任务的任务
        # 暂时返回空列表
        return []
