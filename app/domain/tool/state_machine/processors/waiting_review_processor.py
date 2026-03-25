from typing import Optional
from app.domain.tool.state_machine.state_machine import StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class WaitingReviewProcessor(StateProcessor):
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理等待审核状态，自动触发进入审核流程
        """
        # 直接转移到获取工具状态
        return ToolStatus.FETCHING_TOOLS