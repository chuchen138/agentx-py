import pytest
from app.domain.api_key.model import ApiKey
from datetime import datetime
import uuid


def test_api_key_model():
    """测试 API Key 模型"""
    agent_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    
    # 创建 API Key
    api_key = ApiKey(
        api_key="ak_test_123",
        agent_id=agent_id,
        user_id=user_id,
        name="Test API Key",
        status=True
    )
    
    # 验证属性
    assert api_key.api_key == "ak_test_123"
    assert api_key.agent_id == agent_id
    assert api_key.user_id == user_id
    assert api_key.name == "Test API Key"
    assert api_key.status == True
    assert api_key.usage_count == 0
    assert api_key.last_used_at is None
    assert api_key.expires_at is None
    assert api_key.created_at is not None
    assert api_key.updated_at is not None
    
    # 测试 is_expired 属性
    assert api_key.is_expired == False
    
    # 测试 is_available 属性
    assert api_key.is_available == True
    
    # 测试 update_usage 方法
    api_key.update_usage()
    assert api_key.usage_count == 1
    assert api_key.last_used_at is not None
    assert api_key.updated_at is not None
    
    # 测试状态切换
    api_key.status = False
    assert api_key.is_available == False
