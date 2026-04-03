from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List

from app.core.database import get_db
from app.application.task_management.task_app_service import TaskAppService
from app.domain.task_management.service import TaskNotFoundException, PermissionDeniedException

router = APIRouter(prefix="/api/v1/tasks", tags=["task_management"])


@router.get("/current-session", response_model=Optional[dict])
async def get_current_session_tasks(
    session_id: str = Query(..., description="会话 ID"),
    user_id: str = Query(..., description="用户 ID"),
    include_deleted: bool = Query(False, description="是否包含已删除"),
    db: AsyncSession = Depends(get_db)
):
    """获取当前会话的任务"""
    try:
        app_service = TaskAppService(db)
        result = await app_service.get_current_session_tasks(session_id, user_id, include_deleted)
        if not result:
            return {}
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query", response_model=dict)
async def query_tasks(
    user_id: str = Query(..., description="用户 ID"),
    session_id: Optional[str] = Query(None, description="会话 ID 过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    offset: int = Query(0, description="偏移量"),
    limit: int = Query(20, description="每页数量"),
    db: AsyncSession = Depends(get_db)
):
    """查询任务列表"""
    try:
        app_service = TaskAppService(db)
        
        # 如果提供了 session_id，使用 get_tasks_by_session
        if session_id:
            tasks = await app_service.get_tasks_by_session(session_id, user_id)
            return {
                "tasks": tasks,
                "total": len(tasks),
                "offset": offset,
                "limit": limit
            }
        
        # 否则使用 get_tasks_by_user
        result = await app_service.get_tasks_by_user(user_id, status, limit, offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}/status", response_model=dict)
async def update_task_status(
    task_id: str,
    user_id: str = Query(..., description="用户 ID"),
    status: str = Query(..., description="新状态"),
    version: int = Query(..., description="期望版本号"),
    progress: Optional[int] = Query(None, description="新进度"),
    task_result: Optional[str] = Query(None, description="任务结果"),
    db: AsyncSession = Depends(get_db)
):
    """更新任务状态"""
    try:
        app_service = TaskAppService(db)
        result = await app_service.update_task_status(
            task_id=task_id,
            status=status,
            user_id=user_id,
            version=version,
            progress=progress,
            task_result=task_result
        )
        return result
    except TaskNotFoundException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    except PermissionDeniedException:
        raise HTTPException(status_code=403, detail="You don't have permission to update this task")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=dict)
async def create_task(
    session_id: str = Query(..., description="会话 ID"),
    user_id: str = Query(..., description="用户 ID"),
    task_name: str = Query(..., description="任务名称"),
    description: Optional[str] = Query(None, description="任务描述"),
    parent_task_id: Optional[str] = Query(None, description="父任务 ID"),
    db: AsyncSession = Depends(get_db)
):
    """创建任务"""
    try:
        app_service = TaskAppService(db)
        result = await app_service.create_task(
            session_id=session_id,
            user_id=user_id,
            task_name=task_name,
            description=description,
            parent_task_id=parent_task_id
        )
        return result
    except TaskNotFoundException:
        raise HTTPException(status_code=404, detail=f"Parent task not found")
    except PermissionDeniedException:
        raise HTTPException(status_code=403, detail="You don't have permission to create subtask for this parent task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{task_id}/progress", response_model=dict)
async def update_task_progress(
    task_id: str,
    user_id: str = Query(..., description="用户 ID"),
    progress: int = Query(..., description="新进度"),
    db: AsyncSession = Depends(get_db)
):
    """更新任务进度"""
    try:
        app_service = TaskAppService(db)
        result = await app_service.update_task_progress(
            task_id=task_id,
            progress=progress,
            user_id=user_id
        )
        return result
    except TaskNotFoundException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    except PermissionDeniedException:
        raise HTTPException(status_code=403, detail="You don't have permission to update this task")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    user_id: str = Query(..., description="用户 ID"),
    db: AsyncSession = Depends(get_db)
):
    """删除任务"""
    try:
        app_service = TaskAppService(db)
        await app_service.delete_task(task_id, user_id)
        return {"message": "Task deleted successfully"}
    except TaskNotFoundException:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    except PermissionDeniedException:
        raise HTTPException(status_code=403, detail="You don't have permission to delete this task")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
