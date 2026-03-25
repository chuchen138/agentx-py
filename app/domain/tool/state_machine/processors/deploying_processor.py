from typing import Optional
import asyncio
from app.domain.tool.state_machine.state_machine import StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class DeployingProcessor(StateProcessor):
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理部署状态，模拟 Docker 容器部署
        """
        try:
            # 检查安装命令是否存在
            if not tool.install_command:
                tool.reject_reason = "安装命令不能为空"
                tool.failed_step_status = ToolStatus.DEPLOYING.value
                return ToolStatus.REJECTED

            # 模拟部署过程
            await self._simulate_deployment(tool)

            # 部署成功，转移到发布状态
            return ToolStatus.PUBLISHING
        except Exception as e:
            tool.reject_reason = f"部署失败: {str(e)}"
            tool.failed_step_status = ToolStatus.DEPLOYING.value
            return ToolStatus.REJECTED

    async def _simulate_deployment(self, tool: ToolEntity) -> None:
        """
        模拟部署过程
        """
        # 模拟部署耗时
        await asyncio.sleep(5)  # 模拟 5 秒部署时间

        # 验证安装命令
        install_command = tool.install_command
        if isinstance(install_command, dict):
            command = install_command.get("command")
            if not command:
                raise Exception("安装命令为空")

        # 模拟部署成功
        # 实际项目中这里会调用 Docker SDK 或容器管理服务
        # 例如：
        # 1. 构建 Docker 镜像
        # 2. 创建并启动容器
        # 3. 配置网络和环境变量
        # 4. 验证容器运行状态
        print(f"部署工具: {tool.name}")
        print(f"安装命令: {tool.install_command}")