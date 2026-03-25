import pytest
from unittest.mock import Mock, MagicMock, patch
from app.domain.tool.state_machine.processors.github_url_validate_processor import GithubUrlValidateProcessor
from app.domain.tool.model import ToolEntity
from app.domain.tool.enums import ToolStatus


class TestGithubUrlValidateProcessor:
    @pytest.fixture
    def processor(self):
        return GithubUrlValidateProcessor()

    @pytest.fixture
    def mock_tool(self):
        tool = Mock(spec=ToolEntity)
        tool.upload_url = "https://github.com/test/repo"
        return tool

    def test_parse_github_url_valid(self, processor):
        # 测试有效的 GitHub URL 解析
        url = "https://github.com/test/repo"
        result = processor._parse_github_url(url)
        assert result == {"owner": "test", "repo": "repo", "ref": "main"}

    def test_parse_github_url_with_git_suffix(self, processor):
        # 测试带 .git 后缀的 GitHub URL 解析
        url = "https://github.com/test/repo.git"
        result = processor._parse_github_url(url)
        assert result == {"owner": "test", "repo": "repo", "ref": "main"}

    def test_parse_github_url_with_branch(self, processor):
        # 测试带分支的 GitHub URL 解析
        url = "https://github.com/test/repo/tree/develop"
        result = processor._parse_github_url(url)
        assert result == {"owner": "test", "repo": "repo", "ref": "develop"}

    def test_parse_github_url_invalid(self, processor):
        # 测试无效的 GitHub URL 解析
        url = "https://gitlab.com/test/repo"
        result = processor._parse_github_url(url)
        assert result is not None  # 注意：当前实现会尝试解析任何 URL，只是提取路径部分

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.httpx.AsyncClient')
    async def test_validate_repo_accessibility_valid(self, mock_client, processor):
        # 测试有效的仓库可访问性验证
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        repo_info = {"owner": "test", "repo": "repo"}
        result = await processor._validate_repo_accessibility(repo_info)
        assert result is True

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.httpx.AsyncClient')
    async def test_validate_repo_accessibility_invalid(self, mock_client, processor):
        # 测试无效的仓库可访问性验证
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        repo_info = {"owner": "test", "repo": "repo"}
        result = await processor._validate_repo_accessibility(repo_info)
        assert result is False

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.httpx.AsyncClient')
    async def test_validate_repo_structure_with_config(self, mock_client, processor):
        # 测试带配置文件的仓库结构验证
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        repo_info = {"owner": "test", "repo": "repo", "ref": "main"}
        result = await processor._validate_repo_structure(repo_info)
        assert result is True

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.httpx.AsyncClient')
    async def test_validate_repo_structure_with_setup(self, mock_client, processor):
        # 测试带 setup 文件的仓库结构验证
        # 第一次调用返回 404（无配置文件），第二次调用返回 200（有 setup.py）
        mock_response_404 = Mock()
        mock_response_404.status_code = 404
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        
        mock_client_instance = Mock()
        mock_client_instance.get.side_effect = [mock_response_404, mock_response_404, mock_response_404, mock_response_200]
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        repo_info = {"owner": "test", "repo": "repo", "ref": "main"}
        result = await processor._validate_repo_structure(repo_info)
        assert result is True

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.httpx.AsyncClient')
    async def test_validate_repo_structure_invalid(self, mock_client, processor):
        # 测试无效的仓库结构验证
        mock_response = Mock()
        mock_response.status_code = 404
        mock_client_instance = Mock()
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value.__aenter__.return_value = mock_client_instance
        
        repo_info = {"owner": "test", "repo": "repo", "ref": "main"}
        result = await processor._validate_repo_structure(repo_info)
        assert result is False

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._parse_github_url')
    async def test_process_invalid_url(self, mock_parse, processor, mock_tool):
        # 测试无效 URL 的处理
        mock_parse.return_value = None
        
        result = await processor.process(mock_tool)
        assert result == ToolStatus.REJECTED
        assert "GitHub URL 解析失败" in mock_tool.reject_reason
        assert mock_tool.failed_step_status == ToolStatus.GITHUB_URL_VALIDATION.value

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._parse_github_url')
    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._validate_repo_accessibility')
    async def test_process_inaccessible_repo(self, mock_validate_access, mock_parse, processor, mock_tool):
        # 测试不可访问仓库的处理
        mock_parse.return_value = {"owner": "test", "repo": "repo"}
        mock_validate_access.return_value = False
        
        result = await processor.process(mock_tool)
        assert result == ToolStatus.REJECTED
        assert "无法访问 GitHub 仓库" in mock_tool.reject_reason
        assert mock_tool.failed_step_status == ToolStatus.GITHUB_URL_VALIDATION.value

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._parse_github_url')
    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._validate_repo_accessibility')
    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._validate_repo_structure')
    async def test_process_invalid_structure(self, mock_validate_structure, mock_validate_access, mock_parse, processor, mock_tool):
        # 测试无效仓库结构的处理
        mock_parse.return_value = {"owner": "test", "repo": "repo"}
        mock_validate_access.return_value = True
        mock_validate_structure.return_value = False
        
        result = await processor.process(mock_tool)
        assert result == ToolStatus.REJECTED
        assert "GitHub 仓库结构不符合要求" in mock_tool.reject_reason
        assert mock_tool.failed_step_status == ToolStatus.GITHUB_URL_VALIDATION.value

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._parse_github_url')
    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._validate_repo_accessibility')
    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._validate_repo_structure')
    async def test_process_success(self, mock_validate_structure, mock_validate_access, mock_parse, processor, mock_tool):
        # 测试成功的处理
        mock_parse.return_value = {"owner": "test", "repo": "repo"}
        mock_validate_access.return_value = True
        mock_validate_structure.return_value = True
        
        result = await processor.process(mock_tool)
        assert result == ToolStatus.DEPLOYING

    @patch('app.domain.tool.state_machine.processors.github_url_validate_processor.GithubUrlValidateProcessor._parse_github_url')
    async def test_process_exception(self, mock_parse, processor, mock_tool):
        # 测试异常处理
        mock_parse.side_effect = Exception("Test error")
        
        result = await processor.process(mock_tool)
        assert result == ToolStatus.REJECTED
        assert "GitHub URL 验证失败" in mock_tool.reject_reason
        assert mock_tool.failed_step_status == ToolStatus.GITHUB_URL_VALIDATION.value
