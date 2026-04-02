from typing import List, Dict, Any, Optional
import httpx
from app.domain.mcp.protocol_adapter import MCPProtocolAdapter
from app.domain.mcp.models import ToolDefinition, MCPToolResult


class MCPv1_0Adapter(MCPProtocolAdapter):
    def __init__(self):
        self.client: Optional[httpx.AsyncClient] = None
        self.server_url: str = ""
    
    async def connect(self, server_url: str) -> Any:
        """
        建立与 MCP 服务器的连接
        
        Args:
            server_url: 服务器 URL
            
        Returns:
            Any: 连接对象
        """
        self.server_url = server_url
        self.client = httpx.AsyncClient()
        return self.client
    
    async def discover_tools(self) -> List[ToolDefinition]:
        """
        发现可用工具列表
        
        Returns:
            List[ToolDefinition]: 工具定义列表
        """
        if not self.client or not self.server_url:
            raise ValueError("Not connected to server")
        
        try:
            response = await self.client.get(f"{self.server_url}/api/v1/mcp/tools")
            response.raise_for_status()
            data = response.json()
            
            tools = []
            for tool_data in data.get("tools", []):
                tool = ToolDefinition(
                    name=tool_data.get("name"),
                    description=tool_data.get("description"),
                    input_schema=tool_data.get("inputSchema", {}),
                    output_schema=tool_data.get("outputSchema"),
                    is_global=tool_data.get("isGlobal", False)
                )
                tools.append(tool)
            
            return tools
        except Exception as e:
            print(f"Error discovering tools: {e}")
            return []
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> MCPToolResult:
        """
        调用指定工具
        
        Args:
            tool_name: 工具名称
            args: 工具参数
            
        Returns:
            MCPToolResult: 工具调用结果
        """
        if not self.client or not self.server_url:
            return MCPToolResult(
                success=False,
                error="Not connected to server"
            )
        
        try:
            response = await self.client.post(
                f"{self.server_url}/api/v1/mcp/tools/{tool_name}/call",
                json=args
            )
            
            if response.status_code == 200:
                data = response.json()
                return MCPToolResult(
                    success=True,
                    data=data
                )
            else:
                return MCPToolResult(
                    success=False,
                    error=f"HTTP {response.status_code}: {response.text}"
                )
        except Exception as e:
            return MCPToolResult(
                success=False,
                error=str(e)
            )
    
    async def disconnect(self):
        """
        断开连接并清理资源
        """
        if self.client:
            await self.client.aclose()
            self.client = None
        self.server_url = ""
