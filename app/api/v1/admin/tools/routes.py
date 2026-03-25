from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.application.tool.tool_app_service import ToolStateStateMachineAppService
from app.domain.tool.schemas.schemas import ToolResponse, ToolReviewRequest, ToolStatisticsDTO
from app.infrastructure.dependency_injection import get_tool_state_machine_app_service, get_tool_app_service
from app.api.deps import get_current_user
from app.domain.user.model import UserModel

router = APIRouter(prefix="/api/v1/admin/tools", tags=["admin-tools"])


@router.get("", response_model=List[ToolResponse])
async def get_all_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    tool_app_service = Depends(get_tool_app_service)
):
    """
    获取所有工具列表
    """
    # 实际项目中需要检查用户是否为管理员
    tools = await tool_app_service.tool_domain_service.get_pending_review_tools(skip, limit)
    return [tool_app_service._convert_to_response(tool) for tool in tools]


@router.get("/pending", response_model=List[ToolResponse])
async def get_pending_review_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    tool_state_machine_app_service: ToolStateStateMachineAppService = Depends(get_tool_state_machine_app_service)
):
    """
    获取待审核工具列表
    """
    # 实际项目中需要检查用户是否为管理员
    tools = await tool_state_machine_app_service.get_pending_review_tools(skip, limit)
    return [tool_app_service._convert_to_response(tool) for tool in tools]


@router.post("/{tool_id}/review")
async def review_tool(
    tool_id: int,
    request: ToolReviewRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_state_machine_app_service: ToolStateStateMachineAppService = Depends(get_tool_state_machine_app_service)
):
    """
    审核工具（通过/拒绝）
    """
    # 实际项目中需要检查用户是否为管理员
    success = await tool_state_machine_app_service.review_tool(tool_id, request)
    if not success:
        raise HTTPException(status_code=404, detail="工具不存在")
    return {"message": "审核成功"}


@router.get("/statistics", response_model=ToolStatisticsDTO)
async def get_tool_statistics(
    current_user: UserModel = Depends(get_current_user),
    tool_app_service = Depends(get_tool_app_service)
):
    """
    获取工具统计数据
    """
    # 实际项目中需要检查用户是否为管理员
    stats = await tool_app_service.tool_domain_service.get_statistics()
    return ToolStatisticsDTO(**stats)