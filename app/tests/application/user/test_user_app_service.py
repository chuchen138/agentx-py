#!/usr/bin/env python3
"""用户应用服务单元测试"""

import pytest
import uuid
from unittest.mock import Mock
from app.application.user.user_app_service import UserAppService
from app.domain.user.model import UserModel, UserUpdate
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
from app.domain.user.service import UserDomainService


def test_user_app_service_get_current_user():
    """测试获取当前用户"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository, db=db)
    
    # 创建服务实例
    service = UserAppService(user_domain_service=user_domain_service)
    
    # 准备测试数据
    user_id = uuid.uuid4()
    expected_user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    
    # 模拟服务行为
    user_domain_service.get_user_by_id = Mock(return_value=expected_user)
    
    # 测试获取用户
    user = service.get_current_user(user_id)
    assert user == expected_user
    user_domain_service.get_user_by_id.assert_called_once_with(user_id)


def test_user_app_service_update_user_profile():
    """测试更新用户资料"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository, db=db)
    
    # 创建服务实例
    service = UserAppService(user_domain_service=user_domain_service)
    
    # 准备测试数据
    user_id = uuid.uuid4()
    user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    update_data = UserUpdate(
        nickname="Updated User",
        phone="13800138000",
        avatar_url="https://example.com/avatar.jpg"
    )
    
    # 模拟服务行为
    user_domain_service.get_user_by_id = Mock(return_value=user)
    user_domain_service.update_user = Mock(return_value=user)
    
    # 测试更新用户资料
    updated_user = service.update_user_profile(user_id, update_data)
    assert updated_user.nickname == "Updated User"
    assert updated_user.phone == "13800138000"
    assert updated_user.avatar_url == "https://example.com/avatar.jpg"
    user_domain_service.get_user_by_id.assert_called_once_with(user_id)
    user_domain_service.update_user.assert_called_once()


def test_user_app_service_change_password():
    """测试修改密码"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository, db=db)
    
    # 创建服务实例
    service = UserAppService(user_domain_service=user_domain_service)
    
    # 准备测试数据
    user_id = uuid.uuid4()
    user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    user.password_hash = user_domain_service.get_password_hash("oldpassword")
    
    # 模拟服务行为
    user_domain_service.get_user_by_id = Mock(return_value=user)
    user_domain_service.update_user = Mock(return_value=user)
    user_domain_service.verify_password = Mock(return_value=True)
    user_domain_service.get_password_hash = Mock(return_value="new_hashed_password")
    
    # 测试修改密码
    result = service.change_password(user_id, "oldpassword", "newpassword123")
    assert result is True
    user_domain_service.get_user_by_id.assert_called_once_with(user_id)
    user_domain_service.verify_password.assert_called_once_with("oldpassword", user.password_hash)
    user_domain_service.get_password_hash.assert_called_once_with("newpassword123")
    user_domain_service.update_user.assert_called_once()


def test_user_app_service_delete_user():
    """测试删除用户"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository, db=db)
    
    # 创建服务实例
    service = UserAppService(user_domain_service=user_domain_service)
    
    # 准备测试数据
    user_id = uuid.uuid4()
    
    # 模拟服务行为
    user_domain_service.delete_user = Mock(return_value=True)
    
    # 测试删除用户
    result = service.delete_user(user_id)
    assert result is True
    user_domain_service.delete_user.assert_called_once_with(user_id)


def test_user_app_service_validate_user():
    """测试验证用户"""
    # 创建mock依赖
    db = Mock()
    user_repository = SQLAlchemyUserRepository(db)
    settings_repository = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo=user_repository, settings_repo=settings_repository, db=db)
    
    # 创建服务实例
    service = UserAppService(user_domain_service=user_domain_service)
    
    # 准备测试数据
    user_id = uuid.uuid4()
    user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    
    # 模拟服务行为
    user_domain_service.get_user_by_id = Mock(return_value=user)
    
    # 测试验证用户
    result = service.validate_user(user_id)
    assert result is True
    user_domain_service.get_user_by_id.assert_called_once_with(user_id)
