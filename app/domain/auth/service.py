from typing import Optional, Dict, Any, List
import uuid
import random
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.domain.user.model import UserModel
from app.domain.user.repository import UserRepository
from app.domain.auth.model import VerificationCode, AuthSettingModel
from app.domain.auth.repository import AuthSettingRepository
from app.domain.auth.constant import AuthFeatureKey, FeatureType, SsoProvider

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


class AuthDomainService:
    """认证领域服务"""
    
    def __init__(self, user_repo: UserRepository, db: Session):
        self.user_repo = user_repo
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        # 截断密码，确保不超过 bcrypt 的 72 字节限制
        password = password[:72]
        return pwd_context.hash(password)
    
    def authenticate_user(self, email: str, password: str) -> Optional[UserModel]:
        """认证用户"""
        user = self.user_repo.get_by_email(email)
        if not user:
            return None
        if not self.verify_password(password, user.password_hash):
            return None
        return user
    
    def create_access_token(self, data: dict) -> str:
        """创建访问令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def create_refresh_token(self, data: dict) -> str:
        """创建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[dict]:
        """验证令牌"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except JWTError:
            return None
    
    def generate_verification_code(self) -> str:
        """生成6位数字验证码"""
        return ''.join(random.choices('0123456789', k=6))
    
    def store_verification_code(self, email: str, code: str) -> None:
        """存储验证码到 PostgreSQL"""
        try:
            # 计算过期时间（10分钟后）
            expires_at = datetime.utcnow() + timedelta(minutes=10)
            
            # 创建验证码记录
            verification_code = VerificationCode(
                email=email,
                code=code,
                expires_at=expires_at
            )
            
            # 保存到数据库
            self.db.add(verification_code)
            self.db.commit()
        except Exception:
            # 如果数据库操作失败，忽略错误
            pass
    
    def verify_verification_code(self, email: str, code: str, mark_as_used: bool = True) -> bool:
        """验证验证码"""
        try:
            # 查找未使用且未过期的验证码
            now = datetime.utcnow()
            verification_code = self.db.query(VerificationCode).filter(
                VerificationCode.email == email,
                VerificationCode.code == code,
                VerificationCode.is_used == False,
                VerificationCode.expires_at > now
            ).first()
            
            if not verification_code:
                return False
            
            # 标记验证码为已使用（如果需要）
            if mark_as_used:
                verification_code.is_used = True
                self.db.commit()
            
            return True
        except Exception:
            # 如果数据库操作失败，返回 False
            return False
    
    def reset_password(self, email: str, new_password: str) -> bool:
        """重置密码"""
        # 查找用户
        user = self.user_repo.get_by_email(email)
        if not user:
            return False
        # 更新密码
        user.password_hash = self.get_password_hash(new_password)
        self.user_repo.update(user)
        return True


class AuthSettingDomainService:
    """认证设置领域服务"""
    
    def __init__(self, repository: AuthSettingRepository):
        self.repository = repository
    
    def create_auth_setting(self, setting: AuthSettingModel) -> AuthSettingModel:
        """创建认证设置"""
        # 检查功能键是否已存在
        existing_setting = self.repository.get_by_feature_key(setting.feature_key)
        if existing_setting:
            raise ValueError(f"功能键 {setting.feature_key} 已存在")
        return self.repository.create(setting)
    
    def get_by_id(self, setting_id: str) -> Optional[AuthSettingModel]:
        """根据 ID 获取认证设置"""
        return self.repository.get_by_id(setting_id)
    
    def get_by_feature_key(self, feature_key: str) -> Optional[AuthSettingModel]:
        """根据功能键获取认证设置"""
        return self.repository.get_by_feature_key(feature_key)
    
    def get_enabled_features(self, feature_type: str) -> List[AuthSettingModel]:
        """获取指定类型的启用功能列表"""
        return self.repository.get_enabled_by_feature_type(feature_type)
    
    def get_all_features(self, feature_type: str) -> List[AuthSettingModel]:
        """获取指定类型的所有功能列表"""
        return self.repository.get_by_feature_type(feature_type)
    
    def is_feature_enabled(self, feature_key: str) -> bool:
        """检查功能是否启用"""
        setting = self.repository.get_by_feature_key(feature_key)
        return setting.enabled if setting else False
    
    def toggle_enabled(self, setting_id: str) -> AuthSettingModel:
        """切换启用状态"""
        setting = self.repository.get_by_id(setting_id)
        if not setting:
            raise ValueError(f"认证设置不存在，ID: {setting_id}")
        setting.enabled = not setting.enabled
        return self.repository.update(setting)
    
    def update_auth_setting(self, setting: AuthSettingModel) -> AuthSettingModel:
        """更新认证设置"""
        existing_setting = self.repository.get_by_id(setting.id)
        if not existing_setting:
            raise ValueError(f"认证设置不存在，ID: {setting.id}")
        # 检查功能键是否被其他设置使用
        if setting.feature_key != existing_setting.feature_key:
            other_setting = self.repository.get_by_feature_key(setting.feature_key)
            if other_setting and other_setting.id != setting.id:
                raise ValueError(f"功能键 {setting.feature_key} 已被其他设置使用")
        return self.repository.update(setting)
    
    def delete_auth_setting(self, setting_id: str) -> bool:
        """删除认证设置"""
        return self.repository.delete(setting_id)
    
    def list_all(self, skip: int = 0, limit: int = 100) -> List[AuthSettingModel]:
        """列出所有认证设置"""
        return self.repository.list(skip, limit)
    
    def get_feature_to_provider_mapping(self) -> dict:
        """获取功能键到提供商的映射"""
        return {
            AuthFeatureKey.GITHUB_LOGIN: SsoProvider.GITHUB,
            AuthFeatureKey.COMMUNITY_LOGIN: SsoProvider.COMMUNITY
        }
