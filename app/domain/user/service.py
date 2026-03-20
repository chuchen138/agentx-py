from typing import Optional
import uuid
import random
import os
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.domain.user.model import UserModel, UserSettingsModel, UserSettingsConfig
from app.domain.user.repository import UserRepository, UserSettingsRepository
from app.domain.auth.model import VerificationCode
from sqlalchemy.orm import Session

# 密码加密上下文
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

class UserDomainService:
    """用户领域服务"""
    
    def __init__(self, user_repo: UserRepository, settings_repo: UserSettingsRepository, db: Session):
        self.user_repo = user_repo
        self.settings_repo = settings_repo
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """获取密码哈希"""
        # 截断密码，确保不超过 bcrypt 的 72 字节限制
        password = password[:72]
        return pwd_context.hash(password)
    
    def create_user(self, email: str, password: str, nickname: str, phone: Optional[str] = None) -> UserModel:
        """创建用户"""
        # 检查邮箱是否已存在
        existing_user = self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("邮箱已被注册")
        
        # 创建用户
        user = UserModel(
            id=uuid.uuid4(),
            email=email,
            password_hash=self.get_password_hash(password),
            nickname=nickname,
            phone=phone,
            login_platform="normal",
            is_admin=False
        )
        
        # 保存用户
        user = self.user_repo.create(user)
        
        # 创建默认用户设置
        default_settings = UserSettingsModel(
            id=uuid.uuid4(),
            user_id=user.id,
            setting_config=UserSettingsConfig().model_dump()
        )
        self.settings_repo.create(default_settings)
        
        return user
    
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
    
    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """根据 ID 获取用户"""
        return self.user_repo.get_by_id(user_id)
    
    def update_user(self, user: UserModel) -> UserModel:
        """更新用户"""
        return self.user_repo.update(user)
    
    def delete_user(self, user_id: uuid.UUID) -> bool:
        """删除用户"""
        return self.user_repo.delete(user_id)
    
    def generate_verification_code(self) -> str:
        """生成6位数字验证码"""
        return ''.join(random.choices('0123456789', k=6))
    
    def store_verification_code(self, email: str, code: str) -> None:
        """存储验证码到 PostgreSQL"""
        # 先删除该邮箱的旧验证码
        existing_codes = self.db.query(VerificationCode).filter(
            VerificationCode.email == email,
            VerificationCode.is_used == False
        ).all()
        for existing_code in existing_codes:
            existing_code.is_used = True
            self.db.add(existing_code)
        
        # 创建新验证码，10分钟有效期
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        verification_code = VerificationCode(
            email=email,
            code=code,
            expires_at=expires_at
        )
        self.db.add(verification_code)
        self.db.commit()
    
    def verify_verification_code(self, email: str, code: str) -> bool:
        """验证验证码"""
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
        
        # 标记验证码为已使用
        verification_code.is_used = True
        verification_code.used_at = now
        self.db.add(verification_code)
        self.db.commit()
        
        return True
    
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

class UserSettingsDomainService:
    """用户设置领域服务"""
    
    def __init__(self, settings_repo: UserSettingsRepository):
        self.settings_repo = settings_repo
    
    def get_user_settings(self, user_id: uuid.UUID) -> Optional[UserSettingsModel]:
        """获取用户设置"""
        return self.settings_repo.get_by_user_id(user_id)
    
    def update_user_settings(self, user_id: uuid.UUID, settings_config: UserSettingsConfig) -> UserSettingsModel:
        """更新用户设置"""
        settings = self.settings_repo.get_by_user_id(user_id)
        if not settings:
            # 创建新设置
            settings = UserSettingsModel(
                id=uuid.uuid4(),
                user_id=user_id,
                setting_config=settings_config.model_dump()
            )
            return self.settings_repo.create(settings)
        
        # 更新现有设置
        settings.setting_config = settings_config.model_dump()
        return self.settings_repo.update(settings)
    
    def reset_user_settings(self, user_id: uuid.UUID) -> UserSettingsModel:
        """重置用户设置"""
        default_config = UserSettingsConfig()
        return self.update_user_settings(user_id, default_config)
