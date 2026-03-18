#!/usr/bin/env python3
"""用户领域模型单元测试"""

import pytest
from app.domain.user.model import UserModel, UserSettingsModel, UserCreate, UserUpdate
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
        email=user_data.email,
        nickname=user_data.nickname
    )
    
    # 验证用户属性
    assert user.email == "test@example.com"
    assert user.nickname == "Test User"
    assert user.is_active is True
    assert user.is_superuser is False


def test_user_settings_model_creation():
    """测试用户设置模型创建"""
    user = UserModel(
        email="test@example.com",
        nickname="Test User"
    )
    
    # 创建用户设置
    settings = UserSettingsModel(
        user=user,
        setting_config={
            "theme": "light",
            "language": "zh-CN",
            "email_notifications": True,
            "sms_notifications": False
        }
    )
    
    # 验证设置属性
    assert settings.setting_config["theme"] == "light"
    assert settings.setting_config["language"] == "zh-CN"
    assert settings.setting_config["email_notifications"] is True
    assert settings.setting_config["sms_notifications"] is False
    assert settings.user == user


def test_user_domain_service_password_hashing():
    """测试用户领域服务的密码哈希功能"""
    from unittest.mock import Mock
    from app.domain.user.repository import UserRepository, UserSettingsRepository
    
    # 创建mock依赖
    mock_user_repo = Mock(spec=UserRepository)
    mock_settings_repo = Mock(spec=UserSettingsRepository)
    
    service = UserDomainService(user_repo=mock_user_repo, settings_repo=mock_settings_repo)
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
    
    service = UserDomainService(user_repo=mock_user_repo, settings_repo=mock_settings_repo)
    user = UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email="test@example.com",
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
