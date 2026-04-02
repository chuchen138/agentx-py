import asyncio
from typing import Optional
from .events import ExecutionStartEvent, ExecutionEndEvent, ModelCallEvent, ToolCallEvent


class EventPublisher:
    def __init__(self, queue_size: int = 10000):
        self.queue = asyncio.Queue(maxsize=queue_size)
        self.enabled = True
        
    async def publish(self, event: any) -> bool:
        """发布事件到队列"""
        if not self.enabled:
            return False
        
        try:
            # 队列满时降级，避免阻塞主流程
            if self.queue.full():
                # 丢弃低优先级事件，保留执行结束事件
                if not isinstance(event, (ExecutionEndEvent, ModelCallEvent)):
                    return False
                
                # 尝试等待一小段时间
                try:
                    await asyncio.wait_for(self.queue.put(event), timeout=0.1)
                    return True
                except asyncio.TimeoutError:
                    return False
            else:
                await self.queue.put(event)
                return True
        except Exception:
            # 发布失败不影响主流程
            return False
        
    async def get(self) -> Optional[any]:
        """从队列获取事件"""
        try:
            return await self.queue.get()
        except Exception:
            return None
        
    def qsize(self) -> int:
        """获取队列大小"""
        return self.queue.qsize()
        
    def enable(self):
        """启用发布器"""
        self.enabled = True
        
    def disable(self):
        """禁用发布器"""
        self.enabled = False
