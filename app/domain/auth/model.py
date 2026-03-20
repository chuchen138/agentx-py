from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, JSON
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from app.core.database import Base


class VerificationCode(Base):
    """验证码模型"""
    __tablename__ = "verification_codes"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, index=True)
    code = Column(String(6), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, default=False)
    used_at = Column(DateTime(timezone=True), nullable=True)


class AuthSettingModel(Base):
    """认证设置模型"""
    __tablename__ = "auth_settings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    feature_type = Column(String(32), nullable=False, index=True)
    feature_key = Column(String(64), nullable=False, unique=True, index=True)
    feature_name = Column(String(128), nullable=False)
    enabled = Column(Boolean, nullable=False, default=False)
    config_data = Column(JSON, nullable=True, default={})
    display_order = Column(Integer, nullable=True, default=0)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __init__(self, **kwargs):
        # 设置默认值
        kwargs.setdefault('enabled', False)
        kwargs.setdefault('config_data', {})
        kwargs.setdefault('display_order', 0)
        super().__init__(**kwargs)


# Pydantic 数据模型
class AuthSettingBase(BaseModel):
    feature_type: str
    feature_key: str
    feature_name: str
    enabled: bool = False
    config_data: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = 0
    description: Optional[str] = None


class AuthSettingCreate(AuthSettingBase):
    pass


class AuthSettingUpdate(BaseModel):
    feature_name: Optional[str] = None
    enabled: Optional[bool] = None
    config_data: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = None
    description: Optional[str] = None


class AuthSettingResponse(BaseModel):
    id: str
    feature_type: str
    feature_key: str
    feature_name: str
    enabled: bool
    config_data: Optional[Dict[str, Any]] = None
    display_order: Optional[int] = 0
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }


class LoginMethodDTO(BaseModel):
    """登录方式 DTO"""
    enabled: bool
    name: str
    provider: Optional[str] = None


class AuthConfigDTO(BaseModel):
    """前端认证配置响应 DTO"""
    loginMethods: Dict[str, LoginMethodDTO]
    registerEnabled: bool
