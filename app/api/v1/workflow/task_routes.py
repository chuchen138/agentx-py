from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.application.workflow.task_app_service import TaskAppService
from app.domain.workflow.model.schemas import TaskDTO, TaskStatusDTO

router = APIRouter(prefix="/api/v1", tags=["task"])


@router.get("/workflows/{workflow_id}/tasks", response_model=List[TaskDTO])
def list_workflow_tasks(
    workflow_id: str,
    task_service: TaskAppService = Depends()
):
    """获取工作流任务列表"""
    try:
        tasks = task_service.list_workflow_tasks(workflow_id)
        return tasks
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}", response_model=TaskDTO)
def get_task(
    task_id: str,
    task_service: TaskAppService = Depends()
):
    """获取任务详情"""
    task = task_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.get("/tasks/{task_id}/status", response_model=TaskStatusDTO)
def get_task_status(
    task_id: str,
    task_service: TaskAppService = Depends()
):
    """获取任务状态"""
    try:
        status = task_service.get_task_status(task_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/tasks/{task_id}/retry", response_model=TaskDTO)
def retry_task(
    task_id: str,
    task_service: TaskAppService = Depends()
):
    """重试任务"""
    try:
        task = task_service.retry_task(task_id)
        return task
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/tasks/{task_id}/cancel")
def cancel_task(
    task_id: str,
    task_service: TaskAppService = Depends()
):
    """取消任务"""
    try:
        task_service.cancel_task(task_id)
        return {"message": f"Task {task_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/tasks/{task_id}/dependencies", response_model=List[TaskDTO])
def get_task_dependencies(
    task_id: str,
    task_service: TaskAppService = Depends()
):
    """获取任务依赖"""
    try:
        dependencies = task_service.get_task_dependencies(task_id)
        return dependencies
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
