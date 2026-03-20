#!/usr/bin/env python3
"""认证模块集成测试"""

import pytest
from fastapi.testclient import TestClient
import os
import time
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入应用
from app.main import app
from app.core.database import create_tables

# 创建数据库表
create_tables()

# 创建测试客户端
client = TestClient(app)


class TestAuthIntegration:
    """认证模块集成测试"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 生成唯一的测试邮箱，避免测试冲突
        self.test_email = f"test_{int(time.time())}@example.com"
        self.test_password = "password123"
        self.test_nickname = "Test User"

    def test_register(self):
        """测试注册端点"""
        # 发送注册请求
        response = client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        # 验证响应
        print(f"注册响应状态码: {response.status_code}")
        print(f"注册响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.test_email
        assert data["nickname"] == self.test_nickname

    def test_login(self):
        """测试登录端点"""
        # 先注册用户
        register_response = client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        print(f"注册响应状态码: {register_response.status_code}")
        
        # 发送登录请求
        response = client.post("/api/v1/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        
        # 验证响应
        print(f"登录响应状态码: {response.status_code}")
        print(f"登录响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token(self):
        """测试刷新令牌端点"""
        # 先注册用户
        client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        # 登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        
        print(f"登录响应内容: {login_response.json()}")
        
        # 确保登录成功
        assert login_response.status_code == 200
        assert "refresh_token" in login_response.json()
        
        # 发送刷新令牌请求
        response = client.post("/api/v1/auth/refresh", json={
            "refresh_token": login_response.json()["refresh_token"]
        })
        
        # 验证响应
        print(f"刷新令牌响应状态码: {response.status_code}")
        print(f"刷新令牌响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_forgot_password(self):
        """测试找回密码端点"""
        # 先注册用户
        client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        # 发送找回密码请求
        response = client.post("/api/v1/auth/forgot-password", json={
            "email": self.test_email
        })
        
        # 验证响应
        print(f"找回密码响应状态码: {response.status_code}")
        print(f"找回密码响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "验证码已发送到您的邮箱"
