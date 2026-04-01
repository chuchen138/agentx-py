from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List

from app.application.workflow.summary_app_service import SummaryAppService
from app.domain.workflow.model.schemas import SummaryDTO

router = APIRouter(prefix="/api/v1", tags=["summary"])


@router.get("/sessions/{session_id}/summaries", response_model=SummaryDTO)
def get_session_summary(
    session_id: str,
    summary_service: SummaryAppService = Depends()
):
    """获取会话摘要"""
    summary = summary_service.get_summary(session_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary for session {session_id} not found")
    return summary


@router.get("/workflows/{workflow_id}/summaries", response_model=SummaryDTO)
def get_workflow_summary(
    workflow_id: str,
    summary_service: SummaryAppService = Depends()
):
    """获取工作流摘要"""
    summary = summary_service.get_summary_by_workflow(workflow_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Summary for workflow {workflow_id} not found")
    return summary


@router.post("/sessions/{session_id}/summaries/regenerate", response_model=SummaryDTO)
def regenerate_summary(
    session_id: str,
    strategy: str = "token",
    summary_service: SummaryAppService = Depends()
):
    """重新生成摘要"""
    try:
        summary = summary_service.regenerate_summary(session_id, strategy)
        return summary
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/summaries/{summary_id}")
def delete_summary(
    summary_id: str,
    summary_service: SummaryAppService = Depends()
):
    """删除摘要"""
    try:
        summary_service.delete_summary(summary_id)
        return {"message": f"Summary {summary_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/summaries", response_model=List[SummaryDTO])
def list_summaries(
    user_id: str = Query(..., description="User ID"),
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    summary_service: SummaryAppService = Depends()
):
    """获取用户摘要列表"""
    try:
        summaries = summary_service.list_summaries(user_id, page, size)
        return summaries
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
