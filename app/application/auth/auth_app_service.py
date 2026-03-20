from typing import Optional, Dict, Any, List
import uuid
from sqlalchemy.orm import Session
from app.domain.user.model import UserModel, UserCreate
from app.domain.user.repository import UserRepository, UserSettingsRepository
from app.domain.user.service import UserDomainService
from app.domain.auth.service import AuthDomainService
from app.domain.auth.model import AuthSettingModel, AuthSettingResponse, AuthConfigDTO, AuthSettingUpdate, AuthSettingCreate, LoginMethodDTO
from app.domain.auth.service import AuthSettingDomainService
from app.domain.auth.repository import SQLAlchemyAuthSettingRepository
from app.domain.auth.constant import FeatureType, AuthFeatureKey


class AuthAppService:
    """认证应用服务"""
    
    def __init__(self, user_repo: UserRepository, settings_repo: UserSettingsRepository, db: Session):
        self.user_domain_service = UserDomainService(user_repo, settings_repo, db)
        self.auth_domain_service = AuthDomainService(user_repo, db)
        # 添加认证设置领域服务
        auth_setting_repo = SQLAlchemyAuthSettingRepository(db)
        self.auth_setting_domain_service = AuthSettingDomainService(auth_setting_repo)
    
    def register(self, register_data: UserCreate) -> UserModel:
        """用户注册"""
        return self.user_domain_service.create_user(
            email=register_data.email,
            password=register_data.password,
            nickname=register_data.nickname,
            phone=register_data.phone
        )
    
    def login(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """用户登录"""
        # 认证用户
        user = self.auth_domain_service.authenticate_user(email, password)
        if not user:
            return None
        
        # 生成令牌
        access_token = self.auth_domain_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = self.auth_domain_service.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 15 * 60  # 15分钟
        }
    
    def logout(self, user_id: uuid.UUID) -> bool:
        """用户登出"""
        # 在实际应用中，可能需要将令牌加入黑名单
        # 这里简化处理，返回成功
        return True
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """刷新 JWT Token"""
        # 验证刷新令牌
        payload = self.auth_domain_service.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # 获取用户
        user_id = uuid.UUID(payload.get("sub"))
        user = self.user_domain_service.get_user_by_id(user_id)
        if not user:
            return None
        
        # 生成新的访问令牌
        new_access_token = self.auth_domain_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        new_refresh_token = self.auth_domain_service.create_refresh_token(
            data={"sub": str(user.id)}
        )
        
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": 15 * 60  # 15分钟
        }
    
    def validate_credentials(self, email: str, password: str) -> bool:
        """验证用户凭据"""
        user = self.auth_domain_service.authenticate_user(email, password)
        return user is not None
    
    def send_verification_code(self, email: str) -> bool:
        """发送验证码"""
        # 检查用户是否存在
        user = self.user_domain_service.user_repo.get_by_email(email)
        if not user:
            return False
        # 生成验证码
        code = self.auth_domain_service.generate_verification_code()
        # 存储验证码到 Redis
        self.auth_domain_service.store_verification_code(email, code)
        # 这里应该发送邮件，暂时打印验证码
        print(f"验证码: {code} 已发送到邮箱: {email}")
        return True
    
    def verify_code(self, email: str, code: str, mark_as_used: bool = True) -> bool:
        """验证验证码"""
        return self.auth_domain_service.verify_verification_code(email, code, mark_as_used)

    def reset_password(self, email: str, new_password: str) -> bool:
        """重置密码"""
        return self.auth_domain_service.reset_password(email, new_password)
    
    def get_auth_config(self) -> AuthConfigDTO:
        """获取前端认证配置"""
        # 获取启用的登录方式
        login_settings = self.auth_setting_domain_service.get_enabled_features(FeatureType.LOGIN)
        
        # 构建登录方式 DTO
        login_methods = {}
        feature_to_provider = self.auth_setting_domain_service.get_feature_to_provider_mapping()
        
        for setting in login_settings:
            provider = feature_to_provider.get(setting.feature_key)
            login_method = LoginMethodDTO(
                enabled=setting.enabled,
                name=setting.feature_name,
                provider=provider.value if provider else None
            )
            login_methods[setting.feature_key] = login_method
        
        # 检查注册是否启用
        register_enabled = self.auth_setting_domain_service.is_feature_enabled(AuthFeatureKey.USER_REGISTER)
        
        return AuthConfigDTO(
            loginMethods=login_methods,
            registerEnabled=register_enabled
        )
    
    def get_all_auth_settings(self) -> List[AuthSettingResponse]:
        """获取所有认证配置"""
        settings = self.auth_setting_domain_service.list_all()
        return [self._to_response(setting) for setting in settings]
    
    def get_auth_setting_by_id(self, setting_id: str) -> Optional[AuthSettingResponse]:
        """根据 ID 获取认证配置"""
        setting = self.auth_setting_domain_service.get_by_id(setting_id)
        return self._to_response(setting) if setting else None
    
    def toggle_auth_setting(self, setting_id: str) -> AuthSettingResponse:
        """切换认证配置启用状态"""
        setting = self.auth_setting_domain_service.toggle_enabled(setting_id)
        return self._to_response(setting)
    
    def update_auth_setting(self, setting_id: str, request: AuthSettingUpdate) -> AuthSettingResponse:
        """更新认证配置"""
        setting = self.auth_setting_domain_service.get_by_id(setting_id)
        if not setting:
            raise ValueError(f"认证设置不存在，ID: {setting_id}")
        
        # 更新字段
        if request.feature_name is not None:
            setting.feature_name = request.feature_name
        if request.enabled is not None:
            setting.enabled = request.enabled
        if request.config_data is not None:
            setting.config_data = request.config_data
        if request.display_order is not None:
            setting.display_order = request.display_order
        if request.description is not None:
            setting.description = request.description
        
        updated_setting = self.auth_setting_domain_service.update_auth_setting(setting)
        return self._to_response(updated_setting)
    
    def delete_auth_setting(self, setting_id: str) -> bool:
        """删除认证配置"""
        return self.auth_setting_domain_service.delete_auth_setting(setting_id)
    
    def create_auth_setting(self, setting: AuthSettingModel) -> AuthSettingResponse:
        """创建认证配置"""
        created_setting = self.auth_setting_domain_service.create_auth_setting(setting)
        return self._to_response(created_setting)
    
    def create_auth_setting_from_dto(self, create_dto: 'AuthSettingCreate') -> AuthSettingResponse:
        """从 DTO 创建认证配置"""
        # 转换 DTO 为模型
        setting = AuthSettingModel(
            feature_type=create_dto.feature_type,
            feature_key=create_dto.feature_key,
            feature_name=create_dto.feature_name,
            enabled=create_dto.enabled,
            config_data=create_dto.config_data,
            display_order=create_dto.display_order,
            description=create_dto.description
        )
        return self.create_auth_setting(setting)
    
    def _to_response(self, setting: AuthSettingModel) -> AuthSettingResponse:
        """将实体转换为响应 DTO"""
        return AuthSettingResponse(
            id=setting.id,
            feature_type=setting.feature_type,
            feature_key=setting.feature_key,
            feature_name=setting.feature_name,
            enabled=setting.enabled,
            config_data=setting.config_data,
            display_order=setting.display_order,
            description=setting.description,
            created_at=setting.created_at,
            updated_at=setting.updated_at
        )
