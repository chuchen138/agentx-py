import pytest
from app.application.api_key.api_key_app_service import ApiKeyAppService
from sqlalchemy.orm import Session
import uuid


@pytest.fixture
def api_key_app_service(db: Session):
    return ApiKeyAppService(db)


@pytest.fixture
def test_agent(db: Session):
    """创建测试 Agent"""
    from app.domain.agent.model import Agent
    agent = Agent(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test Agent",
        description="Test Agent Description",
        system_prompt="You are a test agent",
        status="ENABLED"
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


def test_create_api_key(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试创建 API 密钥"""
    user_id = test_agent.user_id
    response = api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 验证响应
    assert response.id is not None
    assert response.agent_id == test_agent.id
    assert response.user_id == user_id
    assert response.name == "Test API Key"
    assert response.status == True
    assert response.usage_count == 0
    assert response.api_key is not None  # 仅创建时返回
    assert response.agent_name == "Test Agent"


def test_get_api_keys(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试获取 API 密钥列表"""
    user_id = test_agent.user_id
    
    # 创建两个 API 密钥
    api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key 1")
    api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key 2")
    
    # 获取密钥列表
    keys = api_key_app_service.get_api_keys(user_id)
    assert len(keys) >= 2
    assert all(key.agent_name == "Test Agent" for key in keys)
    assert all(key.api_key.startswith("ak_") for key in keys)


def test_get_api_key(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试获取 API 密钥详情"""
    user_id = test_agent.user_id
    created_key = api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 获取密钥详情
    retrieved_key = api_key_app_service.get_api_key(created_key.id, user_id)
    assert retrieved_key.id == created_key.id
    assert retrieved_key.name == "Test API Key"
    assert retrieved_key.api_key is None  # 详情不返回密钥值


def test_update_api_key(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试更新 API 密钥"""
    user_id = test_agent.user_id
    created_key = api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 更新密钥
    updated_key = api_key_app_service.update_api_key(
        created_key.id,
        user_id,
        name="Updated API Key",
        status=False
    )
    
    assert updated_key.name == "Updated API Key"
    assert updated_key.status == False


def test_reset_api_key(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试重置 API 密钥"""
    user_id = test_agent.user_id
    created_key = api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 重置密钥
    reset_response = api_key_app_service.reset_api_key(created_key.id, user_id)
    assert reset_response.id == created_key.id
    assert reset_response.new_api_key is not None
    assert reset_response.message == "API key reset successfully"


def test_validate_api_key(api_key_app_service: ApiKeyAppService, test_agent: any):
    """测试验证 API 密钥"""
    user_id = test_agent.user_id
    created_key = api_key_app_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 验证有效密钥
    validation = api_key_app_service.validate_api_key(created_key.api_key)
    assert validation.valid == True
    assert validation.user_id == user_id
    assert validation.agent_id == test_agent.id
    assert validation.message == "API key is valid"
    
    # 验证无效密钥
    validation = api_key_app_service.validate_api_key("invalid_api_key")
    assert validation.valid == False
    assert validation.user_id is None
    assert validation.agent_id is None
    assert validation.message == "Invalid API key"
