#!/usr/bin/env python3
"""用户应用服务单元测试"""

import pytest
from unittest.mock import Mock
from app.application.user.user_app_service import UserAppService
from app.domain.user.model import UserModel, UserUpdate, PasswordChange
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
from app.domain.user.service import UserDomainService


def test_user_app_service_get_user_by_id():
    """测试通过ID获取用户"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = UserAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 准备测试数据
    user_id = "12345678-1234-5678-1234-567812345678"
    expected_user = UserModel(
        id=user_id,
        email="test@example.com",
        nickname="Test User"
    )
    
    # 模拟仓库行为
    user_repository.get_by_id = Mock(return_value=expected_user)
    
    # 测试获取用户
    user = service.get_user_by_id(user_id)
    assert user == expected_user
    user_repository.get_by_id.assert_called_once_with(user_id)


def test_user_app_service_update_user_profile():
    """测试更新用户资料"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = UserAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 准备测试数据
    user_id = "12345678-1234-5678-1234-567812345678"
    user = UserModel(
        id=user_id,
        email="test@example.com",
        nickname="Test User"
    )
    update_data = UserUpdate(
        nickname="Updated User",
        avatar="https://example.com/avatar.jpg"
    )
    
    # 模拟仓库行为
    user_repository.get_by_id = Mock(return_value=user)
    user_repository.update = Mock(return_value=user)
    
    # 测试更新用户资料
    updated_user = service.update_user_profile(user_id, update_data)
    assert updated_user.nickname == "Updated User"
    assert updated_user.avatar == "https://example.com/avatar.jpg"
    user_repository.get_by_id.assert_called_once_with(user_id)
    user_repository.update.assert_called_once()


def test_user_app_service_change_password():
    """测试修改密码"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository)
    
    # 创建服务实例
    service = UserAppService(
        user_repository=user_repository,
        user_domain_service=user_domain_service
    )
    
    # 准备测试数据
    user_id = "12345678-1234-5678-1234-567812345678"
    user = UserModel(
        id=user_id,
        email="test@example.com",
        nickname="Test User"
    )
    user.password_hash = user_domain_service.get_password_hash("oldpassword")
    
    password_change = PasswordChange(
        current_password="oldpassword",
        new_password="newpassword123"
    )
    
    # 模拟仓库行为
    user_repository.get_by_id = Mock(return_value=user)
    user_repository.update = Mock(return_value=user)
    
    # 测试修改密码
    result = service.change_password(user_id, password_change)
    assert result is True
    assert user_domain_service.verify_password("newpassword123", user.password_hash)
    user_repository.get_by_id.assert_called_once_with(user_id)
    user_repository.update.assert_called_once()
