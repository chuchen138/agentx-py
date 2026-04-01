import asyncio
import heapq
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
import uuid

from app.domain.workflow.constant.event_type import WorkflowEventType, EventPriority


class WorkflowEvent:
    """工作流事件"""
    def __init__(self, event_type: WorkflowEventType, workflow_id: str, data: Dict[str, Any], priority: EventPriority = EventPriority.NORMAL):
        self.event_id = str(uuid.uuid4())
        self.event_type = event_type
        self.workflow_id = workflow_id
        self.data = data
        self.timestamp = datetime.now()
        self.priority = priority
    
    def __lt__(self, other):
        """用于优先级队列排序"""
        return self.priority.value < other.priority.value


class AgentEventBus:
    """Agent事件总线"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentEventBus, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._subscribers: Dict[WorkflowEventType, List[Callable]] = {}
            self._event_queue = []  # 使用堆实现优先级队列
            self._running = False
            self._event_loop = asyncio.get_event_loop()
            self._initialized = True
    
    def subscribe(self, event_type: WorkflowEventType, handler: Callable):
        """订阅事件"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)
    
    def unsubscribe(self, event_type: WorkflowEventType, handler: Callable):
        """取消订阅"""
        if event_type in self._subscribers and handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
    
    def publish(self, event_type: WorkflowEventType, workflow_id: str, data: Dict[str, Any], priority: EventPriority = EventPriority.NORMAL):
        """发布事件"""
        event = WorkflowEvent(event_type, workflow_id, data, priority)
        heapq.heappush(self._event_queue, event)
        if not self._running:
            self._running = True
            self._event_loop.create_task(self._process_events())
    
    async def _process_events(self):
        """处理事件循环"""
        while self._running:
            if self._event_queue:
                event = heapq.heappop(self._event_queue)
                await self._dispatch_event(event)
            else:
                await asyncio.sleep(0.01)
    
    async def _dispatch_event(self, event: WorkflowEvent):
        """分发事件到订阅者"""
        handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                # 记录错误但不影响其他处理器
                print(f"Error handling event {event.event_type.value}: {e}")
    
    def stop_event_loop(self):
        """停止事件循环"""
        self._running = False


# 全局事件总线实例
event_bus = AgentEventBus()
