from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.application.mcp.mcp_url_provider_service import McpUrlProviderService
from app.domain.mcp.models import ToolDefinition
from app.infrastructure.mcp.protocol.adapter_factory import MCPAdapterFactory
from app.domain.mcp.enums import MCPProtocolVersion

router = APIRouter(prefix="/mcp", tags=["mcp"])


@router.get("/sse-url")
def get_sse_url(tool_name: str, user_id: str):
    """
    获取 MCP 工具的 SSE URL
    
    Args:
        tool_name: 工具名称
        user_id: 用户 ID
        
    Returns:
        dict: 包含 SSE URL 的响应
    """
    try:
        service = McpUrlProviderService()
        sse_url = service.get_sse_url(tool_name, user_id)
        return {"sse_url": sse_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tools", response_model=List[ToolDefinition])
async def discover_tools(server_url: str, version: str = "1.0"):
    """
    发现 MCP 服务器上的可用工具
    
    Args:
        server_url: MCP 服务器 URL
        version: MCP 协议版本
        
    Returns:
        List[ToolDefinition]: 工具定义列表
    """
    try:
        # 解析协议版本
        protocol_version = MCPProtocolVersion(version)
        
        # 创建适配器并连接
        adapter = MCPAdapterFactory.create_adapter(protocol_version)
        await adapter.connect(server_url)
        
        # 发现工具
        tools = await adapter.discover_tools()
        
        # 断开连接
        await adapter.disconnect()
        
        return tools
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
