import asyncio
import httpx
from typing import Optional, Callable, Dict, Any


class SSEManager:
    def __init__(self):
        self.connections: Dict[str, httpx.Client] = {}
        self.retry_count = 5
        self.base_delay = 1  # 基础延迟 1 秒
    
    async def connect(self, sse_url: str, event_handler: Callable[[Dict[str, Any]], None]) -> str:
        """
        建立 SSE 连接
        
        Args:
            sse_url: SSE 连接 URL
            event_handler: 事件处理函数
            
        Returns:
            str: 连接 ID
        """
        connection_id = self._generate_connection_id(sse_url)
        
        async def connect_with_retry(attempt: int = 0):
            try:
                async with httpx.AsyncClient() as client:
                    self.connections[connection_id] = client
                    async with client.stream('GET', sse_url, timeout=None) as response:
                        async for line in response.aiter_lines():
                            if line.strip():
                                event = self._parse_sse_event(line)
                                if event:
                                    event_handler(event)
            except Exception as e:
                print(f"SSE connection error: {e}")
                if attempt < self.retry_count:
                    delay = min(self.base_delay * (2 ** attempt), 30)
                    print(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                    await connect_with_retry(attempt + 1)
                else:
                    print("Max retry attempts reached")
                    if connection_id in self.connections:
                        del self.connections[connection_id]
        
        # 启动连接任务
        asyncio.create_task(connect_with_retry())
        return connection_id
    
    def disconnect(self, connection_id: str):
        """
        断开 SSE 连接
        
        Args:
            connection_id: 连接 ID
        """
        if connection_id in self.connections:
            client = self.connections.pop(connection_id)
            if hasattr(client, 'close'):
                client.close()
    
    def _generate_connection_id(self, sse_url: str) -> str:
        """
        生成连接 ID
        
        Args:
            sse_url: SSE 连接 URL
            
        Returns:
            str: 连接 ID
        """
        import hashlib
        return hashlib.md5(sse_url.encode()).hexdigest()
    
    def _parse_sse_event(self, line: str) -> Optional[Dict[str, Any]]:
        """
        解析 SSE 事件
        
        Args:
            line: SSE 事件行
            
        Returns:
            Optional[Dict[str, Any]]: 解析后的事件
        """
        # 简单的 SSE 事件解析
        # 实际实现需要更复杂的解析逻辑
        if line.startswith('data:'):
            data = line[5:].strip()
            try:
                import json
                return json.loads(data)
            except json.JSONDecodeError:
                return {"data": data}
        return None
