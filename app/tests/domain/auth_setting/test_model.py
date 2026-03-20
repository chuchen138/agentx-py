import pytest
import uuid
from datetime import datetime
from app.domain.auth_setting.model import AuthSettingModel


class TestAuthSettingModel:
    """测试认证设置模型"""

    def test_create_auth_setting(self):
        """测试创建认证设置"""
        # 创建一个认证设置对象
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="NORMAL_LOGIN",
            feature_name="普通登录",
            enabled=True,
            config_data={"test": "value"},
            display_order=1,
            description="用户名密码登录"
        )

        # 验证属性
        assert auth_setting.feature_type == "LOGIN"
        assert auth_setting.feature_key == "NORMAL_LOGIN"
        assert auth_setting.feature_name == "普通登录"
        assert auth_setting.enabled is True
        assert auth_setting.config_data == {"test": "value"}
        assert auth_setting.display_order == 1
        assert auth_setting.description == "用户名密码登录"

    def test_auth_setting_default_values(self):
        """测试认证设置的默认值"""
        # 创建一个认证设置对象，只设置必要字段
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="GITHUB_LOGIN",
            feature_name="GitHub登录"
        )

        # 验证默认值
        assert auth_setting.enabled is False
        assert auth_setting.config_data == {}
        assert auth_setting.display_order == 0
        assert auth_setting.description is None
