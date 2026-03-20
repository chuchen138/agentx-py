#!/usr/bin/env python3
"""用户仓库单元测试"""

import pytest
import uuid
from unittest.mock import Mock
from app.domain.user.model import UserModel, UserSettingsModel, UserSettingsConfig
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository


def test_sqlalchemy_user_repository_create():
    """测试用户仓库创建用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 创建用户实例
    user = UserModel(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    
    # 测试创建用户
    created_user = repository.create(user)
    db.add.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)
    assert created_user == user


def test_sqlalchemy_user_repository_get_by_id():
    """测试用户仓库通过ID获取用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 模拟查询结果
    user_id = uuid.uuid4()
    expected_user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    user = repository.get_by_id(user_id)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    assert user == expected_user


def test_sqlalchemy_user_repository_get_by_email():
    """测试用户仓库通过邮箱获取用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 模拟查询结果
    expected_user = UserModel(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    email = "test@example.com"
    user = repository.get_by_email(email)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    assert user == expected_user


def test_sqlalchemy_user_repository_get_by_github_id():
    """测试用户仓库通过GitHub ID获取用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 模拟查询结果
    expected_user = UserModel(
        id=uuid.uuid4(),
        github_id="12345",
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    github_id = "12345"
    user = repository.get_by_github_id(github_id)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    assert user == expected_user


def test_sqlalchemy_user_repository_get_by_google_id():
    """测试用户仓库通过Google ID获取用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 模拟查询结果
    expected_user = UserModel(
        id=uuid.uuid4(),
        google_id="123456789",
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    google_id = "123456789"
    user = repository.get_by_google_id(google_id)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    assert user == expected_user


def test_sqlalchemy_user_repository_update():
    """测试用户仓库更新用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 创建用户实例
    user = UserModel(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    
    # 测试更新用户
    updated_user = repository.update(user)
    db.add.assert_called_once_with(user)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(user)
    assert updated_user == user


def test_sqlalchemy_user_repository_delete():
    """测试用户仓库删除用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 模拟查询结果
    user_id = uuid.uuid4()
    user = UserModel(
        id=user_id,
        email="test@example.com",
        password_hash="hashed_password",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = user
    
    # 测试删除用户
    result = repository.delete(user_id)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    db.delete.assert_called_once_with(user)
    db.commit.assert_called_once()
    assert result is True


def test_sqlalchemy_user_settings_repository_create():
    """测试用户设置仓库创建设置"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserSettingsRepository(db)
    
    # 创建用户设置实例
    user_id = uuid.uuid4()
    settings = UserSettingsModel(
        id=uuid.uuid4(),
        user_id=user_id,
        setting_config=UserSettingsConfig().model_dump()
    )
    
    # 测试创建设置
    created_settings = repository.create(settings)
    db.add.assert_called_once_with(settings)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(settings)
    assert created_settings == settings


def test_sqlalchemy_user_settings_repository_get_by_user_id():
    """测试用户设置仓库通过用户ID获取设置"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserSettingsRepository(db)
    
    # 模拟查询结果
    user_id = uuid.uuid4()
    expected_settings = UserSettingsModel(
        id=uuid.uuid4(),
        user_id=user_id,
        setting_config=UserSettingsConfig().model_dump()
    )
    db.query.return_value.filter.return_value.first.return_value = expected_settings
    
    # 测试获取设置
    settings = repository.get_by_user_id(user_id)
    db.query.assert_called_once_with(UserSettingsModel)
    db.query.return_value.filter.assert_called_once()
    assert settings == expected_settings


def test_sqlalchemy_user_settings_repository_update():
    """测试用户设置仓库更新设置"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserSettingsRepository(db)
    
    # 创建用户设置实例
    user_id = uuid.uuid4()
    settings = UserSettingsModel(
        id=uuid.uuid4(),
        user_id=user_id,
        setting_config=UserSettingsConfig().model_dump()
    )
    
    # 测试更新设置
    updated_settings = repository.update(settings)
    db.add.assert_called_once_with(settings)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(settings)
    assert updated_settings == settings
