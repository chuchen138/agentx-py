#!/usr/bin/env python3
"""认证API单元测试"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import os
from dotenv import load_dotenv

# 设置测试环境变量
os.environ["TESTING"] = "True"

# 加载环境变量
load_dotenv()

# 确保所有模型都已导入
from app.domain.user.model import UserModel, UserSettingsModel

# 导入数据库相关模块
from app.core.database import Base, engine, SessionLocal

# 导入app
from app.main import app

# 在模块级别创建数据库表
# 确保所有模型都已导入和注册
from app.domain.user.model import UserModel, UserSettingsModel
# 创建数据库表
Base.metadata.create_all(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """设置数据库，创建所有表"""
    yield
    # 测试结束后清理数据库
    db = SessionLocal()
    try:
        db.query(UserSettingsModel).delete()
        db.query(UserModel).delete()
        db.commit()
    finally:
        db.close()


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


def test_register(client):
    """测试注册端点"""
    # 发送注册请求
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "nickname": "Test User",
        "password": "password123"
    })
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["nickname"] == "Test User"


def test_login(client):
    """测试登录端点"""
    # 先注册用户
    client.post("/api/v1/auth/register", json={
        "email": "test_login@example.com",
        "nickname": "Test User",
        "password": "password123"
    })
    
    # 发送登录请求
    response = client.post("/api/v1/auth/login", json={
        "email": "test_login@example.com",
        "password": "password123"
    })
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_refresh_token(client):
    """测试刷新令牌端点"""
    # 先注册用户
    client.post("/api/v1/auth/register", json={
        "email": "test_refresh@example.com",
        "nickname": "Test User",
        "password": "password123"
    })
    
    # 登录获取token
    login_response = client.post("/api/v1/auth/login", json={
        "email": "test_refresh@example.com",
        "password": "password123"
    })
    
    # 发送刷新令牌请求
    response = client.post("/api/v1/auth/refresh", json={
        "refresh_token": login_response.json()["refresh_token"]
    })
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_github_login(client):
    """测试GitHub登录端点"""
    # 模拟SSO服务依赖
    with patch('app.api.v1.auth.routes.get_sso_app_service') as mock_get_sso:
        # 创建模拟服务
        mock_service = Mock()
        mock_service.get_sso_authorization_url.return_value = "https://github.com/login/oauth/authorize"
        mock_get_sso.return_value = mock_service
        
        # 发送授权请求
        response = client.get("/api/v1/auth/sso/github/authorize", params={
            "redirect_uri": "http://localhost:8080"
        })
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "authorize_url" in data


def test_google_login(client):
    """测试Google登录端点"""
    # 模拟SSO服务依赖
    with patch('app.api.v1.auth.routes.get_sso_app_service') as mock_get_sso:
        # 创建模拟服务
        mock_service = Mock()
        mock_service.get_sso_authorization_url.return_value = "https://accounts.google.com/o/oauth2/auth"
        mock_get_sso.return_value = mock_service
        
        # 发送授权请求
        response = client.get("/api/v1/auth/sso/google/authorize", params={
            "redirect_uri": "http://localhost:8080"
        })
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "authorize_url" in data


def test_forgot_password(client):
    """测试找回密码端点"""
    # 先注册用户
    client.post("/api/v1/auth/register", json={
        "email": "test_forgot@example.com",
        "nickname": "Test User",
        "password": "password123"
    })
    
    # 发送找回密码请求
    response = client.post("/api/v1/auth/forgot-password", json={
        "email": "test_forgot@example.com"
    })
    
    # 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "重置链接已发送到您的邮箱"
