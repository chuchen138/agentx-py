from typing import Optional, List
from datetime import datetime

from app.domain.task_management.model.task_entity import TaskEntity, OptimisticLockException
from app.domain.task_management.model.task_aggregate import TaskAggregate
from app.domain.task_management.constant.task_status import TaskStatus
from app.infrastructure.task_management.task_repository import TaskRepository


class TaskDomainService:
    """任务领域服务"""
    
    def __init__(self, repository: TaskRepository):
        self.repository = repository
    
    async def get_task_aggregate(self, session_id: str, user_id: str) -> Optional[TaskAggregate]:
        """获取任务聚合"""
        return await self.repository.find_aggregate_by_session(session_id, user_id)
    
    async def update_task_status(self, task_id: str, new_status: TaskStatus, user_id: str, expected_version: int, progress: Optional[int] = None, task_result: Optional[str] = None) -> TaskEntity:
        """更新任务状态"""
        # 查找任务
        task = await self.repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundException(f"Task {task_id} not found")
        
        # 权限验证
        if task.user_id != user_id:
            raise PermissionDeniedException("You don't have permission to update this task")
        
        # 更新状态
        task.update_status(new_status, expected_version)
        
        # 更新进度
        if progress is not None:
            if progress < 0 or progress > 100:
                raise ValueError("Progress must be between 0 and 100")
            task.progress = progress
        
        # 更新结果
        if task_result is not None:
            # 截断过长的结果
            if len(task_result) > 65535:
                task_result = task_result[:65532] + "..."
            task.task_result = task_result
        
        # 保存更新
        return await self.repository.save(task)
    
    async def create_task(self, session_id: str, user_id: str, task_name: str, description: Optional[str] = None, parent_task_id: Optional[str] = None) -> TaskEntity:
        """创建任务"""
        # 验证父任务存在且属于同一用户
        if parent_task_id:
            parent_task = await self.repository.find_by_id(parent_task_id)
            if not parent_task:
                raise TaskNotFoundException(f"Parent task {parent_task_id} not found")
            if parent_task.user_id != user_id:
                raise PermissionDeniedException("You don't have permission to create subtask for this parent task")
        
        # 创建任务
        task = TaskEntity(
            session_id=session_id,
            user_id=user_id,
            parent_task_id=parent_task_id,
            task_name=task_name,
            description=description,
            status=TaskStatus.WAITING.value,
            progress=0
        )
        
        return await self.repository.save(task)
    
    async def update_task_progress(self, task_id: str, progress: int, user_id: str) -> TaskEntity:
        """更新任务进度"""
        # 查找任务
        task = await self.repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundException(f"Task {task_id} not found")
        
        # 权限验证
        if task.user_id != user_id:
            raise PermissionDeniedException("You don't have permission to update this task")
        
        # 验证进度范围
        if progress < 0 or progress > 100:
            raise ValueError("Progress must be between 0 and 100")
        
        # 更新进度
        task.progress = progress
        task.updated_at = datetime.now()
        
        return await self.repository.save(task)
    
    async def delete_task(self, task_id: str, user_id: str):
        """删除任务"""
        # 查找任务
        task = await self.repository.find_by_id(task_id)
        if not task:
            raise TaskNotFoundException(f"Task {task_id} not found")
        
        # 权限验证
        if task.user_id != user_id:
            raise PermissionDeniedException("You don't have permission to delete this task")
        
        # 软删除任务
        await self.repository.soft_delete(task_id)
    
    async def get_tasks_by_session(self, session_id: str, user_id: str, include_deleted: bool = False) -> List[TaskEntity]:
        """获取会话的所有任务"""
        return await self.repository.find_by_session(session_id, user_id, include_deleted)
    
    async def get_tasks_by_user(self, user_id: str, status: Optional[TaskStatus] = None, limit: int = 20, offset: int = 0) -> List[TaskEntity]:
        """获取用户的任务"""
        return await self.repository.find_by_user(user_id, status, limit, offset)


class TaskNotFoundException(Exception):
    """任务未找到异常"""
    pass


class PermissionDeniedException(Exception):
    """权限拒绝异常"""
    pass
