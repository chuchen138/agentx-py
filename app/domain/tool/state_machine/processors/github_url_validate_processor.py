from typing import Optional
import httpx
from app.domain.tool.state_machine.state_machine import StateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class GithubUrlValidateProcessor(StateProcessor):
    async def process(self, tool: ToolEntity) -> Optional[ToolStatus]:
        """
        处理 GitHub URL 验证状态，验证仓库的有效性
        """
        try:
            # 解析 GitHub URL
            repo_info = self._parse_github_url(tool.upload_url)
            if not repo_info:
                tool.reject_reason = "GitHub URL 解析失败"
                tool.failed_step_status = ToolStatus.GITHUB_URL_VALIDATION.value
                return ToolStatus.REJECTED

            # 验证仓库是否存在且可读
            if not await self._validate_repo_accessibility(repo_info):
                tool.reject_reason = "无法访问 GitHub 仓库"
                tool.failed_step_status = ToolStatus.GITHUB_URL_VALIDATION.value
                return ToolStatus.REJECTED

            # 验证仓库是否包含必要的文件（例如 MCP 配置文件）
            if not await self._validate_repo_structure(repo_info):
                tool.reject_reason = "GitHub 仓库结构不符合要求"
                tool.failed_step_status = ToolStatus.GITHUB_URL_VALIDATION.value
                return ToolStatus.REJECTED

            # 验证通过，转移到部署状态
            return ToolStatus.DEPLOYING
        except Exception as e:
            tool.reject_reason = f"GitHub URL 验证失败: {str(e)}"
            tool.failed_step_status = ToolStatus.GITHUB_URL_VALIDATION.value
            return ToolStatus.REJECTED

    def _parse_github_url(self, url: str) -> Optional[dict]:
        """
        解析 GitHub URL，提取所有者、仓库名和引用
        """
        try:
            if url.endswith('.git'):
                url = url[:-4]
            parts = url.split('/')
            if len(parts) < 5:
                return None
            owner = parts[3]
            repo = parts[4]
            ref = "main"  # 默认分支
            # 检查是否有指定分支或标签
            if len(parts) > 6 and parts[5] == "tree":
                ref = parts[6]
            return {"owner": owner, "repo": repo, "ref": ref}
        except:
            return None

    async def _validate_repo_accessibility(self, repo_info: dict) -> bool:
        """
        验证仓库是否可访问
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

    async def _validate_repo_structure(self, repo_info: dict) -> bool:
        """
        验证仓库结构是否符合要求
        """
        owner = repo_info.get("owner")
        repo = repo_info.get("repo")
        ref = repo_info.get("ref", "main")

        # 检查是否存在 mcp_config.json 或类似配置文件
        config_files = ["mcp_config.json", "tool_config.json", "config.json"]
        for config_file in config_files:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{config_file}?ref={ref}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return True
            except:
                continue

        # 检查是否存在 setup.py 或 requirements.txt
        setup_files = ["setup.py", "requirements.txt"]
        for setup_file in setup_files:
            url = f"https://api.github.com/repos/{owner}/{repo}/contents/{setup_file}?ref={ref}"
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url)
                    if response.status_code == 200:
                        return True
            except:
                continue

        return False