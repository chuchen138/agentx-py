from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.task_management.service import TaskDomainService, TaskNotFoundException, PermissionDeniedException
from app.domain.task_management.constant.task_status import TaskStatus
from app.domain.task_management.model.task_aggregate import TaskAggregate
from app.infrastructure.task_management.task_repository import TaskRepository


class TaskAppService:
    """任务应用服务"""
    
    def __init__(self, db: AsyncSession):
        self.repository = TaskRepository(db)
        self.domain_service = TaskDomainService(self.repository)
    
    async def get_current_session_tasks(self, session_id: str, user_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
        """获取当前会话的任务"""
        try:
            aggregate = await self.domain_service.get_task_aggregate(session_id, user_id)
            if not aggregate:
                return None
            
            # 转换为响应格式
            return aggregate.to_dict()
        except Exception as e:
            # 记录异常
            print(f"Error getting current session tasks: {e}")
            raise
    
    async def update_task_status(self, task_id: str, status: str, user_id: str, version: int, progress: Optional[int] = None, task_result: Optional[str] = None) -> Dict[str, Any]:
        """更新任务状态"""
        try:
            # 转换状态枚举
            new_status = TaskStatus(status)
            
            # 更新状态
            task = await self.domain_service.update_task_status(
                task_id=task_id,
                new_status=new_status,
                user_id=user_id,
                expected_version=version,
                progress=progress,
                task_result=task_result
            )
            
            return task.to_dict()
        except TaskNotFoundException:
            raise
        except PermissionDeniedException:
            raise
        except ValueError as e:
            raise
        except Exception as e:
            # 记录异常
            print(f"Error updating task status: {e}")
            raise
    
    async def create_task(self, session_id: str, user_id: str, task_name: str, description: Optional[str] = None, parent_task_id: Optional[str] = None) -> Dict[str, Any]:
        """创建任务"""
        try:
            task = await self.domain_service.create_task(
                session_id=session_id,
                user_id=user_id,
                task_name=task_name,
                description=description,
                parent_task_id=parent_task_id
            )
            
            return task.to_dict()
        except TaskNotFoundException:
            raise
        except PermissionDeniedException:
            raise
        except Exception as e:
            # 记录异常
            print(f"Error creating task: {e}")
            raise
    
    async def update_task_progress(self, task_id: str, progress: int, user_id: str) -> Dict[str, Any]:
        """更新任务进度"""
        try:
            task = await self.domain_service.update_task_progress(
                task_id=task_id,
                progress=progress,
                user_id=user_id
            )
            
            return task.to_dict()
        except TaskNotFoundException:
            raise
        except PermissionDeniedException:
            raise
        except ValueError as e:
            raise
        except Exception as e:
            # 记录异常
            print(f"Error updating task progress: {e}")
            raise
    
    async def delete_task(self, task_id: str, user_id: str):
        """删除任务"""
        try:
            await self.domain_service.delete_task(task_id, user_id)
        except TaskNotFoundException:
            raise
        except PermissionDeniedException:
            raise
        except Exception as e:
            # 记录异常
            print(f"Error deleting task: {e}")
            raise
    
    async def get_tasks_by_session(self, session_id: str, user_id: str, include_deleted: bool = False) -> List[Dict[str, Any]]:
        """获取会话的所有任务"""
        try:
            tasks = await self.domain_service.get_tasks_by_session(session_id, user_id, include_deleted)
            return [task.to_dict() for task in tasks]
        except Exception as e:
            # 记录异常
            print(f"Error getting tasks by session: {e}")
            raise
    
    async def get_tasks_by_user(self, user_id: str, status: Optional[str] = None, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """获取用户的任务"""
        try:
            # 转换状态枚举
            status_enum = TaskStatus(status) if status else None
            
            tasks = await self.domain_service.get_tasks_by_user(user_id, status_enum, limit, offset)
            
            # 计算总数（简化版，实际应该查询 count）
            total = len(tasks)  # 实际应该单独查询总数
            
            return {
                "tasks": [task.to_dict() for task in tasks],
                "total": total,
                "offset": offset,
                "limit": limit
            }
        except Exception as e:
            # 记录异常
            print(f"Error getting tasks by user: {e}")
            raise
