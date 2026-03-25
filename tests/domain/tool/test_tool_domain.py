import pytest
from unittest.mock import Mock, MagicMock
from app.domain.tool.service import ToolDomainService, ToolVersionDomainService, UserToolDomainService
from app.domain.tool.repository import SQLAlchemyToolRepository, SQLAlchemyToolVersionRepository, SQLAlchemyUserToolRepository
from app.domain.tool.model import ToolEntity, ToolVersionEntity, UserToolEntity
from app.domain.tool.schemas.schemas import CreateToolRequest, UpdateToolRequest, ToolVersionRequest
from app.domain.tool.enums import ToolStatus, ToolVersionStatus


class TestToolDomainService:
    @pytest.fixture
    def mock_tool_repository(self):
        return Mock(spec=SQLAlchemyToolRepository)

    @pytest.fixture
    def tool_domain_service(self, mock_tool_repository):
        return ToolDomainService(mock_tool_repository)

    async def test_create_tool(self, tool_domain_service, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        request = CreateToolRequest(
            name="Test Tool",
            description="Test description",
            tool_type="MCP",
            upload_type="GITHUB",
            upload_url="https://github.com/test/repo"
        )
        mock_tool = Mock(spec=ToolEntity)
        mock_tool_repository.create.return_value = mock_tool

        # 执行测试
        result = await tool_domain_service.create_tool(user_id, request)

        # 验证结果
        assert result.tool == mock_tool
        assert result.need_state_transition is True
        assert result.error_message is None
        mock_tool_repository.create.assert_called_once()

    async def test_create_tool_invalid_github_url(self, tool_domain_service):
        # 准备测试数据
        user_id = 1
        request = CreateToolRequest(
            name="Test Tool",
            description="Test description",
            tool_type="MCP",
            upload_type="GITHUB",
            upload_url="https://gitlab.com/test/repo"
        )

        # 执行测试
        result = await tool_domain_service.create_tool(user_id, request)

        # 验证结果
        assert result.tool is None
        assert result.need_state_transition is False
        assert "GitHub URL 必须以 https://github.com/ 开头" in result.error_message

    async def test_update_tool(self, tool_domain_service, mock_tool_repository):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        request = UpdateToolRequest(
            name="Updated Tool",
            description="Updated description"
        )
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = user_id
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_tool_repository.update.return_value = mock_tool

        # 执行测试
        result = await tool_domain_service.update_tool(tool_id, user_id, request)

        # 验证结果
        assert result == mock_tool
        mock_tool_repository.get_by_id.assert_called_once_with(tool_id)
        mock_tool_repository.update.assert_called_once()

    async def test_update_tool_no_permission(self, tool_domain_service, mock_tool_repository):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        request = UpdateToolRequest(name="Updated Tool")
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = 2  # 不同用户
        mock_tool_repository.get_by_id.return_value = mock_tool

        # 执行测试
        result = await tool_domain_service.update_tool(tool_id, user_id, request)

        # 验证结果
        assert result is None

    async def test_delete_tool(self, tool_domain_service, mock_tool_repository):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = user_id
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_tool_repository.delete.return_value = True

        # 执行测试
        result = await tool_domain_service.delete_tool(tool_id, user_id)

        # 验证结果
        assert result is True
        mock_tool_repository.get_by_id.assert_called_once_with(tool_id)
        mock_tool_repository.delete.assert_called_once_with(tool_id)

    async def test_delete_tool_no_permission(self, tool_domain_service, mock_tool_repository):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = 2  # 不同用户
        mock_tool_repository.get_by_id.return_value = mock_tool

        # 执行测试
        result = await tool_domain_service.delete_tool(tool_id, user_id)

        # 验证结果
        assert result is False


class TestToolVersionDomainService:
    @pytest.fixture
    def mock_tool_version_repository(self):
        return Mock(spec=SQLAlchemyToolVersionRepository)

    @pytest.fixture
    def mock_tool_repository(self):
        return Mock(spec=SQLAlchemyToolRepository)

    @pytest.fixture
    def tool_version_domain_service(self, mock_tool_version_repository, mock_tool_repository):
        return ToolVersionDomainService(mock_tool_version_repository, mock_tool_repository)

    async def test_create_version(self, tool_version_domain_service, mock_tool_version_repository, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        request = ToolVersionRequest(
            tool_id=1,
            version_number="1.0.0",
            config={"key": "value"}
        )
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = user_id
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_version = Mock(spec=ToolVersionEntity)
        mock_tool_version_repository.create.return_value = mock_version

        # 执行测试
        result = await tool_version_domain_service.create_version(user_id, request)

        # 验证结果
        assert result == mock_version
        mock_tool_repository.get_by_id.assert_called_once_with(request.tool_id)
        mock_tool_version_repository.create.assert_called_once()

    async def test_create_version_no_permission(self, tool_version_domain_service, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        request = ToolVersionRequest(tool_id=1, version_number="1.0.0")
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = 2  # 不同用户
        mock_tool_repository.get_by_id.return_value = mock_tool

        # 执行测试
        result = await tool_version_domain_service.create_version(user_id, request)

        # 验证结果
        assert result is None

    async def test_publish_version(self, tool_version_domain_service, mock_tool_version_repository, mock_tool_repository):
        # 准备测试数据
        version_id = 1
        user_id = 1
        mock_version = Mock(spec=ToolVersionEntity)
        mock_version.tool_id = 1
        mock_tool_version_repository.get_by_id.return_value = mock_version
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = user_id
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_tool_version_repository.update.return_value = mock_version

        # 执行测试
        result = await tool_version_domain_service.publish_version(version_id, user_id)

        # 验证结果
        assert result == mock_version
        assert mock_version.status == ToolVersionStatus.PUBLISHED.value
        mock_tool_version_repository.get_by_id.assert_called_once_with(version_id)
        mock_tool_repository.get_by_id.assert_called_once_with(mock_version.tool_id)
        mock_tool_version_repository.update.assert_called_once()


class TestUserToolDomainService:
    @pytest.fixture
    def mock_user_tool_repository(self):
        return Mock(spec=SQLAlchemyUserToolRepository)

    @pytest.fixture
    def mock_tool_repository(self):
        return Mock(spec=SQLAlchemyToolRepository)

    @pytest.fixture
    def user_tool_domain_service(self, mock_user_tool_repository, mock_tool_repository):
        return UserToolDomainService(mock_user_tool_repository, mock_tool_repository)

    async def test_install_tool(self, user_tool_domain_service, mock_user_tool_repository, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        tool_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.status = ToolStatus.PUBLISHED.value
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_user_tool_repository.is_tool_installed.return_value = False
        mock_user_tool = Mock(spec=UserToolEntity)
        mock_user_tool_repository.create.return_value = mock_user_tool

        # 执行测试
        result = await user_tool_domain_service.install_tool(user_id, tool_id)

        # 验证结果
        assert result == mock_user_tool
        mock_tool_repository.get_by_id.assert_called_once_with(tool_id)
        mock_user_tool_repository.is_tool_installed.assert_called_once_with(user_id, tool_id)
        mock_user_tool_repository.create.assert_called_once()

    async def test_install_tool_already_installed(self, user_tool_domain_service, mock_user_tool_repository, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        tool_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.status = ToolStatus.PUBLISHED.value
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_user_tool_repository.is_tool_installed.return_value = True

        # 执行测试
        result = await user_tool_domain_service.install_tool(user_id, tool_id)

        # 验证结果
        assert result is None

    async def test_uninstall_tool(self, user_tool_domain_service, mock_user_tool_repository, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        tool_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = 2  # 不是用户自己创建的工具
        mock_tool_repository.get_by_id.return_value = mock_tool
        mock_user_tool_repository.delete.return_value = True

        # 执行测试
        result = await user_tool_domain_service.uninstall_tool(user_id, tool_id)

        # 验证结果
        assert result is True
        mock_tool_repository.get_by_id.assert_called_once_with(tool_id)
        mock_user_tool_repository.delete.assert_called_once_with(user_id, tool_id)

    async def test_uninstall_tool_own_tool(self, user_tool_domain_service, mock_tool_repository):
        # 准备测试数据
        user_id = 1
        tool_id = 1
        mock_tool = Mock(spec=ToolEntity)
        mock_tool.user_id = user_id  # 用户自己创建的工具
        mock_tool_repository.get_by_id.return_value = mock_tool

        # 执行测试
        result = await user_tool_domain_service.uninstall_tool(user_id, tool_id)

        # 验证结果
        assert result is False