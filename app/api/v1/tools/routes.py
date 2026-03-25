from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List
from app.application.tool.tool_app_service import ToolAppService, ToolVersionService
from app.domain.tool.schemas.schemas import (
    CreateToolRequest, UpdateToolRequest, ToolResponse, ToolVersionRequest, ToolVersionResponse,
    InstallToolRequest, UninstallToolRequest, ToolMarketResponse
)
from app.infrastructure.dependency_injection import get_tool_app_service, get_tool_version_service
from app.api.deps import get_current_user
from app.domain.user.model import UserModel

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])


@router.post("", response_model=ToolResponse)
async def upload_tool(
    request: CreateToolRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    上传工具
    """
    tool = await tool_app_service.upload_tool(current_user.id, request)
    if not tool:
        raise HTTPException(status_code=400, detail="上传工具失败")
    return tool


@router.get("", response_model=List[ToolResponse])
async def get_user_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    获取用户工具列表
    """
    return await tool_app_service.get_user_tools(current_user.id, skip, limit)


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool_detail(
    tool_id: int,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    获取工具详情
    """
    tool = await tool_app_service.get_tool_detail(tool_id, current_user.id)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在")
    return tool


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: int,
    request: UpdateToolRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    更新工具
    """
    tool = await tool_app_service.update_tool(tool_id, current_user.id, request)
    if not tool:
        raise HTTPException(status_code=404, detail="工具不存在或无权限")
    return tool


@router.delete("/{tool_id}")
async def delete_tool(
    tool_id: int,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    删除工具
    """
    success = await tool_app_service.delete_tool(tool_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="工具不存在或无权限")
    return {"message": "工具删除成功"}


@router.get("/market/list", response_model=List[ToolMarketResponse])
async def get_market_tools(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    获取工具市场
    """
    return await tool_app_service.get_market_tools(current_user.id, skip, limit)


@router.post("/market/install")
async def install_market_tool(
    request: InstallToolRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    安装市场工具
    """
    success = await tool_app_service.install_market_tool(current_user.id, request)
    if not success:
        raise HTTPException(status_code=400, detail="安装工具失败")
    return {"message": "工具安装成功"}


@router.post("/market/uninstall")
async def uninstall_tool(
    request: UninstallToolRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_app_service: ToolAppService = Depends(get_tool_app_service)
):
    """
    卸载工具
    """
    success = await tool_app_service.uninstall_tool(current_user.id, request)
    if not success:
        raise HTTPException(status_code=400, detail="卸载工具失败")
    return {"message": "工具卸载成功"}


# 工具版本路由
@router.get("/{tool_id}/versions", response_model=List[ToolVersionResponse])
async def get_tool_versions(
    tool_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    tool_version_service: ToolVersionService = Depends(get_tool_version_service)
):
    """
    获取工具版本列表
    """
    return await tool_version_service.get_tool_versions(tool_id, current_user.id, skip, limit)


@router.post("/{tool_id}/versions", response_model=ToolVersionResponse)
async def create_tool_version(
    tool_id: int,
    request: ToolVersionRequest,
    current_user: UserModel = Depends(get_current_user),
    tool_version_service: ToolVersionService = Depends(get_tool_version_service)
):
    """
    创建工具版本
    """
    # 确保请求中的 tool_id 与路径参数一致
    request.tool_id = tool_id
    version = await tool_version_service.create_tool_version(current_user.id, request)
    if not version:
        raise HTTPException(status_code=400, detail="创建版本失败")
    return version


@router.post("/versions/{version_id}/publish", response_model=ToolVersionResponse)
async def publish_tool_version(
    version_id: int,
    current_user: UserModel = Depends(get_current_user),
    tool_version_service: ToolVersionService = Depends(get_tool_version_service)
):
    """
    发布工具版本
    """
    version = await tool_version_service.publish_tool_version(version_id, current_user.id)
    if not version:
        raise HTTPException(status_code=400, detail="发布版本失败")
    return version


@router.post("/versions/{version_id}/rollback", response_model=ToolVersionResponse)
async def rollback_tool_version(
    version_id: int,
    current_user: UserModel = Depends(get_current_user),
    tool_version_service: ToolVersionService = Depends(get_tool_version_service)
):
    """
    回滚工具版本
    """
    version = await tool_version_service.rollback_tool_version(version_id, current_user.id)
    if not version:
        raise HTTPException(status_code=400, detail="回滚版本失败")
    return version