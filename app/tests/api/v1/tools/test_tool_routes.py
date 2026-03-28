import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient
from app.api.v1.tools.routes import router
from app.application.tool.tool_app_service import ToolAppService, ToolVersionService
from app.domain.tool.schemas.schemas import (
    CreateToolRequest, UpdateToolRequest, ToolResponse, ToolVersionRequest, ToolVersionResponse,
    InstallToolRequest, UninstallToolRequest, ToolMarketResponse
)
from app.domain.user.model import UserModel


@pytest.fixture
async def mock_tool_app_service():
    return Mock(spec=ToolAppService)


@pytest.fixture
async def mock_tool_version_service():
    return Mock(spec=ToolVersionService)


@pytest.fixture
async def mock_current_user():
    user = Mock(spec=UserModel)
    user.id = 1
    return user


@pytest.fixture
def test_client():
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


async def test_upload_tool(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool = Mock(spec=ToolResponse)
        mock_tool_app_service.upload_tool.return_value = mock_tool
        
        # 发送请求
        response = test_client.post("/api/v1/tools", json={
            "name": "Test Tool",
            "description": "Test description",
            "tool_type": "MCP",
            "upload_type": "GITHUB",
            "upload_url": "https://github.com/test/repo"
        })
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_app_service.upload_tool.assert_called_once_with(1, CreateToolRequest(**response.json()))
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_get_user_tools(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tools = [Mock(spec=ToolResponse)]
        mock_tool_app_service.get_user_tools.return_value = mock_tools
        
        # 发送请求
        response = test_client.get("/api/v1/tools?skip=0&limit=20")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_app_service.get_user_tools.assert_called_once_with(1, 0, 20)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_get_tool_detail(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool = Mock(spec=ToolResponse)
        mock_tool_app_service.get_tool_detail.return_value = mock_tool
        
        # 发送请求
        response = test_client.get("/api/v1/tools/1")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_app_service.get_tool_detail.assert_called_once_with(1, 1)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_update_tool(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool = Mock(spec=ToolResponse)
        mock_tool_app_service.update_tool.return_value = mock_tool
        
        # 发送请求
        response = test_client.put("/api/v1/tools/1", json={
            "name": "Updated Tool",
            "description": "Updated description"
        })
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_app_service.update_tool.assert_called_once_with(1, 1, UpdateToolRequest(**response.json()))
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_delete_tool(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool_app_service.delete_tool.return_value = True
        
        # 发送请求
        response = test_client.delete("/api/v1/tools/1")
        
        # 验证结果
        assert response.status_code == 200
        assert response.json() == {"message": "工具删除成功"}
        mock_tool_app_service.delete_tool.assert_called_once_with(1, 1)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_get_market_tools(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tools = [Mock(spec=ToolMarketResponse)]
        mock_tool_app_service.get_market_tools.return_value = mock_tools
        
        # 发送请求
        response = test_client.get("/api/v1/tools/market/list?skip=0&limit=20")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_app_service.get_market_tools.assert_called_once_with(1, 0, 20)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_install_market_tool(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool_app_service.install_market_tool.return_value = True
        
        # 发送请求
        response = test_client.post("/api/v1/tools/market/install", json={"tool_id": 1})
        
        # 验证结果
        assert response.status_code == 200
        assert response.json() == {"message": "工具安装成功"}
        mock_tool_app_service.install_market_tool.assert_called_once_with(1, InstallToolRequest(tool_id=1))
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_uninstall_tool(test_client, mock_tool_app_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_app_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_app_service = get_tool_app_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_app_service = lambda: mock_tool_app_service
        
        # 准备测试数据
        mock_tool_app_service.uninstall_tool.return_value = True
        
        # 发送请求
        response = test_client.post("/api/v1/tools/market/uninstall", json={"tool_id": 1})
        
        # 验证结果
        assert response.status_code == 200
        assert response.json() == {"message": "工具卸载成功"}
        mock_tool_app_service.uninstall_tool.assert_called_once_with(1, UninstallToolRequest(tool_id=1))
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_app_service = original_get_tool_app_service


async def test_get_tool_versions(test_client, mock_tool_version_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_version_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_version_service = get_tool_version_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_version_service = lambda: mock_tool_version_service
        
        # 准备测试数据
        mock_versions = [Mock(spec=ToolVersionResponse)]
        mock_tool_version_service.get_tool_versions.return_value = mock_versions
        
        # 发送请求
        response = test_client.get("/api/v1/tools/1/versions?skip=0&limit=20")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_version_service.get_tool_versions.assert_called_once_with(1, 1, 0, 20)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_version_service = original_get_tool_version_service


async def test_create_tool_version(test_client, mock_tool_version_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_version_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_version_service = get_tool_version_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_version_service = lambda: mock_tool_version_service
        
        # 准备测试数据
        mock_version = Mock(spec=ToolVersionResponse)
        mock_tool_version_service.create_tool_version.return_value = mock_version
        
        # 发送请求
        response = test_client.post("/api/v1/tools/1/versions", json={
            "version_number": "1.0.0",
            "config": {"key": "value"}
        })
        
        # 验证结果
        assert response.status_code == 200
        request_data = response.json()
        request_data["tool_id"] = 1
        mock_tool_version_service.create_tool_version.assert_called_once_with(1, ToolVersionRequest(**request_data))
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_version_service = original_get_tool_version_service


async def test_publish_tool_version(test_client, mock_tool_version_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_version_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_version_service = get_tool_version_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_version_service = lambda: mock_tool_version_service
        
        # 准备测试数据
        mock_version = Mock(spec=ToolVersionResponse)
        mock_tool_version_service.publish_tool_version.return_value = mock_version
        
        # 发送请求
        response = test_client.post("/api/v1/tools/versions/1/publish")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_version_service.publish_tool_version.assert_called_once_with(1, 1)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_version_service = original_get_tool_version_service


async def test_rollback_tool_version(test_client, mock_tool_version_service, mock_current_user):
    # 模拟依赖项
    from app.api.deps import get_current_user
    from app.infrastructure.dependency_injection import get_tool_version_service
    
    # 保存原始依赖
    original_get_current_user = get_current_user
    original_get_tool_version_service = get_tool_version_service
    
    try:
        # 替换依赖
        get_current_user = lambda: mock_current_user
        get_tool_version_service = lambda: mock_tool_version_service
        
        # 准备测试数据
        mock_version = Mock(spec=ToolVersionResponse)
        mock_tool_version_service.rollback_tool_version.return_value = mock_version
        
        # 发送请求
        response = test_client.post("/api/v1/tools/versions/1/rollback")
        
        # 验证结果
        assert response.status_code == 200
        mock_tool_version_service.rollback_tool_version.assert_called_once_with(1, 1)
    finally:
        # 恢复原始依赖
        get_current_user = original_get_current_user
        get_tool_version_service = original_get_tool_version_service
