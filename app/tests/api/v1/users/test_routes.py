#!/usr/bin/env python3
"""用户API单元测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from app.main import app
from app.domain.user.model import UserModel, UserSettingsModel


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_get_current_user(client):
    """测试获取当前用户信息"""
    # 模拟依赖
    with patch('app.api.middleware.auth.get_current_user') as mock_get_current_user:
        # 模拟当前用户
        mock_get_current_user.return_value = UserModel(
            id="12345678-1234-5678-1234-567812345678",
            email="test@example.com",
            nickname="Test User"
        )
        
        # 发送请求
        response = client.get("/api/v1/users/me", headers={
            "Authorization": "Bearer test-token"
        })
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["nickname"] == "Test User"


def test_update_user_profile(client):
    """测试更新用户资料"""
    # 模拟依赖
    with patch('app.api.middleware.auth.get_current_user') as mock_get_current_user:
        with patch('app.api.v1.users.routes.user_app_service') as mock_service:
            # 模拟当前用户
            mock_get_current_user.return_value = UserModel(
                id="12345678-1234-5678-1234-567812345678",
                email="test@example.com",
                nickname="Test User"
            )
            
            # 模拟更新结果
            mock_service.update_user_profile.return_value = UserModel(
                id="12345678-1234-5678-1234-567812345678",
                email="test@example.com",
                nickname="Updated User",
                avatar="https://example.com/avatar.jpg"
            )
            
            # 发送请求
            response = client.put("/api/v1/users/me", headers={
                "Authorization": "Bearer test-token"
            }, json={
                "nickname": "Updated User",
                "avatar": "https://example.com/avatar.jpg"
            })
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["nickname"] == "Updated User"
            assert data["avatar"] == "https://example.com/avatar.jpg"


def test_change_password(client):
    """测试修改密码"""
    # 模拟依赖
    with patch('app.api.middleware.auth.get_current_user') as mock_get_current_user:
        with patch('app.api.v1.users.routes.user_app_service') as mock_service:
            # 模拟当前用户
            mock_get_current_user.return_value = UserModel(
                id="12345678-1234-5678-1234-567812345678",
                email="test@example.com"
            )
            
            # 模拟修改密码结果
            mock_service.change_password.return_value = True
            
            # 发送请求
            response = client.post("/api/v1/users/me/change-password", headers={
                "Authorization": "Bearer test-token"
            }, json={
                "current_password": "oldpassword",
                "new_password": "newpassword123"
            })
            
            # 验证响应
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "Password changed successfully"
