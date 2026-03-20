#!/usr/bin/env python3
"""用户领域模型单元测试"""

import pytest
import uuid
from app.domain.user.model import UserModel, UserSettingsModel, UserCreate, UserUpdate, UserSettingsConfig
from app.domain.user.service import UserDomainService


def test_user_model_creation():
    """测试用户模型创建"""
    user_data = UserCreate(
        email="test@example.com",
        nickname="Test User",
        password="password123"
    )
    
    # 创建用户模型
    user = UserModel(
        id=uuid.uuid4(),
        email=user_data.email,
        password_hash="hashed_password",
        nickname=user_data.nickname
    )
    
    # 验证用户属性
    assert user.email == "test@example.com"
    assert user.nickname == "Test User"
    assert user.login_platform == "normal"
    assert user.is_admin is False


def test_user_settings_model_creation():
    """测试用户设置模型创建"""
    user_id = uuid.uuid4()
    
    # 创建用户设置
    settings = UserSettingsModel(
        id=uuid.uuid4(),
        user_id=user_id,
        setting_config=UserSettingsConfig().model_dump()
    )
    
    # 验证设置属性
    assert settings.user_id == user_id
    assert "default_model" in settings.setting_config
    assert "theme" in settings.setting_config
    assert "language" in settings.setting_config


def test_user_domain_service_password_hashing():
    """测试用户领域服务的密码哈希功能"""
    from unittest.mock import Mock
    from app.domain.user.repository import UserRepository, UserSettingsRepository
    
    # 创建mock依赖
    mock_user_repo = Mock(spec=UserRepository)
    mock_settings_repo = Mock(spec=UserSettingsRepository)
    mock_db = Mock()
    
    service = UserDomainService(user_repo=mock_user_repo, settings_repo=mock_settings_repo, db=mock_db)
    password = "password123"
    
    # 生成密码哈希
    hashed_password = service.get_password_hash(password)
    assert hashed_password != password
    
    # 验证密码
    assert service.verify_password(password, hashed_password)
    assert not service.verify_password("wrongpassword", hashed_password)


def test_user_domain_service_token_creation():
    """测试用户领域服务的令牌创建功能"""
    from unittest.mock import Mock
    from app.domain.user.repository import UserRepository, UserSettingsRepository
    
    # 创建mock依赖
    mock_user_repo = Mock(spec=UserRepository)
    mock_settings_repo = Mock(spec=UserSettingsRepository)
    mock_db = Mock()
    
    service = UserDomainService(user_repo=mock_user_repo, settings_repo=mock_settings_repo, db=mock_db)
    user = UserModel(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    
    # 创建访问令牌
    token = service.create_access_token({"sub": str(user.id), "email": user.email})
    assert token is not None
    assert isinstance(token, str)
    
    # 验证令牌
    payload = service.verify_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user.id)
    assert payload.get("email") == user.email
