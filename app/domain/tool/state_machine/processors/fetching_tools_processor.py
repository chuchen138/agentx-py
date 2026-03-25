import asyncio
from typing import Optional
import httpx
from app.domain.tool.state_machine.state_machine import StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus, UploadType


class FetchingToolsProcessor(StateProcessor):
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理获取工具状态，解析 GitHub URL 或 Zip 包
        """
        try:
            if tool.upload_type == UploadType.GITHUB.value:
                # 验证 GitHub URL 格式
                if not tool.upload_url.startswith("https://github.com/"):
                    tool.reject_reason = "GitHub URL 格式无效"
                    tool.failed_step_status = ToolStatus.FETCHING_TOOLS.value
                    return ToolStatus.REJECTED

                # 解析 GitHub 仓库信息
                repo_info = self._parse_github_url(tool.upload_url)
                if not repo_info:
                    tool.reject_reason = "GitHub URL 解析失败"
                    tool.failed_step_status = ToolStatus.FETCHING_TOOLS.value
                    return ToolStatus.REJECTED

                # 验证仓库是否存在
                if not await self._validate_github_repo(repo_info):
                    tool.reject_reason = "GitHub 仓库不存在或无法访问"
                    tool.failed_step_status = ToolStatus.FETCHING_TOOLS.value
                    return ToolStatus.REJECTED

                # 转移到 GitHub URL 验证状态
                return ToolStatus.GITHUB_URL_VALIDATION
            elif tool.upload_type == UploadType.ZIP.value:
                # TODO: 实现 Zip 包解析逻辑
                # 暂时直接转移到部署状态
                return ToolStatus.DEPLOYING
            else:
                tool.reject_reason = "不支持的上传类型"
                tool.failed_step_status = ToolStatus.FETCHING_TOOLS.value
                return ToolStatus.REJECTED
        except Exception as e:
            tool.reject_reason = f"获取工具失败: {str(e)}"
            tool.failed_step_status = ToolStatus.FETCHING_TOOLS.value
            return ToolStatus.REJECTED

    def _parse_github_url(self, url: str) -> Optional[dict]:
        """
        解析 GitHub URL，提取所有者和仓库名
        """
        try:
            # 处理不同格式的 GitHub URL
            if url.endswith('.git'):
                url = url[:-4]
            parts = url.split('/')
            if len(parts) < 5:
                return None
            owner = parts[3]
            repo = parts[4]
            return {"owner": owner, "repo": repo}
        except:
            return None

    async def _validate_github_repo(self, repo_info: dict) -> bool:
        """
        验证 GitHub 仓库是否存在
        """
        owner = repo_info.get("owner")
        repo = repo_info.get("repo")
        if not owner or not repo:
            return False

        url = f"https://api.github.com/repos/{owner}/{repo}"
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                return response.status_code == 200
        except:
            return False