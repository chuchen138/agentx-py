from app.domain.tool.model import ToolEntity, ToolVersionEntity, UserToolEntity
from app.domain.tool.schemas.schemas import (
    CreateToolRequest, UpdateToolRequest, ToolResponse,
    ToolVersionRequest, ToolVersionResponse, UserToolResponse
)


class ToolAssembler:
    @staticmethod
    def from_create_request(request: CreateToolRequest, user_id: int) -> ToolEntity:
        """
        从创建请求转换为工具实体
        """
        return ToolEntity(
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
            status="WAITING_REVIEW"
        )

    @staticmethod
    def from_update_request(request: UpdateToolRequest, tool: ToolEntity) -> ToolEntity:
        """
        从更新请求更新工具实体
        """
        if request.name is not None:
            tool.name = request.name
        if request.icon is not None:
            tool.icon = request.icon
        if request.subtitle is not None:
            tool.subtitle = request.subtitle
        if request.description is not None:
            tool.description = request.description
        return tool

    @staticmethod
    def to_response(tool: ToolEntity) -> ToolResponse:
        """
        工具实体转换为响应对象
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


class ToolVersionAssembler:
    @staticmethod
    def from_request(request: ToolVersionRequest) -> ToolVersionEntity:
        """
        从请求转换为版本实体
        """
        return ToolVersionEntity(
            tool_id=request.tool_id,
            version_number=request.version_number,
            config=request.config,
            status="DRAFT"
        )

    @staticmethod
    def to_response(version: ToolVersionEntity) -> ToolVersionResponse:
        """
        版本实体转换为响应对象
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


class UserToolAssembler:
    @staticmethod
    def to_response(user_tool: UserToolEntity) -> UserToolResponse:
        """
        用户工具实体转换为响应对象
        """
        return UserToolResponse(
            id=user_tool.id,
            user_id=user_tool.user_id,
            tool_id=user_tool.tool_id,
            installed_at=user_tool.installed_at
        )