from typing import List, Optional
import asyncio
from app.domain.tool.service import ToolDomainService, ToolVersionDomainService, UserToolDomainService
from app.domain.tool.schemas.schemas import (
    CreateToolRequest, UpdateToolRequest, ToolResponse, ToolVersionRequest, ToolVersionResponse,
    InstallToolRequest, UninstallToolRequest, ToolMarketResponse, ToolReviewRequest
)
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class ToolAppService:
    def __init__(
        self,
        tool_domain_service: ToolDomainService,
        tool_version_domain_service: ToolVersionDomainService,
        user_tool_domain_service: UserToolDomainService,
        tool_state_machine_app_service: 'ToolStateStateMachineAppService'
    ):
        self.tool_domain_service = tool_domain_service
        self.tool_version_domain_service = tool_version_domain_service
        self.user_tool_domain_service = user_tool_domain_service
        self.tool_state_machine_app_service = tool_state_machine_app_service

    async def upload_tool(self, user_id: int, request: CreateToolRequest) -> Optional[ToolResponse]:
        """
        上传工具
        """
        result = await self.tool_domain_service.create_tool(user_id, request)
        if result.error_message:
            return None

        # 触发状态机处理
        if result.need_state_transition:
            await self.tool_state_machine_app_service.submit_tool_for_processing(result.tool)

        return self._convert_to_response(result.tool)

    async def get_tool_detail(self, tool_id: int, user_id: int) -> Optional[ToolResponse]:
        """
        获取工具详情
        """
        tool = await self.tool_domain_service.get_tool_by_id(tool_id)
        if not tool:
            return None

        # 检查权限（只能查看自己的工具或已发布的工具）
        if tool.user_id != user_id and tool.status != ToolStatus.PUBLISHED.value:
            return None

        return self._convert_to_response(tool)

    async def get_user_tools(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolResponse]:
        """
        获取用户工具列表
        """
        tools = await self.tool_domain_service.get_user_tools(user_id, skip, limit)
        return [self._convert_to_response(tool) for tool in tools]

    async def update_tool(self, tool_id: int, user_id: int, request: UpdateToolRequest) -> Optional[ToolResponse]:
        """
        更新工具
        """
        tool = await self.tool_domain_service.update_tool(tool_id, user_id, request)
        if not tool:
            return None

        return self._convert_to_response(tool)

    async def delete_tool(self, tool_id: int, user_id: int) -> bool:
        """
        删除工具
        """
        return await self.tool_domain_service.delete_tool(tool_id, user_id)

    async def get_market_tools(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolMarketResponse]:
        """
        获取工具市场
        """
        tools = await self.tool_domain_service.get_market_tools(skip, limit)
        market_tools = []

        for tool in tools:
            # 检查用户是否已安装
            is_installed = await self.user_tool_domain_service.is_tool_installed(user_id, tool.id)
            # 计算安装数量（模拟）
            install_count = 0  # 实际项目中需要从数据库查询

            market_tool = ToolMarketResponse(
                id=tool.id,
                name=tool.name,
                icon=tool.icon,
                subtitle=tool.subtitle,
                description=tool.description,
                tool_type=tool.tool_type,
                install_count=install_count,
                is_installed=is_installed
            )
            market_tools.append(market_tool)

        return market_tools

    async def install_market_tool(self, user_id: int, request: InstallToolRequest) -> bool:
        """
        安装市场工具
        """
        user_tool = await self.user_tool_domain_service.install_tool(user_id, request.tool_id)
        return user_tool is not None

    async def uninstall_tool(self, user_id: int, request: UninstallToolRequest) -> bool:
        """
        卸载工具
        """
        return await self.user_tool_domain_service.uninstall_tool(user_id, request.tool_id)

    def _convert_to_response(self, tool: ToolEntity) -> ToolResponse:
        """
        转换工具实体为响应对象
        """
        return ToolResponse(
            id=tool.id,
            name=tool.name,
            icon=tool.icon,
            subtitle=tool.subtitle,
            description=tool.description,
            user_id=tool.user_id,
            labels=tool.labels,
            tool_type=tool.tool_type,
            upload_type=tool.upload_type,
            upload_url=tool.upload_url,
            install_command=tool.install_command,
            tool_list=tool.tool_list,
            status=tool.status,
            is_office=tool.is_office,
            reject_reason=tool.reject_reason,
            failed_step_status=tool.failed_step_status,
            mcp_server_name=tool.mcp_server_name,
            is_global=tool.is_global,
            created_at=tool.created_at,
            updated_at=tool.updated_at
        )


class ToolVersionService:
    def __init__(self, tool_version_domain_service: ToolVersionDomainService):
        self.tool_version_domain_service = tool_version_domain_service

    async def create_tool_version(self, user_id: int, request: ToolVersionRequest) -> Optional[ToolVersionResponse]:
        """
        创建工具版本
        """
        version = await self.tool_version_domain_service.create_version(user_id, request)
        if not version:
            return None

        return self._convert_to_response(version)

    async def get_tool_versions(self, tool_id: int, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolVersionResponse]:
        """
        获取工具版本列表
        """
        versions = await self.tool_version_domain_service.get_tool_versions(tool_id, user_id, skip, limit)
        return [self._convert_to_response(version) for version in versions]

    async def publish_tool_version(self, version_id: int, user_id: int) -> Optional[ToolVersionResponse]:
        """
        发布工具版本
        """
        version = await self.tool_version_domain_service.publish_version(version_id, user_id)
        if not version:
            return None

        return self._convert_to_response(version)

    async def rollback_tool_version(self, version_id: int, user_id: int) -> Optional[ToolVersionResponse]:
        """
        回滚工具版本
        """
        version = await self.tool_version_domain_service.rollback_version(version_id, user_id)
        if not version:
            return None

        return self._convert_to_response(version)

    def _convert_to_response(self, version):
        """
        转换版本实体为响应对象
        """
        return ToolVersionResponse(
            id=version.id,
            tool_id=version.tool_id,
            version_number=version.version_number,
            config=version.config,
            status=version.status,
            created_at=version.created_at,
            updated_at=version.updated_at
        )


class ToolStateStateMachineAppService:
    def __init__(self, tool_domain_service: ToolDomainService):
        self.tool_domain_service = tool_domain_service
        self.state_machine = None  # 实际项目中需要初始化状态机

    async def submit_tool_for_processing(self, tool: ToolEntity):
        """
        提交工具进行状态处理
        """
        # 实际项目中这里会启动异步任务处理状态机
        # 暂时同步处理
        if self.state_machine:
            await self.state_machine.process(tool)
            await self.tool_domain_service.tool_repository.update(tool)

    async def review_tool(self, tool_id: int, request: ToolReviewRequest) -> bool:
        """
        手动审核工具
        """
        tool = await self.tool_domain_service.get_tool_by_id(tool_id)
        if not tool:
            return False

        if request.approve:
            tool.status = ToolStatus.PUBLISHED.value
        else:
            tool.status = ToolStatus.REJECTED.value
            tool.reject_reason = request.reject_reason

        await self.tool_domain_service.tool_repository.update(tool)
        return True

    async def get_pending_review_tools(self, skip: int = 0, limit: int = 20):
        """
        获取待审核工具列表
        """
        return await self.tool_domain_service.get_pending_review_tools(skip, limit)