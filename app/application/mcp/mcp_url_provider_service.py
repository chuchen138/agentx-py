from app.domain.mcp.enums import ToolType
from app.domain.mcp.tool_classifier import ToolClassifier
from app.infrastructure.mcp.container_service import MockContainerService
from app.infrastructure.mcp.url_builder import MCPUrlBuilder


class McpUrlProviderService:
    def __init__(self):
        self.tool_classifier = ToolClassifier()
        self.container_service = MockContainerService()
        self.url_builder = MCPUrlBuilder()
    
    def get_sse_url(self, tool_name: str, user_id: str) -> str:
        """
        智能获取 MCP 工具的 SSE URL
        
        Args:
            tool_name: 工具名称
            user_id: 用户 ID
            
        Returns:
            str: SSE URL
        """
        # 1. 判断工具类型
        tool_type = self.tool_classifier.classify(tool_name)
        
        # 2. 根据工具类型选择策略
        if tool_type == ToolType.GLOBAL:
            # 全局工具使用审核容器
            container = self.container_service.get_review_container()
            return self.url_builder.build_review_container_url(container)
        elif tool_type == ToolType.USER:
            # 用户工具使用用户容器
            container = self.container_service.get_or_create_user_container(user_id)
            return self.url_builder.build_user_container_url(container)
        else:  # EXTERNAL
            # 外部工具直接使用外部服务器
            server = self.container_service.get_server_for_tool(tool_name)
            if server:
                return self.url_builder.build_external_server_url(server["server_url"])
            raise ValueError(f"No server found for tool: {tool_name}")
