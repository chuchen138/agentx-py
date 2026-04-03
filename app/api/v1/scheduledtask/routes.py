from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.scheduledtask.schemas import (
    CreateScheduledTaskRequest,
    UpdateScheduledTaskRequest,
    ScheduledTaskDTO,
    ScheduledTaskListResponse,
    TaskExecutionLogListResponse,
    RepeatConfigSchema
)
from app.domain.scheduledtask.constant import ScheduleTaskStatus, RepeatType
from app.application.scheduledtask import create_scheduled_task_app_service, ScheduledTaskAppService

router = APIRouter(prefix="/scheduled-tasks", tags=["定时任务管理"])


def get_current_user():
    """获取当前用户（临时实现）"""
    # TODO: 从 JWT token 中解析用户ID
    return "user_123"


def get_scheduled_task_service(db: Session = Depends(get_db)) -> ScheduledTaskAppService:
    """获取定时任务应用服务"""
    return create_scheduled_task_app_service(db)


@router.post("", response_model=ScheduledTaskDTO, status_code=status.HTTP_201_CREATED)
async def create_scheduled_task(
    request: CreateScheduledTaskRequest,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    创建定时任务

    - **agent_id**: Agent ID
    - **session_id**: 会话 ID
    - **content**: 任务内容（1-10000字符）
    - **repeat_type**: 重复类型（immediate, interval, daily, weekly, custom）
    - **repeat_config**: 重复配置
    - **max_retry_count**: 最大重试次数（默认3）
    - **timeout_minutes**: 超时时间（分钟，默认30）
    """
    try:
        return service.create_task(request, user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("", response_model=ScheduledTaskListResponse)
async def list_scheduled_tasks(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    status: Optional[ScheduleTaskStatus] = Query(None, description="状态过滤"),
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    获取定时任务列表

    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认10，最大100）
    - **status**: 状态过滤（可选：pending, running, completed, failed, paused）
    """
    return service.list_tasks(user_id, page, page_size, status)


@router.get("/{task_id}", response_model=ScheduledTaskDTO)
async def get_scheduled_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    获取定时任务详情

    - **task_id**: 任务ID
    """
    task = service.get_task(task_id, user_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=ScheduledTaskDTO)
async def update_scheduled_task(
    task_id: str,
    request: UpdateScheduledTaskRequest,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    更新定时任务

    - **task_id**: 任务ID
    - **content**: 任务内容（可选）
    - **repeat_type**: 重复类型（可选）
    - **repeat_config**: 重复配置（可选）
    - **max_retry_count**: 最大重试次数（可选）
    - **timeout_minutes**: 超时时间（可选）
    """
    try:
        return service.update_task(task_id, request, user_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scheduled_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    删除定时任务

    - **task_id**: 任务ID
    """
    try:
        service.delete_task(task_id, user_id)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{task_id}/pause", status_code=status.HTTP_200_OK)
async def pause_scheduled_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    暂停定时任务

    - **task_id**: 任务ID
    """
    try:
        service.pause_task(task_id, user_id)
        return {"success": True, "message": "Task paused successfully"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{task_id}/resume", status_code=status.HTTP_200_OK)
async def resume_scheduled_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    恢复定时任务

    - **task_id**: 任务ID
    """
    try:
        service.resume_task(task_id, user_id)
        return {"success": True, "message": "Task resumed successfully"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{task_id}/trigger", status_code=status.HTTP_200_OK)
async def trigger_scheduled_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    手动触发定时任务执行

    - **task_id**: 任务ID
    """
    try:
        success = await service.trigger_task_manually(task_id, user_id)
        return {"success": success, "message": "Task triggered successfully" if success else "Task trigger failed"}
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/{task_id}/execution-logs", response_model=TaskExecutionLogListResponse)
async def get_task_execution_logs(
    task_id: str,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(get_current_user),
    service: ScheduledTaskAppService = Depends(get_scheduled_task_service)
):
    """
    获取任务执行历史

    - **task_id**: 任务ID
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认10，最大100）
    """
    try:
        return service.get_execution_logs(task_id, user_id, page, page_size)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        if "permission" in str(e).lower():
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
