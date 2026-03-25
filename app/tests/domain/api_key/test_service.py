import pytest
from app.domain.api_key.service import ApiKeyService
from app.domain.api_key.model import ApiKey
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, UTC


@pytest.fixture
def api_key_service(db: Session):
    return ApiKeyService(db)


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


def test_generate_api_key(api_key_service: ApiKeyService):
    """测试生成 API 密钥"""
    agent_id = uuid.uuid4()
    api_key = api_key_service.generate_api_key(agent_id)
    
    # 验证密钥格式
    assert api_key.startswith(f"ak_{str(agent_id).replace('-', '_')}_")
    assert len(api_key) > 20


def test_create_api_key(api_key_service: ApiKeyService, db: Session, test_agent: any):
    """测试创建 API 密钥"""
    user_id = test_agent.user_id
    api_key = api_key_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 验证 API Key 创建成功
    assert api_key.id is not None
    assert api_key.agent_id == test_agent.id
    assert api_key.user_id == user_id
    assert api_key.name == "Test API Key"
    assert api_key.status == True
    assert api_key.usage_count == 0


def test_validate_api_key(api_key_service: ApiKeyService, db: Session, test_agent: any):
    """测试验证 API 密钥"""
    user_id = test_agent.user_id
    api_key = api_key_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 验证有效密钥
    valid, returned_user_id, returned_agent_id, message = api_key_service.validate_api_key(api_key.api_key)
    assert valid == True
    assert returned_user_id == user_id
    assert returned_agent_id == test_agent.id
    assert message == "API key is valid"
    
    # 验证使用次数增加
    updated_api_key = db.query(ApiKey).filter(ApiKey.id == api_key.id).first()
    assert updated_api_key.usage_count == 1
    
    # 验证无效密钥
    valid, _, _, message = api_key_service.validate_api_key("invalid_api_key")
    assert valid == False
    assert message == "Invalid API key"


def test_reset_api_key(api_key_service: ApiKeyService, db: Session, test_agent: any):
    """测试重置 API 密钥"""
    user_id = test_agent.user_id
    api_key = api_key_service.create_api_key(user_id, test_agent.id, "Test API Key")
    old_api_key = api_key.api_key
    
    # 重置密钥
    updated_api_key, new_api_key = api_key_service.reset_api_key(api_key.id, user_id)
    
    # 验证密钥已更新
    assert updated_api_key.api_key != old_api_key
    assert updated_api_key.api_key == new_api_key
    assert updated_api_key.usage_count == 0
    assert updated_api_key.last_used_at is None


def test_toggle_api_key_status(api_key_service: ApiKeyService, db: Session, test_agent: any):
    """测试切换 API 密钥状态"""
    user_id = test_agent.user_id
    api_key = api_key_service.create_api_key(user_id, test_agent.id, "Test API Key")
    
    # 禁用密钥
    updated_api_key = api_key_service.toggle_api_key_status(api_key.id, user_id, False)
    assert updated_api_key.status == False
    
    # 验证禁用后无法使用
    valid, _, _, message = api_key_service.validate_api_key(updated_api_key.api_key)
    assert valid == False
    assert message == "API key is disabled"
    
    # 重新启用密钥
    updated_api_key = api_key_service.toggle_api_key_status(api_key.id, user_id, True)
    assert updated_api_key.status == True


def test_delete_api_key(api_key_service: ApiKeyService, db: Session, test_agent: any):
    """测试删除 API 密钥"""
    user_id = test_agent.user_id
    api_key = api_key_service.create_api_key(user_id, test_agent.id, "Test API Key")
    api_key_id = api_key.id
    
    # 删除密钥
    api_key_service.delete_api_key(api_key_id, user_id)
    
    # 验证密钥已删除
    deleted_api_key = db.query(ApiKey).filter(ApiKey.id == api_key_id).first()
    assert deleted_api_key is None
