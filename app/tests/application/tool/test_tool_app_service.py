import pytest
from unittest.mock import Mock, MagicMock
from app.application.tool.tool_app_service import ToolAppService, ToolVersionService, ToolStateStateMachineAppService
from app.domain.tool.service import ToolDomainService, ToolVersionDomainService, UserToolDomainService
from app.domain.tool.schemas.schemas import (
    CreateToolRequest, UpdateToolRequest, ToolResponse, ToolVersionRequest, ToolVersionResponse,
    InstallToolRequest, UninstallToolRequest, ToolMarketResponse, ToolReviewRequest
)
from app.domain.tool.model import ToolEntity, ToolVersionEntity, UserToolEntity
from app.domain.tool.enums import ToolStatus, ToolVersionStatus


class TestToolAppService:
    @pytest.fixture
    def mock_tool_domain_service(self):
        return Mock(spec=ToolDomainService)

    @pytest.fixture
    def mock_tool_version_domain_service(self):
        return Mock(spec=ToolVersionDomainService)

    @pytest.fixture
    def mock_user_tool_domain_service(self):
        return Mock(spec=UserToolDomainService)

    @pytest.fixture
    def mock_tool_state_machine_app_service(self):
        return Mock(spec=ToolStateStateMachineAppService)

    @pytest.fixture
    def tool_app_service(self, mock_tool_domain_service, mock_tool_version_domain_service, 
                         mock_user_tool_domain_service, mock_tool_state_machine_app_service):
        return ToolAppService(
            mock_tool_domain_service,
            mock_tool_version_domain_service,
            mock_user_tool_domain_service,
            mock_tool_state_machine_app_service
        )

    @pytest.fixture
    def mock_tool(self):
        tool = Mock(spec=ToolEntity)
        tool.id = 1
        tool.name = "Test Tool"
        tool.description = "Test description"
        tool.user_id = 1
        tool.status = ToolStatus.WAITING_REVIEW.value
        return tool

    async def test_upload_tool_success(self, tool_app_service, mock_tool_domain_service, 
                                      mock_tool_state_machine_app_service, mock_tool):
        # 准备测试数据
        user_id = 1
        request = CreateToolRequest(
            name="Test Tool",
            description="Test description",
            tool_type="MCP",
            upload_type="GITHUB",
            upload_url="https://github.com/test/repo"
        )
        
        # 模拟返回结果
        mock_result = Mock()
        mock_result.error_message = None
        mock_result.need_state_transition = True
        mock_result.tool = mock_tool
        mock_tool_domain_service.create_tool.return_value = mock_result
        
        # 执行测试
        result = await tool_app_service.upload_tool(user_id, request)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_tool.id
        mock_tool_domain_service.create_tool.assert_called_once_with(user_id, request)
        mock_tool_state_machine_app_service.submit_tool_for_processing.assert_called_once_with(mock_tool)

    async def test_upload_tool_failure(self, tool_app_service, mock_tool_domain_service):
        # 准备测试数据
        user_id = 1
        request = CreateToolRequest(
            name="Test Tool",
            description="Test description",
            tool_type="MCP",
            upload_type="GITHUB",
            upload_url="https://github.com/test/repo"
        )
        
        # 模拟返回结果
        mock_result = Mock()
        mock_result.error_message = "Error"
        mock_result.need_state_transition = False
        mock_result.tool = None
        mock_tool_domain_service.create_tool.return_value = mock_result
        
        # 执行测试
        result = await tool_app_service.upload_tool(user_id, request)
        
        # 验证结果
        assert result is None
        mock_tool_domain_service.create_tool.assert_called_once_with(user_id, request)

    async def test_get_tool_detail_own_tool(self, tool_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        mock_tool.user_id = user_id
        mock_tool_domain_service.get_tool_by_id.return_value = mock_tool
        
        # 执行测试
        result = await tool_app_service.get_tool_detail(tool_id, user_id)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_tool.id
        mock_tool_domain_service.get_tool_by_id.assert_called_once_with(tool_id)

    async def test_get_tool_detail_published_tool(self, tool_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        user_id = 2  # 不同用户
        mock_tool.user_id = 1
        mock_tool.status = ToolStatus.PUBLISHED.value
        mock_tool_domain_service.get_tool_by_id.return_value = mock_tool
        
        # 执行测试
        result = await tool_app_service.get_tool_detail(tool_id, user_id)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_tool.id
        mock_tool_domain_service.get_tool_by_id.assert_called_once_with(tool_id)

    async def test_get_tool_detail_no_permission(self, tool_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        user_id = 2  # 不同用户
        mock_tool.user_id = 1
        mock_tool.status = ToolStatus.WAITING_REVIEW.value  # 未发布
        mock_tool_domain_service.get_tool_by_id.return_value = mock_tool
        
        # 执行测试
        result = await tool_app_service.get_tool_detail(tool_id, user_id)
        
        # 验证结果
        assert result is None
        mock_tool_domain_service.get_tool_by_id.assert_called_once_with(tool_id)

    async def test_get_user_tools(self, tool_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        user_id = 1
        mock_tool_domain_service.get_user_tools.return_value = [mock_tool]
        
        # 执行测试
        result = await tool_app_service.get_user_tools(user_id, 0, 20)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].id == mock_tool.id
        mock_tool_domain_service.get_user_tools.assert_called_once_with(user_id, 0, 20)

    async def test_update_tool(self, tool_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        request = UpdateToolRequest(name="Updated Tool")
        mock_tool_domain_service.update_tool.return_value = mock_tool
        
        # 执行测试
        result = await tool_app_service.update_tool(tool_id, user_id, request)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_tool.id
        mock_tool_domain_service.update_tool.assert_called_once_with(tool_id, user_id, request)

    async def test_delete_tool(self, tool_app_service, mock_tool_domain_service):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        mock_tool_domain_service.delete_tool.return_value = True
        
        # 执行测试
        result = await tool_app_service.delete_tool(tool_id, user_id)
        
        # 验证结果
        assert result is True
        mock_tool_domain_service.delete_tool.assert_called_once_with(tool_id, user_id)

    async def test_get_market_tools(self, tool_app_service, mock_tool_domain_service, 
                                   mock_user_tool_domain_service, mock_tool):
        # 准备测试数据
        user_id = 1
        mock_tool.status = ToolStatus.PUBLISHED.value
        mock_tool_domain_service.get_market_tools.return_value = [mock_tool]
        mock_user_tool_domain_service.is_tool_installed.return_value = False
        
        # 执行测试
        result = await tool_app_service.get_market_tools(user_id, 0, 20)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].id == mock_tool.id
        mock_tool_domain_service.get_market_tools.assert_called_once_with(0, 20)
        mock_user_tool_domain_service.is_tool_installed.assert_called_once_with(user_id, mock_tool.id)

    async def test_install_market_tool(self, tool_app_service, mock_user_tool_domain_service):
        # 准备测试数据
        user_id = 1
        request = InstallToolRequest(tool_id=1)
        mock_user = Mock(spec=UserToolEntity)
        mock_user_tool_domain_service.install_tool.return_value = mock_user
        
        # 执行测试
        result = await tool_app_service.install_market_tool(user_id, request)
        
        # 验证结果
        assert result is True
        mock_user_tool_domain_service.install_tool.assert_called_once_with(user_id, request.tool_id)

    async def test_uninstall_tool(self, tool_app_service, mock_user_tool_domain_service):
        # 准备测试数据
        user_id = 1
        request = UninstallToolRequest(tool_id=1)
        mock_user_tool_domain_service.uninstall_tool.return_value = True
        
        # 执行测试
        result = await tool_app_service.uninstall_tool(user_id, request)
        
        # 验证结果
        assert result is True
        mock_user_tool_domain_service.uninstall_tool.assert_called_once_with(user_id, request.tool_id)


class TestToolVersionService:
    @pytest.fixture
    def mock_tool_version_domain_service(self):
        return Mock(spec=ToolVersionDomainService)

    @pytest.fixture
    def tool_version_service(self, mock_tool_version_domain_service):
        return ToolVersionService(mock_tool_version_domain_service)

    @pytest.fixture
    def mock_version(self):
        version = Mock(spec=ToolVersionEntity)
        version.id = 1
        version.tool_id = 1
        version.version_number = "1.0.0"
        version.status = ToolVersionStatus.DRAFT.value
        return version

    async def test_create_tool_version(self, tool_version_service, mock_tool_version_domain_service, mock_version):
        # 准备测试数据
        user_id = 1
        request = ToolVersionRequest(tool_id=1, version_number="1.0.0")
        mock_tool_version_domain_service.create_version.return_value = mock_version
        
        # 执行测试
        result = await tool_version_service.create_tool_version(user_id, request)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_version.id
        mock_tool_version_domain_service.create_version.assert_called_once_with(user_id, request)

    async def test_get_tool_versions(self, tool_version_service, mock_tool_version_domain_service, mock_version):
        # 准备测试数据
        tool_id = 1
        user_id = 1
        mock_tool_version_domain_service.get_tool_versions.return_value = [mock_version]
        
        # 执行测试
        result = await tool_version_service.get_tool_versions(tool_id, user_id, 0, 20)
        
        # 验证结果
        assert len(result) == 1
        assert result[0].id == mock_version.id
        mock_tool_version_domain_service.get_tool_versions.assert_called_once_with(tool_id, user_id, 0, 20)

    async def test_publish_tool_version(self, tool_version_service, mock_tool_version_domain_service, mock_version):
        # 准备测试数据
        version_id = 1
        user_id = 1
        mock_tool_version_domain_service.publish_version.return_value = mock_version
        
        # 执行测试
        result = await tool_version_service.publish_tool_version(version_id, user_id)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_version.id
        mock_tool_version_domain_service.publish_version.assert_called_once_with(version_id, user_id)

    async def test_rollback_tool_version(self, tool_version_service, mock_tool_version_domain_service, mock_version):
        # 准备测试数据
        version_id = 1
        user_id = 1
        mock_tool_version_domain_service.rollback_version.return_value = mock_version
        
        # 执行测试
        result = await tool_version_service.rollback_tool_version(version_id, user_id)
        
        # 验证结果
        assert result is not None
        assert result.id == mock_version.id
        mock_tool_version_domain_service.rollback_version.assert_called_once_with(version_id, user_id)


class TestToolStateStateMachineAppService:
    @pytest.fixture
    def mock_tool_domain_service(self):
        return Mock(spec=ToolDomainService)

    @pytest.fixture
    def tool_state_machine_app_service(self, mock_tool_domain_service):
        service = ToolStateStateMachineAppService(mock_tool_domain_service)
        # 初始化状态机
        from app.domain.tool.state_machine.state_machine import ToolStateMachine
        service.state_machine = ToolStateMachine()
        return service

    @pytest.fixture
    def mock_tool(self):
        tool = Mock(spec=ToolEntity)
        tool.id = 1
        tool.status = ToolStatus.WAITING_REVIEW.value
        return tool

    async def test_submit_tool_for_processing(self, tool_state_machine_app_service, mock_tool_domain_service, mock_tool):
        # 执行测试
        await tool_state_machine_app_service.submit_tool_for_processing(mock_tool)
        
        # 验证结果
        mock_tool_domain_service.tool_repository.update.assert_called_once_with(mock_tool)

    async def test_review_tool_approve(self, tool_state_machine_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        request = ToolReviewRequest(approve=True, reject_reason="")
        mock_tool_domain_service.get_tool_by_id.return_value = mock_tool
        
        # 执行测试
        result = await tool_state_machine_app_service.review_tool(tool_id, request)
        
        # 验证结果
        assert result is True
        assert mock_tool.status == ToolStatus.PUBLISHED.value
        mock_tool_domain_service.get_tool_by_id.assert_called_once_with(tool_id)
        mock_tool_domain_service.tool_repository.update.assert_called_once_with(mock_tool)

    async def test_review_tool_reject(self, tool_state_machine_app_service, mock_tool_domain_service, mock_tool):
        # 准备测试数据
        tool_id = 1
        request = ToolReviewRequest(approve=False, reject_reason="Reject reason")
        mock_tool_domain_service.get_tool_by_id.return_value = mock_tool
        
        # 执行测试
        result = await tool_state_machine_app_service.review_tool(tool_id, request)
        
        # 验证结果
        assert result is True
        assert mock_tool.status == ToolStatus.REJECTED.value
        assert mock_tool.reject_reason == "Reject reason"
        mock_tool_domain_service.get_tool_by_id.assert_called_once_with(tool_id)
        mock_tool_domain_service.tool_repository.update.assert_called_once_with(mock_tool)

    async def test_get_pending_review_tools(self, tool_state_machine_app_service, mock_tool_domain_service):
        # 准备测试数据
        mock_tool_domain_service.get_pending_review_tools.return_value = []
        
        # 执行测试
        result = await tool_state_machine_app_service.get_pending_review_tools(0, 20)
        
        # 验证结果
        assert result == []
        mock_tool_domain_service.get_pending_review_tools.assert_called_once_with(0, 20)
