from typing import Optional
import asyncio
from app.domain.tool.state_machine.state_machine import StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class PublishingProcessor(StateProcessor):
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理发布状态，完成工具发布流程
        """
        try:
            # 模拟发布过程
            await self._simulate_publishing(tool)

            # 发布成功，转移到已发布状态
            return ToolStatus.PUBLISHED
        except Exception as e:
            tool.reject_reason = f"发布失败: {str(e)}"
            tool.failed_step_status = ToolStatus.PUBLISHING.value
            return ToolStatus.REJECTED

    async def _simulate_publishing(self, tool: ToolEntity) -> None:
        """
        模拟发布过程
        """
        # 模拟发布耗时
        await asyncio.sleep(3)  # 模拟 3 秒发布时间

        # 验证工具信息完整性
        if not tool.name or not tool.description:
            raise Exception("工具信息不完整")

        # 模拟发布成功
        # 实际项目中这里会：
        # 1. 更新工具状态为已发布
        # 2. 通知市场服务
        # 3. 更新工具统计数据
        # 4. 为工具创建者自动安装工具
        print(f"发布工具: {tool.name}")
        print(f"工具状态: {ToolStatus.PUBLISHED.value}")