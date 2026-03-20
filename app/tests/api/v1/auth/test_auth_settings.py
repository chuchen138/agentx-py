import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.auth_setting.model import AuthSettingModel


@pytest.fixture
def db_session():
    """创建一个内存数据库会话"""
    # 创建内存数据库
    engine = create_engine('sqlite:///:memory:')
    # 创建所有表
    Base.metadata.create_all(engine)
    # 创建会话
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    # 清理
    session.close()


@pytest.fixture
def client(db_session):
    """创建测试客户端"""
    # 延迟导入 app，避免提前初始化
    from app.main import app
    # 替换应用的数据库会话
    from app.core.database import get_db
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


class TestAuthSettingsAPI:
    """测试认证设置 API"""

    def test_create_auth_setting(self, client):
        """测试创建认证设置"""
        # 准备请求数据
        data = {
            "feature_type": "LOGIN",
            "feature_key": "API_TEST_LOGIN",
            "feature_name": "API测试登录",
            "enabled": True,
            "config_data": {"test": "value"},
            "display_order": 1,
            "description": "API测试登录功能"
        }

        # 发送请求
        response = client.post("/api/v1/auth/settings", json=data)

        # 验证响应
        assert response.status_code == 200
        assert response.json()["feature_key"] == "API_TEST_LOGIN"
        assert response.json()["feature_name"] == "API测试登录"
        assert response.json()["enabled"] is True

    def test_get_auth_setting_by_id(self, client, db_session):
        """测试获取单个认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="API_GET_LOGIN",
            feature_name="API获取测试登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 发送请求
        response = client.get(f"/api/v1/auth/settings/{auth_setting.id}")

        # 验证响应
        assert response.status_code == 200
        assert response.json()["id"] == str(auth_setting.id)
        assert response.json()["feature_key"] == "API_GET_LOGIN"

    def test_get_all_auth_settings(self, client, db_session):
        """测试获取所有认证设置"""
        # 创建并保存多个认证设置
        login_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="API_LOGIN1",
            feature_name="API登录1"
        )
        register_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="REGISTER",
            feature_key="API_REGISTER1",
            feature_name="API注册1"
        )
        db_session.add(login_setting)
        db_session.add(register_setting)
        db_session.commit()

        # 发送请求
        response = client.get("/api/v1/auth/settings")

        # 验证响应
        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_update_auth_setting(self, client, db_session):
        """测试更新认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="API_UPDATE_LOGIN",
            feature_name="API更新测试登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 准备更新数据
        update_data = {
            "feature_name": "更新后的API测试登录",
            "enabled": False,
            "description": "更新后的API测试登录功能"
        }

        # 发送请求
        response = client.put(f"/api/v1/auth/settings/{auth_setting.id}", json=update_data)

        # 验证响应
        assert response.status_code == 200
        assert response.json()["feature_name"] == "更新后的API测试登录"
        assert response.json()["enabled"] is False
        assert response.json()["description"] == "更新后的API测试登录功能"

    def test_delete_auth_setting(self, client, db_session):
        """测试删除认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="API_DELETE_LOGIN",
            feature_name="API删除测试登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 发送请求
        response = client.delete(f"/api/v1/auth/settings/{auth_setting.id}")

        # 验证响应
        assert response.status_code == 200
        assert response.json()["message"] == "删除成功"

    def test_toggle_auth_setting(self, client, db_session):
        """测试切换认证设置启用状态"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="API_TOGGLE_LOGIN",
            feature_name="API切换测试登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 发送请求
        response = client.post(f"/api/v1/auth/settings/{auth_setting.id}/toggle")

        # 验证响应
        assert response.status_code == 200
        assert response.json()["enabled"] is False

        # 再次切换
        response = client.post(f"/api/v1/auth/settings/{auth_setting.id}/toggle")
        assert response.status_code == 200
        assert response.json()["enabled"] is True
