from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.domain.auth.model import AuthSettingModel


class AuthSettingRepository(ABC):
    """认证设置仓储接口"""
    
    @abstractmethod
    def create(self, auth_setting: AuthSettingModel) -> AuthSettingModel:
        """创建认证设置"""
        pass
    
    @abstractmethod
    def get_by_id(self, setting_id: str) -> Optional[AuthSettingModel]:
        """根据 ID 获取认证设置"""
        pass
    
    @abstractmethod
    def get_by_feature_key(self, feature_key: str) -> Optional[AuthSettingModel]:
        """根据功能键获取认证设置"""
        pass
    
    @abstractmethod
    def get_by_feature_type(self, feature_type: str) -> List[AuthSettingModel]:
        """根据功能类型获取认证设置"""
        pass
    
    @abstractmethod
    def get_enabled_by_feature_type(self, feature_type: str) -> List[AuthSettingModel]:
        """根据功能类型获取启用的认证设置"""
        pass
    
    @abstractmethod
    def update(self, auth_setting: AuthSettingModel) -> AuthSettingModel:
        """更新认证设置"""
        pass
    
    @abstractmethod
    def delete(self, setting_id: str) -> bool:
        """删除认证设置"""
        pass
    
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[AuthSettingModel]:
        """列出所有认证设置"""
        pass


class SQLAlchemyAuthSettingRepository(AuthSettingRepository):
    """SQLAlchemy 认证设置仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, auth_setting: AuthSettingModel) -> AuthSettingModel:
        self.db.add(auth_setting)
        self.db.commit()
        self.db.refresh(auth_setting)
        return auth_setting
    
    def get_by_id(self, setting_id: str) -> Optional[AuthSettingModel]:
        return self.db.query(AuthSettingModel).filter(AuthSettingModel.id == setting_id).first()
    
    def get_by_feature_key(self, feature_key: str) -> Optional[AuthSettingModel]:
        return self.db.query(AuthSettingModel).filter(AuthSettingModel.feature_key == feature_key).first()
    
    def get_by_feature_type(self, feature_type: str) -> List[AuthSettingModel]:
        return self.db.query(AuthSettingModel).filter(AuthSettingModel.feature_type == feature_type).order_by(AuthSettingModel.display_order).all()
    
    def get_enabled_by_feature_type(self, feature_type: str) -> List[AuthSettingModel]:
        return self.db.query(AuthSettingModel).filter(
            AuthSettingModel.feature_type == feature_type,
            AuthSettingModel.enabled == True
        ).order_by(AuthSettingModel.display_order).all()
    
    def update(self, auth_setting: AuthSettingModel) -> AuthSettingModel:
        self.db.commit()
        self.db.refresh(auth_setting)
        return auth_setting
    
    def delete(self, setting_id: str) -> bool:
        setting = self.get_by_id(setting_id)
        if setting:
            self.db.delete(setting)
            self.db.commit()
            return True
        return False
    
    def list(self, skip: int = 0, limit: int = 100) -> List[AuthSettingModel]:
        return self.db.query(AuthSettingModel).offset(skip).limit(limit).all()
