from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_

from app.domain.task_management.model.task_entity import TaskEntity
from app.domain.task_management.model.task_aggregate import TaskAggregate
from app.domain.task_management.constant.task_status import TaskStatus


class TaskRepository:
    """任务数据访问层"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def find_by_id(self, task_id: str) -> Optional[TaskEntity]:
        """根据 ID 查找任务"""
        result = await self.db.execute(
            select(TaskEntity).where(
                and_(
                    TaskEntity.id == task_id,
                    TaskEntity.deleted_at == None
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def find_aggregate_by_session(self, session_id: str, user_id: str) -> Optional[TaskAggregate]:
        """查找会话的任务聚合"""
        # 查找最新的父任务（parent_task_id 为空）
        parent_result = await self.db.execute(
            select(TaskEntity).where(
                and_(
                    TaskEntity.session_id == session_id,
                    TaskEntity.user_id == user_id,
                    TaskEntity.parent_task_id == None,
                    TaskEntity.deleted_at == None
                )
            ).order_by(TaskEntity.created_at.desc()).limit(1)
        )
        parent_task = parent_result.scalar_one_or_none()
        
        if not parent_task:
            return None
        
        # 查找子任务
        sub_result = await self.db.execute(
            select(TaskEntity).where(
                and_(
                    TaskEntity.parent_task_id == parent_task.id,
                    TaskEntity.deleted_at == None
                )
            )
        )
        sub_tasks = sub_result.scalars().all()
        
        return TaskAggregate(parent_task, sub_tasks)
    
    async def find_subtasks(self, parent_task_id: str) -> List[TaskEntity]:
        """查找子任务"""
        result = await self.db.execute(
            select(TaskEntity).where(
                and_(
                    TaskEntity.parent_task_id == parent_task_id,
                    TaskEntity.deleted_at == None
                )
            )
        )
        return result.scalars().all()
    
    async def save(self, task: TaskEntity) -> TaskEntity:
        """保存任务"""
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        return task
    
    async def bulk_update_statuses(self, task_ids: List[str], new_status: TaskStatus):
        """批量更新任务状态"""
        from sqlalchemy import update
        await self.db.execute(
            update(TaskEntity)
            .where(
                and_(
                    TaskEntity.id.in_(task_ids),
                    TaskEntity.deleted_at == None
                )
            )
            .values(status=new_status.value)
        )
        await self.db.commit()
    
    async def soft_delete(self, task_id: str):
        """软删除任务"""
        from sqlalchemy import update
        from datetime import datetime
        
        # 先删除子任务
        await self.db.execute(
            update(TaskEntity)
            .where(TaskEntity.parent_task_id == task_id)
            .values(deleted_at=datetime.now())
        )
        
        # 再删除父任务
        await self.db.execute(
            update(TaskEntity)
            .where(TaskEntity.id == task_id)
            .values(deleted_at=datetime.now())
        )
        
        await self.db.commit()
    
    async def find_by_session(self, session_id: str, user_id: str, include_deleted: bool = False) -> List[TaskEntity]:
        """查找会话的所有任务"""
        query = select(TaskEntity).where(
            and_(
                TaskEntity.session_id == session_id,
                TaskEntity.user_id == user_id
            )
        )
        
        if not include_deleted:
            query = query.where(TaskEntity.deleted_at == None)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def find_by_user(self, user_id: str, status: Optional[TaskStatus] = None, limit: int = 20, offset: int = 0) -> List[TaskEntity]:
        """按用户和状态查询任务"""
        query = select(TaskEntity).where(
            and_(
                TaskEntity.user_id == user_id,
                TaskEntity.deleted_at == None
            )
        )
        
        if status:
            query = query.where(TaskEntity.status == status.value)
        
        query = query.order_by(TaskEntity.created_at.desc()).limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
