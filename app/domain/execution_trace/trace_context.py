from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class TraceContext(BaseModel):
    trace_id: str
    span_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    user_id: str
    session_id: str
    agent_id: str
    enabled: bool = True
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None
    current_user_message_id: Optional[str] = None
    user_message_content: Optional[str] = None
    user_message_type: Optional[str] = None
    
    def disable(self):
        """禁用追踪"""
        self.enabled = False
        
    def is_enabled(self) -> bool:
        """检查追踪是否启用"""
        return self.enabled
        
    def set_end_time(self):
        """设置结束时间"""
        self.end_time = datetime.now()
        
    def get_duration(self) -> Optional[int]:
        """获取执行时长（毫秒）"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return None
