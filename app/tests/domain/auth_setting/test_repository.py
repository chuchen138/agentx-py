import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.domain.auth_setting.model import AuthSettingModel
from app.domain.auth_setting.repository import SQLAlchemyAuthSettingRepository


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
def auth_setting_repository(db_session):
    """创建认证设置仓储实例"""
    return SQLAlchemyAuthSettingRepository(db_session)


class TestSQLAlchemyAuthSettingRepository:
    """测试 SQLAlchemy 认证设置仓储"""

    def test_create_auth_setting(self, auth_setting_repository, db_session):
        """测试创建认证设置"""
        # 创建一个认证设置对象
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="NORMAL_LOGIN",
            feature_name="普通登录",
            enabled=True,
            display_order=1,
            description="用户名密码登录"
        )

        # 保存到数据库
        saved_setting = auth_setting_repository.create(auth_setting)

        # 验证保存成功
        assert saved_setting.id == auth_setting.id
        assert saved_setting.feature_type == auth_setting.feature_type
        assert saved_setting.feature_key == auth_setting.feature_key

        # 从数据库中查询
        retrieved_setting = db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first()
        assert retrieved_setting is not None
        assert retrieved_setting.feature_name == "普通登录"

    def test_get_by_id(self, auth_setting_repository, db_session):
        """测试根据 ID 获取认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="GITHUB_LOGIN",
            feature_name="GitHub登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 根据 ID 查询
        retrieved_setting = auth_setting_repository.get_by_id(auth_setting.id)

        # 验证查询成功
        assert retrieved_setting is not None
        assert retrieved_setting.id == auth_setting.id
        assert retrieved_setting.feature_key == "GITHUB_LOGIN"

    def test_get_by_feature_key(self, auth_setting_repository, db_session):
        """测试根据功能键获取认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="COMMUNITY_LOGIN",
            feature_name="敲鸭登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 根据功能键查询
        retrieved_setting = auth_setting_repository.get_by_feature_key("COMMUNITY_LOGIN")

        # 验证查询成功
        assert retrieved_setting is not None
        assert retrieved_setting.feature_key == "COMMUNITY_LOGIN"
        assert retrieved_setting.feature_name == "敲鸭登录"

    def test_get_by_feature_type(self, auth_setting_repository, db_session):
        """测试根据功能类型获取认证设置"""
        # 创建并保存多个认证设置
        login_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="NORMAL_LOGIN",
            feature_name="普通登录"
        )
        register_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="REGISTER",
            feature_key="USER_REGISTER",
            feature_name="用户注册"
        )
        db_session.add(login_setting)
        db_session.add(register_setting)
        db_session.commit()

        # 根据功能类型查询
        login_settings = auth_setting_repository.get_by_feature_type("LOGIN")
        register_settings = auth_setting_repository.get_by_feature_type("REGISTER")

        # 验证查询成功
        assert len(login_settings) == 1
        assert login_settings[0].feature_key == "NORMAL_LOGIN"
        assert len(register_settings) == 1
        assert register_settings[0].feature_key == "USER_REGISTER"

    def test_update_auth_setting(self, auth_setting_repository, db_session):
        """测试更新认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="NORMAL_LOGIN",
            feature_name="普通登录",
            enabled=True
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 更新认证设置
        auth_setting.enabled = False
        auth_setting.feature_name = "普通登录（已禁用）"
        updated_setting = auth_setting_repository.update(auth_setting)

        # 验证更新成功
        assert updated_setting.enabled is False
        assert updated_setting.feature_name == "普通登录（已禁用）"

        # 从数据库中查询验证
        retrieved_setting = db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first()
        assert retrieved_setting.enabled is False
        assert retrieved_setting.feature_name == "普通登录（已禁用）"

    def test_delete_auth_setting(self, auth_setting_repository, db_session):
        """测试删除认证设置"""
        # 创建并保存一个认证设置
        auth_setting = AuthSettingModel(
            id=uuid.uuid4(),
            feature_type="LOGIN",
            feature_key="TEST_LOGIN",
            feature_name="测试登录"
        )
        db_session.add(auth_setting)
        db_session.commit()

        # 验证存在
        assert db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first() is not None

        # 删除认证设置
        result = auth_setting_repository.delete(auth_setting.id)

        # 验证删除成功
        assert result is True
        assert db_session.query(AuthSettingModel).filter_by(id=auth_setting.id).first() is None
