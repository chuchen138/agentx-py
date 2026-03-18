#!/usr/bin/env python3
"""用户仓库单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from app.domain.user.model import UserModel, UserSettingsModel
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository


def test_sqlalchemy_user_repository_create():
    """测试用户仓库创建用户"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserRepository(db)
    
    # 创建用户实例
    user = UserModel(
        email="test@example.com",
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
    expected_user = UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email="test@example.com",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    user_id = "12345678-1234-5678-1234-567812345678"
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
        email="test@example.com",
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
        github_id="12345",
        email="test@example.com",
        nickname="Test User"
    )
    db.query.return_value.filter.return_value.first.return_value = expected_user
    
    # 测试获取用户
    github_id = "12345"
    user = repository.get_by_github_id(github_id)
    db.query.assert_called_once_with(UserModel)
    db.query.return_value.filter.assert_called_once()
    assert user == expected_user


def test_sqlalchemy_user_settings_repository_get_by_user_id():
    """测试用户设置仓库通过用户ID获取设置"""
    # 创建mock数据库会话
    db = Mock()
    repository = SQLAlchemyUserSettingsRepository(db)
    
    # 模拟查询结果
    user = UserModel(
        id="12345678-1234-5678-1234-567812345678",
        email="test@example.com"
    )
    expected_settings = UserSettingsModel(
        user=user,
        setting_config={
            "theme": "light",
            "language": "zh-CN"
        }
    )
    db.query.return_value.filter.return_value.first.return_value = expected_settings
    
    # 测试获取设置
    user_id = "12345678-1234-5678-1234-567812345678"
    settings = repository.get_by_user_id(user_id)
    db.query.assert_called_once_with(UserSettingsModel)
    db.query.return_value.filter.assert_called_once()
    assert settings == expected_settings
