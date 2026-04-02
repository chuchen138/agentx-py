import pytest
import asyncio
from app.infrastructure.mcp.sse_manager import SSEManager


async def test_sse_manager():
    """
    测试 SSE 管理器功能
    """
    manager = SSEManager()
    events = []
    
    def event_handler(event):
        events.append(event)
    
    # 测试连接生成
    connection_id = await manager.connect("http://localhost:8080/api/v1/mcp/sse", event_handler)
    assert connection_id is not None
    assert len(manager.connections) == 1
    
    # 测试断开连接
    manager.disconnect(connection_id)
    assert len(manager.connections) == 0


if __name__ == "__main__":
    asyncio.run(test_sse_manager())
