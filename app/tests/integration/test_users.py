#!/usr/bin/env python3
"""用户模块集成测试"""

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


class TestUsersIntegration:
    """用户模块集成测试"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        # 生成唯一的测试邮箱，避免测试冲突
        import random
        self.test_email = f"test_user_{int(time.time())}_{random.randint(1000, 9999)}@example.com"
        self.test_password = "password123"
        self.test_nickname = "Test User"

    def test_get_current_user(self):
        """测试获取当前用户信息"""
        # 先注册用户
        register_response = client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        print(f"注册响应状态码: {register_response.status_code}")
        
        # 登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应内容: {login_response.json()}")
        
        # 确保登录成功
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        access_token = login_response.json()["access_token"]
        
        # 发送获取当前用户请求
        response = client.get("/api/v1/users/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        # 验证响应
        print(f"获取用户信息响应状态码: {response.status_code}")
        print(f"获取用户信息响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == self.test_email
        assert data["nickname"] == self.test_nickname

    def test_update_user_profile(self):
        """测试更新用户资料"""
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
        
        # 确保登录成功
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        access_token = login_response.json()["access_token"]
        
        # 发送更新用户资料请求
        response = client.put("/api/v1/users/me", headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "nickname": "Updated User",
            "phone": "13800138000",
            "avatar_url": "https://example.com/avatar.jpg"
        })
        
        # 验证响应
        print(f"更新用户资料响应状态码: {response.status_code}")
        print(f"更新用户资料响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["nickname"] == "Updated User"
        assert data["phone"] == "13800138000"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"

    def test_change_password(self):
        """测试修改密码"""
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
        
        # 确保登录成功
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        access_token = login_response.json()["access_token"]
        
        # 发送修改密码请求
        response = client.post("/api/v1/users/me/change-password", headers={
            "Authorization": f"Bearer {access_token}"
        }, json={
            "current_password": self.test_password,
            "new_password": "newpassword123",
            "confirm_password": "newpassword123"
        })
        
        # 验证响应
        print(f"修改密码响应状态码: {response.status_code}")
        print(f"修改密码响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "密码修改成功"

    def test_delete_user(self):
        """测试删除用户"""
        # 先注册用户
        register_response = client.post("/api/v1/auth/register", json={
            "email": self.test_email,
            "nickname": self.test_nickname,
            "password": self.test_password
        })
        
        print(f"注册响应状态码: {register_response.status_code}")
        print(f"注册响应内容: {register_response.json()}")
        
        # 确保注册成功
        assert register_response.status_code == 200
        
        # 登录获取token
        login_response = client.post("/api/v1/auth/login", json={
            "email": self.test_email,
            "password": self.test_password
        })
        
        print(f"登录响应状态码: {login_response.status_code}")
        print(f"登录响应内容: {login_response.json()}")
        
        # 确保登录成功
        assert login_response.status_code == 200
        assert "access_token" in login_response.json()
        
        access_token = login_response.json()["access_token"]
        
        # 发送删除用户请求
        response = client.delete("/api/v1/users/me", headers={
            "Authorization": f"Bearer {access_token}"
        })
        
        # 验证响应
        print(f"删除用户响应状态码: {response.status_code}")
        print(f"删除用户响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "用户删除成功"
