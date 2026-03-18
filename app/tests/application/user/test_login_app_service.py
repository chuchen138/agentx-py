#!/usr/bin/env python3
"""登录应用服务单元测试"""

import pytest
from unittest.mock import Mock, patch
from app.application.user.login_app_service import LoginAppService
from app.domain.user.model import UserModel, UserCreate, UserLogin
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
from app.domain.user.service import UserDomainService


def test_login_app_service_register():
    """测试用户注册功能"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = LoginAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 准备测试数据
    user_data = UserCreate(
        email="test@example.com",
        nickname="Test User",
        password="password123"
    )
    
    # 模拟仓库行为
    user_repository.get_by_email = Mock(return_value=None)
    user_repository.create = Mock(return_value=UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email=user_data.email,
        nickname=user_data.nickname
    ))
    
    # 测试注册
    user = service.register(user_data)
    assert user is not None
    assert user.email == "test@example.com"
    assert user.nickname == "Test User"
    user_repository.get_by_email.assert_called_once_with("test@example.com")
    user_repository.create.assert_called_once()


def test_login_app_service_login():
    """测试用户登录功能"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = LoginAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 准备测试数据
    login_data = UserLogin(
        email="test@example.com",
        password="password123"
    )
    
    # 创建测试用户
    user = UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email=login_data.email,
        nickname="Test User"
    )
    user.password_hash = user_domain_service.get_password_hash("password123")
    
    # 模拟仓库行为
    user_repository.get_by_email = Mock(return_value=user)
    
    # 测试登录
    token_data = service.login(login_data)
    assert token_data is not None
    assert "access_token" in token_data
    assert "token_type" in token_data
    assert token_data["token_type"] == "bearer"
    user_repository.get_by_email.assert_called_once_with("test@example.com")


def test_login_app_service_refresh_token():
    """测试刷新令牌功能"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = LoginAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 创建测试用户
    user = UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email="test@example.com",
        nickname="Test User"
    )
    
    # 生成访问令牌
    access_token = user_domain_service.create_access_token(user)
    
    # 模拟仓库行为
    user_repository.get_by_id = Mock(return_value=user)
    
    # 测试刷新令牌
    new_token_data = service.refresh_token(access_token)
    assert new_token_data is not None
    assert "access_token" in new_token_data
    assert "token_type" in new_token_data
    assert new_token_data["token_type"] == "bearer"
    user_repository.get_by_id.assert_called_once_with(user.id)
