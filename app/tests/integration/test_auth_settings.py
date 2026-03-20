#!/usr/bin/env python3
"""认证设置模块集成测试"""

import pytest
from fastapi.testclient import TestClient
import os
from dotenv import load_dotenv
import uuid

# 加载环境变量
load_dotenv()

# 导入应用
from app.main import app
from app.core.database import create_tables

# 创建数据库表
create_tables()

# 创建测试客户端
client = TestClient(app)


class TestAuthSettingsIntegration:
    """认证设置模块集成测试"""

    def test_get_auth_config(self):
        """测试获取前端认证配置"""
        # 发送请求
        response = client.get("/api/v1/auth/config")
        
        # 验证响应
        print(f"获取认证配置响应状态码: {response.status_code}")
        print(f"获取认证配置响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert "loginMethods" in data
        assert "registerEnabled" in data

    def test_get_all_auth_settings(self):
        """测试获取所有认证设置"""
        # 发送请求
        response = client.get("/api/v1/auth/settings")
        
        # 验证响应
        print(f"获取所有认证设置响应状态码: {response.status_code}")
        print(f"获取所有认证设置响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_create_auth_setting(self):
        """测试创建认证设置"""
        # 准备请求数据
        data = {
            "feature_type": "LOGIN",
            "feature_key": f"TEST_LOGIN_{uuid.uuid4()}",
            "feature_name": "测试登录",
            "enabled": True,
            "config_data": {"test": "value"},
            "display_order": 1,
            "description": "测试登录功能"
        }

        # 发送请求
        response = client.post("/api/v1/auth/settings", json=data)

        # 验证响应
        print(f"创建认证设置响应状态码: {response.status_code}")
        print(f"创建认证设置响应内容: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["feature_key"] == data["feature_key"]
        assert response_data["feature_name"] == data["feature_name"]
        assert response_data["enabled"] == data["enabled"]

    def test_update_auth_setting(self):
        """测试更新认证设置"""
        # 先创建一个认证设置
        create_data = {
            "feature_type": "LOGIN",
            "feature_key": f"UPDATE_TEST_{uuid.uuid4()}",
            "feature_name": "更新测试登录",
            "enabled": True
        }
        create_response = client.post("/api/v1/auth/settings", json=create_data)
        
        print(f"创建认证设置响应状态码: {create_response.status_code}")
        print(f"创建认证设置响应内容: {create_response.json()}")
        
        # 确保创建成功
        assert create_response.status_code == 200
        assert "id" in create_response.json()
        
        setting_id = create_response.json()["id"]

        # 准备更新数据
        update_data = {
            "feature_name": "更新后的测试登录",
            "enabled": False,
            "description": "更新后的测试登录功能"
        }

        # 发送请求
        response = client.put(f"/api/v1/auth/settings/{setting_id}", json=update_data)

        # 验证响应
        print(f"更新认证设置响应状态码: {response.status_code}")
        print(f"更新认证设置响应内容: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["feature_name"] == update_data["feature_name"]
        assert response_data["enabled"] == update_data["enabled"]
        assert response_data["description"] == update_data["description"]

    def test_toggle_auth_setting(self):
        """测试切换认证设置启用状态"""
        # 先创建一个认证设置
        create_data = {
            "feature_type": "LOGIN",
            "feature_key": f"TOGGLE_TEST_{uuid.uuid4()}",
            "feature_name": "切换测试登录",
            "enabled": True
        }
        create_response = client.post("/api/v1/auth/settings", json=create_data)
        
        print(f"创建认证设置响应状态码: {create_response.status_code}")
        print(f"创建认证设置响应内容: {create_response.json()}")
        
        # 确保创建成功
        assert create_response.status_code == 200
        assert "id" in create_response.json()
        
        setting_id = create_response.json()["id"]

        # 发送请求切换状态
        response = client.post(f"/api/v1/auth/settings/{setting_id}/toggle")

        # 验证响应
        print(f"切换认证设置状态响应状态码: {response.status_code}")
        print(f"切换认证设置状态响应内容: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["enabled"] is False

        # 再次切换状态
        response = client.post(f"/api/v1/auth/settings/{setting_id}/toggle")
        print(f"再次切换认证设置状态响应状态码: {response.status_code}")
        print(f"再次切换认证设置状态响应内容: {response.json()}")
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["enabled"] is True

    def test_delete_auth_setting(self):
        """测试删除认证设置"""
        # 先创建一个认证设置
        create_data = {
            "feature_type": "LOGIN",
            "feature_key": f"DELETE_TEST_{uuid.uuid4()}",
            "feature_name": "删除测试登录"
        }
        create_response = client.post("/api/v1/auth/settings", json=create_data)
        
        print(f"创建认证设置响应状态码: {create_response.status_code}")
        print(f"创建认证设置响应内容: {create_response.json()}")
        
        # 确保创建成功
        assert create_response.status_code == 200
        assert "id" in create_response.json()
        
        setting_id = create_response.json()["id"]

        # 发送请求
        response = client.delete(f"/api/v1/auth/settings/{setting_id}")

        # 验证响应
        print(f"删除认证设置响应状态码: {response.status_code}")
        print(f"删除认证设置响应内容: {response.json()}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "删除成功"
