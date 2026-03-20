from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
from sqlalchemy.orm import Session
from app.domain.user.model import UserModel, UserSettingsModel

class UserRepository(ABC):
    """用户仓储接口"""
    
    @abstractmethod
    def create(self, user: UserModel) -> UserModel:
        """创建用户"""
        pass
    
    @abstractmethod
    def get_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """根据 ID 获取用户"""
        pass
    
    @abstractmethod
    def get_by_email(self, email: str) -> Optional[UserModel]:
        """根据邮箱获取用户"""
        pass
    
    @abstractmethod
    def get_by_github_id(self, github_id: str) -> Optional[UserModel]:
        """根据 GitHub ID 获取用户"""
        pass
    
    @abstractmethod
    def get_by_google_id(self, google_id: str) -> Optional[UserModel]:
        """根据 Google ID 获取用户"""
        pass
    
    @abstractmethod
    def update(self, user: UserModel) -> UserModel:
        """更新用户"""
        pass
    
    @abstractmethod
    def delete(self, user_id: uuid.UUID) -> bool:
        """删除用户"""
        pass
    
    @abstractmethod
    def list(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        """列出用户"""
        pass

class UserSettingsRepository(ABC):
    """用户设置仓储接口"""
    
    @abstractmethod
    def create(self, settings: UserSettingsModel) -> UserSettingsModel:
        """创建用户设置"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSettingsModel]:
        """根据用户 ID 获取设置"""
        pass
    
    @abstractmethod
    def update(self, settings: UserSettingsModel) -> UserSettingsModel:
        """更新用户设置"""
        pass
    
    @abstractmethod
    def delete(self, settings_id: uuid.UUID) -> bool:
        """删除用户设置"""
        pass

class SQLAlchemyUserRepository(UserRepository):
    """SQLAlchemy 用户仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, user: UserModel) -> UserModel:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def get_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.email == email).first()
    
    def get_by_github_id(self, github_id: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.github_id == github_id).first()
    
    def get_by_google_id(self, google_id: str) -> Optional[UserModel]:
        return self.db.query(UserModel).filter(UserModel.google_id == google_id).first()
    
    def update(self, user: UserModel) -> UserModel:
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def delete(self, user_id: uuid.UUID) -> bool:
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False
    
    def list(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        return self.db.query(UserModel).offset(skip).limit(limit).all()

class SQLAlchemyUserSettingsRepository(UserSettingsRepository):
    """SQLAlchemy 用户设置仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, settings: UserSettingsModel) -> UserSettingsModel:
        self.db.add(settings)
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSettingsModel]:
        return self.db.query(UserSettingsModel).filter(UserSettingsModel.user_id == user_id).first()
    
    def update(self, settings: UserSettingsModel) -> UserSettingsModel:
        self.db.commit()
        self.db.refresh(settings)
        return settings
    
    def delete(self, settings_id: uuid.UUID) -> bool:
        settings = self.db.query(UserSettingsModel).filter(UserSettingsModel.id == settings_id).first()
        if settings:
            self.db.delete(settings)
            self.db.commit()
            return True
        return False
