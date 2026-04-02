from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from app.domain.mcp.models import ToolDefinition, MCPToolResult


class MCPProtocolAdapter(ABC):
    @abstractmethod
    async def connect(self, server_url: str) -> Any:
        """
        建立与 MCP 服务器的连接
        
        Args:
            server_url: 服务器 URL
            
        Returns:
            Any: 连接对象
        """
        pass
    
    @abstractmethod
    async def discover_tools(self) -> List[ToolDefinition]:
        """
        发现可用工具列表
        
        Returns:
            List[ToolDefinition]: 工具定义列表
        """
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> MCPToolResult:
        """
        调用指定工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            MCPToolResult: 工具调用结果
        """
        pass
    
    @abstractmethod
    async def disconnect(self):
        """
        断开连接并清理资源
        """
        pass
