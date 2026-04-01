from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from app.domain.workflow.repository import SummaryRepository
from app.domain.workflow.event_bus import event_bus
from app.domain.workflow.constant.event_type import WorkflowEventType


class SummaryStrategy(ABC):
    """摘要策略基类"""
    
    @abstractmethod
    def should_generate(self, context: Dict[str, Any]) -> bool:
        """判断是否需要生成摘要"""
        pass


class TokenThresholdStrategy(SummaryStrategy):
    """基于Token阈值的摘要策略"""
    def __init__(self, token_threshold: int = 4000):
        self.token_threshold = token_threshold
    
    def should_generate(self, context: Dict[str, Any]) -> bool:
        token_count = context.get("token_count", 0)
        return token_count > self.token_threshold


class TurnCountStrategy(SummaryStrategy):
    """基于对话轮次的摘要策略"""
    def __init__(self, turn_threshold: int = 10):
        self.turn_threshold = turn_threshold
    
    def should_generate(self, context: Dict[str, Any]) -> bool:
        turn_count = context.get("turn_count", 0)
        return turn_count >= self.turn_threshold


class TaskCompletionStrategy(SummaryStrategy):
    """基于任务完成的摘要策略"""
    def should_generate(self, context: Dict[str, Any]) -> bool:
        task_completed = context.get("task_completed", False)
        return task_completed


class ImportanceBasedStrategy(SummaryStrategy):
    """基于重要性的摘要策略"""
    def should_generate(self, context: Dict[str, Any]) -> bool:
        importance_score = context.get("importance_score", 0)
        return importance_score > 0.7


class SummarizeHandler:
    """摘要生成处理器"""
    
    def __init__(self, summary_repository: SummaryRepository):
        self.summary_repository = summary_repository
        self._strategies = [
            TokenThresholdStrategy(),
            TurnCountStrategy(),
            TaskCompletionStrategy(),
            ImportanceBasedStrategy()
        ]
    
    def check_summary_needed(self, context: Dict[str, Any]) -> bool:
        """检查是否需要生成摘要"""
        for strategy in self._strategies:
            if strategy.should_generate(context):
                return True
        return False
    
    def generate_summary(self, context: Dict[str, Any], strategy: Optional[SummaryStrategy] = None) -> str:
        """生成摘要"""
        # 这里应该使用LLM生成摘要
        # 暂时模拟摘要生成
        messages = context.get("messages", [])
        if not messages:
            return "No content to summarize"
        
        # 提取关键信息
        key_points = []
        for msg in messages[-5:]:  # 只处理最近5条消息
            if msg.get("role") == "user":
                key_points.append(f"User: {msg.get('content', '')[:100]}...")
            elif msg.get("role") == "assistant":
                key_points.append(f"Assistant: {msg.get('content', '')[:100]}...")
        
        summary = "\n".join(key_points)
        return f"Summary of recent conversation:\n{summary}"
    
    def save_summary(self, session_id: str, summary_text: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """保存摘要"""
        import uuid
        summary_id = str(uuid.uuid4())
        
        # 计算token数（模拟）
        token_count = len(summary_text.split())
        
        summary_data = {
            "summary_id": summary_id,
            "session_id": session_id,
            "workflow_id": workflow_id,
            "summary_text": summary_text,
            "token_count": token_count
        }
        
        summary = self.summary_repository.save_summary(summary_data)
        
        # 发布摘要生成事件
        if workflow_id:
            event_bus.publish(
                WorkflowEventType.SUMMARY_GENERATED,
                workflow_id,
                {
                    "summary_id": summary.summary_id,
                    "session_id": session_id,
                    "token_count": token_count
                }
            )
        
        return {
            "summary_id": summary.summary_id,
            "summary_text": summary.summary_text,
            "token_count": summary.token_count
        }
    
    def restore_context_from_summary(self, summary: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从摘要恢复上下文"""
        # 从摘要恢复上下文
        return [{
            "role": "system",
            "content": f"Summary of previous conversation:\n{summary.get('summary_text')}"
        }]
    
    def handle(self, context: Dict[str, Any], session_id: str, workflow_id: Optional[str] = None) -> Dict[str, Any]:
        """处理摘要生成"""
        if not self.check_summary_needed(context):
            return {"summary_generated": False}
        
        # 生成摘要
        summary_text = self.generate_summary(context)
        
        # 保存摘要
        summary_result = self.save_summary(session_id, summary_text, workflow_id)
        
        # 压缩上下文
        compressed_context = self.restore_context_from_summary(summary_result)
        
        return {
            "summary_generated": True,
            "summary": summary_result,
            "compressed_context": compressed_context
        }
