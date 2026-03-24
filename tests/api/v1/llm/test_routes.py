from fastapi.testclient import TestClient
from app.main import app
import pytest

client = TestClient(app)


class TestLLMRoutes:
    """LLM 路由测试"""

    def test_create_provider(self):
        """测试创建服务商"""
        response = client.post(
            "/api/v1/llm/providers",
            json={
                "name": "Test Provider",
                "protocol": "OPENAI",
                "description": "Test provider",
                "config": {
                    "api_key": "test-api-key",
                    "base_url": "https://api.example.com/v1"
                },
                "status": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Provider"
        assert data["protocol"] == "OPENAI"
        assert data["status"] == True

    def test_get_providers(self):
        """测试获取服务商列表"""
        response = client.get("/api/v1/llm/providers?provider_type=ALL")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_refresh_provider_status(self):
        """测试刷新服务商状态"""
        # 先创建一个服务商
        create_response = client.post(
            "/api/v1/llm/providers",
            json={
                "name": "Test Provider for Refresh",
                "protocol": "OPENAI",
                "description": "Test provider for refresh",
                "config": {
                    "api_key": "test-api-key",
                    "base_url": "https://api.example.com/v1"
                },
                "status": True
            }
        )
        provider_id = create_response.json()["id"]

        # 刷新状态
        refresh_response = client.post(f"/api/v1/llm/providers/{provider_id}/refresh-status")
        assert refresh_response.status_code == 200
        data = refresh_response.json()
        assert data["message"] == "Provider status refreshed successfully"

    def test_create_model(self):
        """测试创建模型"""
        # 先创建一个服务商
        create_response = client.post(
            "/api/v1/llm/providers",
            json={
                "name": "Test Provider for Model",
                "protocol": "OPENAI",
                "description": "Test provider for model",
                "config": {
                    "api_key": "test-api-key",
                    "base_url": "https://api.example.com/v1"
                },
                "status": True
            }
        )
        provider_id = create_response.json()["id"]

        # 创建模型
        response = client.post(
            "/api/v1/llm/models",
            json={
                "provider_id": provider_id,
                "model_id": "test-model",
                "name": "Test Model",
                "description": "Test model",
                "model_endpoint": "test-model",
                "type": "CHAT",
                "status": True
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Model"
        assert data["model_id"] == "test-model"
        assert data["type"] == "CHAT"

    def test_get_active_models(self):
        """测试获取激活的模型"""
        response = client.get("/api/v1/llm/models/active?provider_type=ALL&model_type=CHAT")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_save_preference(self):
        """测试保存用户偏好设置"""
        response = client.post(
            "/api/v1/llm/preference",
            json={
                "provider_id": "test-provider",
                "model_id": "test-model"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Preference saved successfully"

    def test_get_preference(self):
        """测试获取用户偏好设置"""
        response = client.get("/api/v1/llm/preference")
        assert response.status_code == 200

    def test_chat(self):
        """测试与模型对话"""
        response = client.post(
            "/api/v1/llm/chat",
            json={
                "model_id": "test-model",
                "message": "Hello"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
