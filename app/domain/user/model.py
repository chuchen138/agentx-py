from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, JSON, TypeDecorator
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional, List
import uuid
from datetime import datetime

# 自定义UUID类型，兼容SQLite
class UUID(TypeDecorator):
    impl = String
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        elif isinstance(value, uuid.UUID):
            return str(value)
        else:
            return value
    
    def process_result_value(self, value, dialect):
        if value is None:
            return None
        else:
            return uuid.UUID(value)

# 基础模型基类
from app.core.database import Base

# SQLAlchemy ORM 模型
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String(255), nullable=False, unique=True, index=True)
    nickname = Column(String(100), nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    github_id = Column(String(100), nullable=True, unique=True)
    github_login = Column(String(100), nullable=True)
    google_id = Column(String(100), nullable=True, unique=True)
    login_platform = Column(String(20), nullable=False, default="normal")
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    is_superuser = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    settings = relationship("UserSettingsModel", back_populates="user", uselist=False, cascade="all, delete-orphan")

class UserSettingsModel(Base):
    __tablename__ = "user_settings"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    setting_config = Column(JSON, nullable=False, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关系
    user = relationship("UserModel", back_populates="settings")

# Pydantic 数据模型
class FallbackConfig(BaseModel):
    enabled: bool = Field(default=False, description="是否启用降级")
    fallback_chain: List[str] = Field(default_factory=list, description="降级模型 ID 列表（按优先级排序）")
    max_retries: int = Field(default=3, description="最大重试次数")

class UserSettingsConfig(BaseModel):
    default_model: Optional[str] = Field(None, description="默认聊天模型 ID")
    default_ocr_model: Optional[str] = Field(None, description="默认 OCR 模型 ID")
    default_embedding_model: Optional[str] = Field(None, description="默认嵌入模型 ID")
    fallback_config: Optional[FallbackConfig] = Field(None, description="降级配置")
    theme: str = Field(default="light", description="界面主题")
    language: str = Field(default="zh-CN", description="语言设置")

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., min_length=8, description="密码")
    nickname: str = Field(..., min_length=2, max_length=100, description="用户昵称")
    phone: Optional[str] = Field(None, description="手机号")

class UserUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=2, max_length=100, description="用户昵称")
    phone: Optional[str] = Field(None, description="手机号")
    avatar_url: Optional[str] = Field(None, description="头像 URL")

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    nickname: str
    phone: Optional[str]
    avatar_url: Optional[str]
    github_id: Optional[str]
    github_login: Optional[str]
    google_id: Optional[str]
    login_platform: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class UserSettingsCreate(BaseModel):
    setting_config: UserSettingsConfig = Field(default_factory=UserSettingsConfig)

class UserSettingsUpdate(BaseModel):
    setting_config: Optional[UserSettingsConfig] = Field(None)

class UserSettingsResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    setting_config: UserSettingsConfig
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="用户邮箱")
    password: str = Field(..., description="密码")

class PasswordChange(BaseModel):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=8, description="新密码")
