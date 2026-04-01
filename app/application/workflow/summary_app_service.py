from typing import List, Optional, Dict, Any

from app.domain.workflow.model.schemas import SummaryDTO
from app.domain.workflow.repository import SummaryRepository
from app.domain.workflow.handlers.summarize import SummarizeHandler


class SummaryAppService:
    """摘要应用服务"""
    
    def __init__(self, summary_repository: SummaryRepository, summarize_handler: SummarizeHandler):
        self.summary_repository = summary_repository
        self.summarize_handler = summarize_handler
    
    def get_summary(self, session_id: str) -> Optional[SummaryDTO]:
        """获取会话摘要"""
        summary = self.summary_repository.get_by_session_id(session_id)
        if summary:
            return SummaryDTO.model_validate(summary)
        return None
    
    def get_summary_by_workflow(self, workflow_id: str) -> Optional[SummaryDTO]:
        """获取工作流摘要"""
        summary = self.summary_repository.get_by_workflow_id(workflow_id)
        if summary:
            return SummaryDTO.model_validate(summary)
        return None
    
    def regenerate_summary(self, session_id: str, strategy: str = "token") -> SummaryDTO:
        """重新生成摘要"""
        # 这里应该实现根据策略重新生成摘要的逻辑
        # 暂时创建一个新的摘要
        import uuid
        summary_id = str(uuid.uuid4())
        summary_data = {
            "summary_id": summary_id,
            "session_id": session_id,
            "summary_text": f"Regenerated summary for session {session_id}",
            "token_count": 100
        }
        summary = self.summary_repository.save_summary(summary_data)
        return SummaryDTO.model_validate(summary)
    
    def delete_summary(self, summary_id: str):
        """删除摘要"""
        # 这里需要实现删除摘要的逻辑
        # 暂时不实现
        pass
    
    def list_summaries(self, user_id: str, page: int, size: int) -> List[SummaryDTO]:
        """获取用户摘要列表"""
        # 这里需要实现查询用户摘要的逻辑
        # 暂时返回空列表
        return []
