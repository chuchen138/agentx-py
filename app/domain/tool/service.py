from typing import Optional, List, Dict, Any
from app.domain.tool.model import ToolEntity, ToolVersionEntity, UserToolEntity
from app.domain.tool.repository import ToolRepository, ToolVersionRepository, UserToolRepository
from app.domain.tool.enums import ToolStatus, ToolVersionStatus
from app.domain.tool.schemas.schemas import CreateToolRequest, UpdateToolRequest, ToolVersionRequest


class ToolOperationResult:
    def __init__(self, tool: Optional[ToolEntity] = None, need_state_transition: bool = False, error_message: Optional[str] = None):
        self.tool = tool
        self.need_state_transition = need_state_transition
        self.error_message = error_message


class ToolDomainService:
    def __init__(self, tool_repository: ToolRepository):
        self.tool_repository = tool_repository

    async def create_tool(self, user_id: int, request: CreateToolRequest) -> ToolOperationResult:
        try:
            # 验证工具名称是否为空
            if not request.name:
                return ToolOperationResult(error_message="工具名称不能为空")

            # 验证 GitHub URL 是否有效
            if request.upload_type == "GITHUB" and not request.upload_url.startswith("https://github.com/"):
                return ToolOperationResult(error_message="GitHub URL 必须以 https://github.com/ 开头")

            # 创建工具实体
            tool = ToolEntity(
                name=request.name,
                icon=request.icon,
                subtitle=request.subtitle,
                description=request.description,
                user_id=user_id,
                labels=request.labels or [],
                tool_type=request.tool_type.value,
                upload_type=request.upload_type.value,
                upload_url=request.upload_url,
                install_command=request.install_command.model_dump() if request.install_command else None,
                tool_list=[t.model_dump() for t in request.tool_list] if request.tool_list else [],
                status=ToolStatus.WAITING_REVIEW.value
            )

            created_tool = await self.tool_repository.create(tool)
            return ToolOperationResult(tool=created_tool, need_state_transition=True)
        except Exception as e:
            return ToolOperationResult(error_message=str(e))

    async def update_tool(self, tool_id: int, user_id: int, request: UpdateToolRequest) -> Optional[ToolEntity]:
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool:
            return None

        # 检查权限
        if tool.user_id != user_id:
            return None

        # 更新字段
        if request.name is not None:
            tool.name = request.name
        if request.icon is not None:
            tool.icon = request.icon
        if request.subtitle is not None:
            tool.subtitle = request.subtitle
        if request.description is not None:
            tool.description = request.description

        return await self.tool_repository.update(tool)

    async def delete_tool(self, tool_id: int, user_id: int) -> bool:
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool:
            return False

        # 检查权限
        if tool.user_id != user_id:
            return False

        return await self.tool_repository.delete(tool_id)

    async def get_tool_by_id(self, tool_id: int) -> Optional[ToolEntity]:
        return await self.tool_repository.get_by_id(tool_id)

    async def get_user_tools(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        return await self.tool_repository.get_by_user_id(user_id, skip, limit)

    async def get_market_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        return await self.tool_repository.get_market_tools(skip, limit)

    async def get_pending_review_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        return await self.tool_repository.get_pending_review_tools(skip, limit)

    async def get_statistics(self) -> Dict[str, int]:
        return await self.tool_repository.get_statistics()


class ToolVersionDomainService:
    def __init__(self, tool_version_repository: ToolVersionRepository, tool_repository: ToolRepository):
        self.tool_version_repository = tool_version_repository
        self.tool_repository = tool_repository

    async def create_version(self, user_id: int, request: ToolVersionRequest) -> Optional[ToolVersionEntity]:
        # 检查工具是否存在且属于当前用户
        tool = await self.tool_repository.get_by_id(request.tool_id)
        if not tool or tool.user_id != user_id:
            return None

        # 创建版本实体
        version = ToolVersionEntity(
            tool_id=request.tool_id,
            version_number=request.version_number,
            config=request.config,
            status=ToolVersionStatus.DRAFT.value
        )

        return await self.tool_version_repository.create(version)

    async def publish_version(self, version_id: int, user_id: int) -> Optional[ToolVersionEntity]:
        version = await self.tool_version_repository.get_by_id(version_id)
        if not version:
            return None

        # 检查工具权限
        tool = await self.tool_repository.get_by_id(version.tool_id)
        if not tool or tool.user_id != user_id:
            return None

        # 更新状态为已发布
        version.status = ToolVersionStatus.PUBLISHED.value
        return await self.tool_version_repository.update(version)

    async def rollback_version(self, version_id: int, user_id: int) -> Optional[ToolVersionEntity]:
        version = await self.tool_version_repository.get_by_id(version_id)
        if not version:
            return None

        # 检查工具权限
        tool = await self.tool_repository.get_by_id(version.tool_id)
        if not tool or tool.user_id != user_id:
            return None

        # 标记当前已发布版本为归档
        published_version = await self.tool_version_repository.get_published_version(version.tool_id)
        if published_version:
            published_version.status = ToolVersionStatus.ARCHIVED.value
            await self.tool_version_repository.update(published_version)

        # 发布当前版本
        version.status = ToolVersionStatus.PUBLISHED.value
        return await self.tool_version_repository.update(version)

    async def get_tool_versions(self, tool_id: int, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolVersionEntity]:
        # 检查工具权限
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool or tool.user_id != user_id:
            return []

        return await self.tool_version_repository.get_by_tool_id(tool_id, skip, limit)


class UserToolDomainService:
    def __init__(self, user_tool_repository: UserToolRepository, tool_repository: ToolRepository):
        self.user_tool_repository = user_tool_repository
        self.tool_repository = tool_repository

    async def install_tool(self, user_id: int, tool_id: int) -> Optional[UserToolEntity]:
        # 检查工具是否存在且已发布
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool or tool.status != ToolStatus.PUBLISHED.value:
            return None

        # 检查是否已经安装
        if await self.user_tool_repository.is_tool_installed(user_id, tool_id):
            return None

        # 创建用户工具关系
        user_tool = UserToolEntity(
            user_id=user_id,
            tool_id=tool_id
        )

        return await self.user_tool_repository.create(user_tool)

    async def uninstall_tool(self, user_id: int, tool_id: int) -> bool:
        # 检查工具是否存在
        tool = await self.tool_repository.get_by_id(tool_id)
        if not tool:
            return False

        # 不允许卸载自己创建的工具
        if tool.user_id == user_id:
            return False

        return await self.user_tool_repository.delete(user_id, tool_id)

    async def get_user_installed_tools(self, user_id: int) -> List[UserToolEntity]:
        return await self.user_tool_repository.get_user_installed_tools(user_id)

    async def is_tool_installed(self, user_id: int, tool_id: int) -> bool:
        return await self.user_tool_repository.is_tool_installed(user_id, tool_id)