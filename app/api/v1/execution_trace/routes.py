from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime
from app.application.execution_trace.execution_trace_app_service import AgentExecutionTraceAppService
from app.domain.execution_trace.entities import AgentExecutionSummary
from app.api.middleware.auth import get_current_user
from app.domain.user.model import User

router = APIRouter(prefix="/execution-trace", tags=["execution-trace"])


def get_execution_trace_app_service() -> AgentExecutionTraceAppService:
    """获取执行追踪应用服务"""
    # 这里需要依赖注入，暂时返回 None
    # 实际实现中应该通过依赖注入容器获取
    from app.infrastructure.dependency_injection import get_service
    return get_service(AgentExecutionTraceAppService)


@router.get("/trace/{trace_id}")
async def get_execution_trace(
    trace_id: str,
    current_user: User = Depends(get_current_user),
    app_service: AgentExecutionTraceAppService = Depends(get_execution_trace_app_service)
):
    """获取完整的执行链路信息"""
    trace = await app_service.get_execution_trace(trace_id, current_user.id)
    if not trace:
        raise HTTPException(status_code=404, detail="Execution trace not found")
    return trace


@router.get("/history")
async def get_user_execution_history(
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    app_service: AgentExecutionTraceAppService = Depends(get_execution_trace_app_service)
) -> List[AgentExecutionSummary]:
    """分页查询用户的执行历史"""
    return await app_service.get_user_execution_history(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        start_time=start_time,
        end_time=end_time
    )


@router.get("/session/{session_id}")
async def get_session_execution_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    app_service: AgentExecutionTraceAppService = Depends(get_execution_trace_app_service)
) -> List[AgentExecutionSummary]:
    """查询会话的执行历史"""
    return await app_service.get_session_execution_history(session_id, current_user.id)


@router.get("/failed")
async def get_failed_executions(
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    app_service: AgentExecutionTraceAppService = Depends(get_execution_trace_app_service)
) -> List[AgentExecutionSummary]:
    """查询用户的失败执行记录"""
    return await app_service.get_failed_executions(
        user_id=current_user.id,
        limit=limit,
        offset=offset
    )


@router.get("/statistics")
async def get_execution_statistics(
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    app_service: AgentExecutionTraceAppService = Depends(get_execution_trace_app_service)
):
    """获取用户的执行统计信息"""
    return await app_service.get_execution_statistics(
        user_id=current_user.id,
        start_time=start_time,
        end_time=end_time
    )
