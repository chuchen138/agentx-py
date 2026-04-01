from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any

from app.domain.workflow.repository import WorkflowEventRepository
from app.domain.workflow.model.schemas import WorkflowEventDTO

router = APIRouter(prefix="/api/v1", tags=["workflow-event"])


@router.get("/workflows/{workflow_id}/events", response_model=List[WorkflowEventDTO])
def list_workflow_events(
    workflow_id: str,
    limit: int = Query(100, ge=1, le=1000),
    event_repository: WorkflowEventRepository = Depends()
):
    """获取工作流事件列表"""
    try:
        events = event_repository.get_by_workflow_id(workflow_id, limit)
        return [WorkflowEventDTO.model_validate(event) for event in events]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/types", response_model=Dict[str, int])
def get_event_type_statistics(
    event_repository: WorkflowEventRepository = Depends()
):
    """获取事件类型统计"""
    try:
        # 这里需要实现获取事件类型统计的逻辑
        # 暂时返回模拟数据
        return {
            "WORKFLOW_CREATED": 100,
            "TASK_CREATED": 500,
            "TASK_COMPLETED": 450,
            "TASK_FAILED": 50,
            "WORKFLOW_COMPLETED": 90,
            "WORKFLOW_FAILED": 10
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
