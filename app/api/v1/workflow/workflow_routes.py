from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from app.application.workflow.workflow_app_service import WorkflowAppService
from app.domain.workflow.model.schemas import WorkflowDTO, WorkflowCreateRequest

router = APIRouter(prefix="/api/v1/workflows", tags=["workflow"])


@router.post("", response_model=WorkflowDTO)
def create_workflow(
    request: WorkflowCreateRequest,
    workflow_service: WorkflowAppService = Depends()
):
    """创建工作流"""
    try:
        workflow = workflow_service.create_workflow(
            user_id=request.user_id,
            agent_id=request.agent_id,
            session_id=request.session_id
        )
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{workflow_id}", response_model=WorkflowDTO)
def get_workflow(
    workflow_id: str,
    workflow_service: WorkflowAppService = Depends()
):
    """获取工作流详情"""
    workflow = workflow_service.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
    return workflow


@router.get("", response_model=List[WorkflowDTO])
def list_workflows(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[str] = Query(None),
    workflow_service: WorkflowAppService = Depends()
):
    """获取用户工作流列表"""
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    try:
        workflows = workflow_service.list_user_workflows(user_id, page, size)
        return workflows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions/{session_id}/workflows", response_model=List[WorkflowDTO])
def list_session_workflows(
    session_id: str,
    workflow_service: WorkflowAppService = Depends()
):
    """获取会话工作流列表"""
    try:
        workflows = workflow_service.list_session_workflows(session_id)
        return workflows
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: str,
    workflow_service: WorkflowAppService = Depends()
):
    """删除工作流"""
    try:
        # 这里需要实现删除工作流的逻辑
        return {"message": f"Workflow {workflow_id} deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/cancel")
def cancel_workflow(
    workflow_id: str,
    reason: str,
    workflow_service: WorkflowAppService = Depends()
):
    """取消工作流"""
    try:
        workflow_service.cancel_workflow(workflow_id, reason)
        return {"message": f"Workflow {workflow_id} cancelled"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/retry", response_model=WorkflowDTO)
def retry_workflow(
    workflow_id: str,
    workflow_service: WorkflowAppService = Depends()
):
    """重试工作流"""
    try:
        workflow = workflow_service.retry_workflow(workflow_id)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{workflow_id}/replay", response_model=WorkflowDTO)
def replay_workflow(
    workflow_id: str,
    workflow_service: WorkflowAppService = Depends()
):
    """重放工作流"""
    try:
        workflow = workflow_service.replay_workflow(workflow_id)
        return workflow
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
