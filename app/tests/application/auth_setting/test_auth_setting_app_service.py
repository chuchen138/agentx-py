import pytest
import uuid
from app.domain.auth_setting.model import AuthSettingModel, AuthSettingCreate, AuthSettingUpdate
from app.domain.auth_setting.repository import SQLAlchemyAuthSettingRepository
from app.application.auth_setting.auth_setting_app_service import AuthSettingAppService


@pytest.fixture
def db_session():
    """创建一个内存数据库会话"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from app.core.database import Base
    
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
def auth_setting_repository(db_session):
    """创建认证设置仓储实例"""
    return SQLAlchemyAuthSettingRepository(db_session)


@pytest.fixture
def auth_setting_domain_service(auth_setting_repository):
    """创建认证设置领域服务实例"""
    from app.domain.auth_setting.service import AuthSettingDomainService
    return AuthSettingDomainService(auth_setting_repository)


@pytest.fixture
def auth_setting_app_service(auth_setting_domain_service):
    """创建认证设置应用服务实例"""
    return AuthSettingAppService(auth_setting_domain_service)


class TestAuthSettingAppService:
    """测试认证设置应用服务"""

    def test_create_auth_setting(self, auth_setting_app_service, db_session):
        """测试创建认证设置"""
        # 创建认证设置创建模型
        create_data = AuthSettingCreate(
            feature_type="LOGIN",
            feature_key="TEST_LOGIN",
            feature_name="测试登录",
            enabled=True,
            config_data={"test": "value"},
            display_order=1,
            description="测试登录功能"
        )

        # 调用应用服务创建认证设置
        created_setting = auth_setting_app_service.create_auth_setting_from_dto(create_data)

        # 验证创建成功
        assert created_setting is not None
        assert created_setting.feature_key == "TEST_LOGIN"
        assert created_setting.feature_name == "测试登录"
        assert created_setting.enabled is True

    def test_update_auth_setting(self, auth_setting_app_service, db_session):
        """测试更新认证设置"""
        # 先创建一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="UPDATE_LOGIN",
            feature_name="更新测试登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 创建更新数据
        update_data = AuthSettingUpdate(
            feature_name="更新后的测试登录",
            enabled=False,
            description="更新后的测试登录功能"
        )

        # 调用应用服务更新认证设置
        updated_setting = auth_setting_app_service.update_auth_setting(auth_setting.id, update_data)

        # 验证更新成功
        assert updated_setting is not None
        assert updated_setting.feature_name == "更新后的测试登录"
        assert updated_setting.enabled is False
        assert updated_setting.description == "更新后的测试登录功能"

    def test_get_auth_setting_by_id(self, auth_setting_app_service, db_session):
        """测试根据 ID 获取认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="GET_LOGIN",
            feature_name="获取测试登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 调用应用服务获取认证设置
        retrieved_setting = auth_setting_app_service.get_auth_setting_by_id(auth_setting.id)

        # 验证获取成功
        assert retrieved_setting is not None
        assert retrieved_setting.id == auth_setting.id
        assert retrieved_setting.feature_key == "GET_LOGIN"

    def test_get_all_auth_settings(self, auth_setting_app_service, db_session):
        """测试获取所有认证设置"""
        # 创建并保存多个认证设置
        login_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="LOGIN1",
            feature_name="登录1"
        )
        register_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="REGISTER",
            feature_key="REGISTER1",
            feature_name="注册1"
        )
        db_session.add(login_setting)
        db_session.add(register_setting)
        db_session.commit()

        # 调用应用服务获取所有认证设置
        all_settings = auth_setting_app_service.get_all_auth_settings()

        # 验证获取成功
        assert len(all_settings) == 2

    def test_delete_auth_setting(self, auth_setting_app_service, db_session):
        """测试删除认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="DELETE_LOGIN",
            feature_name="删除测试登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 验证存在
        assert db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first() is not None

        # 调用应用服务删除认证设置
        result = auth_setting_app_service.delete_auth_setting(auth_setting.id)

        # 验证删除成功
        assert result is True
        assert db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first() is None

    def test_toggle_auth_setting(self, auth_setting_app_service, db_session):
        """测试切换认证设置启用状态"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="TOGGLE_LOGIN",
            feature_name="切换测试登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 调用应用服务切换启用状态
        toggled_setting = auth_setting_app_service.toggle_auth_setting(auth_setting.id)

        # 验证状态已切换
        assert toggled_setting.enabled is False

        # 再次切换
        toggled_setting = auth_setting_app_service.toggle_auth_setting(auth_setting.id)
        assert toggled_setting.enabled is True
