import pytest
import uuid
from app.domain.auth_setting.model import AuthSettingModel
from app.domain.auth_setting.repository import SQLAlchemyAuthSettingRepository
from app.domain.auth_setting.service import AuthSettingDomainService
from app.domain.auth_setting.constant import FeatureType, AuthFeatureKey


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
    return AuthSettingDomainService(auth_setting_repository)


class TestAuthSettingDomainService:
    """测试认证设置领域服务"""

    def test_create_auth_setting(self, auth_setting_domain_service, db_session):
        """测试创建认证设置"""
        # 创建一个认证设置对象
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="TEST_LOGIN",
            feature_name="测试登录",
            enabled=True
        )

        # 保存到数据库
        created_setting = auth_setting_domain_service.create_auth_setting(auth_setting)

        # 验证创建成功
        assert created_setting is not None
        assert created_setting.feature_key == "TEST_LOGIN"

    def test_create_auth_setting_with_duplicate_feature_key(self, auth_setting_domain_service, db_session):
        """测试创建重复功能键的认证设置"""
        # 创建第一个认证设置
        auth_setting1 = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="DUPLICATE_KEY",
            feature_name="测试登录1"
        )
        auth_setting_domain_service.create_auth_setting(auth_setting1)

        # 尝试创建相同功能键的认证设置
        auth_setting2 = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="DUPLICATE_KEY",
            feature_name="测试登录2"
        )

        # 验证抛出异常
        with pytest.raises(ValueError, match="功能键 DUPLICATE_KEY 已存在"):
            auth_setting_domain_service.create_auth_setting(auth_setting2)

    def test_get_enabled_features(self, auth_setting_domain_service, db_session):
        """测试获取启用的功能"""
        # 创建并保存多个认证设置
        enabled_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="ENABLED_LOGIN",
            feature_name="启用的登录",
            enabled=True
        )
        disabled_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="DISABLED_LOGIN",
            feature_name="禁用的登录",
            enabled=False
        )
        db_session.add(enabled_setting)
        db_session.add(disabled_setting)
        db_session.commit()

        # 获取启用的功能
        enabled_features = auth_setting_domain_service.get_enabled_features("LOGIN")

        # 验证只返回启用的功能
        assert len(enabled_features) == 1
        assert enabled_features[0].feature_key == "ENABLED_LOGIN"
        assert enabled_features[0].enabled is True

    def test_is_feature_enabled(self, auth_setting_domain_service, db_session):
        """测试检查功能是否启用"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="REGISTER",
            feature_key="USER_REGISTER",
            feature_name="用户注册",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 检查功能是否启用
        is_enabled = auth_setting_domain_service.is_feature_enabled("USER_REGISTER")

        # 验证返回正确的启用状态
        assert is_enabled is True

    def test_toggle_enabled(self, auth_setting_domain_service, db_session):
        """测试切换启用状态"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="TOGGLE_LOGIN",
            feature_name="切换登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 切换启用状态
        toggled_setting = auth_setting_domain_service.toggle_enabled(auth_setting.id)

        # 验证状态已切换
        assert toggled_setting.enabled is False

        # 再次切换
        toggled_setting = auth_setting_domain_service.toggle_enabled(auth_setting.id)
        assert toggled_setting.enabled is True

    def test_get_feature_to_provider_mapping(self, auth_setting_domain_service):
        """测试获取功能键到提供商的映射"""
        # 获取映射
        mapping = auth_setting_domain_service.get_feature_to_provider_mapping()

        # 验证映射包含预期的键值对
        assert "GITHUB_LOGIN" in mapping
        assert "COMMUNITY_LOGIN" in mapping
        assert mapping["GITHUB_LOGIN"].value == "GITHUB"
        assert mapping["COMMUNITY_LOGIN"].value == "COMMUNITY"
