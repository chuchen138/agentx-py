from abc import ABC, abstractmethod
from typing import Dict, Optional, Type
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class StateProcessor(ABC):
    @abstractmethod
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理工具状态
        返回下一个状态，如果返回 None 表示状态不变
        """
        pass


class ToolStateMachine:
    def __init__(self):
        self.processors: Dict[str, StateProcessor] = {}
        self.transition_rules = {
            ToolStatus.WAITING_REVIEW.value: [ToolStatus.FETCHING_TOOLS.value],
            ToolStatus.FETCHING_TOOLS.value: [ToolStatus.GITHUB_URL_VALIDATION.value, ToolStatus.DEPLOYING.value, ToolStatus.REJECTED.value],
            ToolStatus.GITHUB_URL_VALIDATION.value: [ToolStatus.DEPLOYING.value, ToolStatus.REJECTED.value],
            ToolStatus.DEPLOYING.value: [ToolStatus.PUBLISHING.value, ToolStatus.REJECTED.value],
            ToolStatus.PUBLISHING.value: [ToolStatus.PUBLISHED.value, ToolStatus.REJECTED.value],
            ToolStatus.PUBLISHED.value: [],
            ToolStatus.REJECTED.value: []
        }

    def register_processor(self, status: str, processor: StateProcessor):
        self.processors[status] = processor

    def can_transition(self, from_status: str, to_status: str) -> bool:
        """
        检查状态是否可以转换
        """
        return to_status in self.transition_rules.get(from_status, [])

    async def transition_to(self, tool: ToolEntity, new_status: str) -> bool:
        """
        执行状态转换
        """
        if not self.can_transition(tool.status, new_status):
            return False

        tool.status = new_status
        return True

    async def process(self, tool: ToolEntity) -> bool:
        """
        处理工具状态
        """
        processor = self.processors.get(tool.status)
        if not processor:
            return False

        try:
            next_status = await processor.process(tool)
            if next_status:
                return await self.transition_to(tool, next_status.value)
            return True
        except Exception as e:
            # 处理失败，转换到 REJECTED 状态
            tool.status = ToolStatus.REJECTED.value
            tool.reject_reason = str(e)
            tool.failed_step_status = tool.status
            return False