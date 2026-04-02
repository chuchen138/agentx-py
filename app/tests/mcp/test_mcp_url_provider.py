import pytest
from app.application.mcp.mcp_url_provider_service import McpUrlProviderService


def test_get_sse_url():
    """
    测试获取 SSE URL 功能
    """
    service = McpUrlProviderService()
    
    # 测试用户工具
    user_tool_url = service.get_sse_url("test_tool", "user123")
    assert user_tool_url == "http://localhost:8081/api/v1/mcp/sse"
    
    # 测试全局工具（由于当前实现默认返回用户工具，所以结果应该相同）
    global_tool_url = service.get_sse_url("global_tool", "user123")
    assert global_tool_url == "http://localhost:8081/api/v1/mcp/sse"
