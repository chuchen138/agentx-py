from abc import ABC, abstractmethod
from typing import Optional, List
import uuid
import json
from sqlalchemy.orm import Session
from app.domain.user.model import UserModel, UserSettingsModel
from app.core.redis import get_redis

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


class RedisUserRepository(UserRepository):
    """Redis 用户仓储实现"""
    
    def __init__(self):
        self.redis = get_redis()
        self.user_key_prefix = "user:"
        self.email_index_key = "user:email:"
    
    def _user_to_dict(self, user: UserModel) -> dict:
        """将用户模型转换为字典"""
        from datetime import datetime
        created_at = user.created_at if user.created_at else datetime.utcnow()
        updated_at = user.updated_at if user.updated_at else datetime.utcnow()
        return {
            "id": str(user.id),
            "email": user.email,
            "nickname": user.nickname,
            "password_hash": user.password_hash,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "github_id": user.github_id,
            "github_login": user.github_login,
            "google_id": user.google_id,
            "login_platform": user.login_platform,
            "is_admin": user.is_admin,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "created_at": str(created_at),
            "updated_at": str(updated_at)
        }
    
    def _dict_to_user(self, user_dict: dict) -> UserModel:
        """将字典转换为用户模型"""
        user = UserModel(
            id=uuid.UUID(user_dict.get("id", str(uuid.uuid4()))),
            email=user_dict.get("email", ""),
            nickname=user_dict.get("nickname", ""),
            password_hash=user_dict.get("password_hash", ""),
            phone=user_dict.get("phone"),
            avatar_url=user_dict.get("avatar_url"),
            github_id=user_dict.get("github_id"),
            github_login=user_dict.get("github_login"),
            google_id=user_dict.get("google_id"),
            login_platform=user_dict.get("login_platform"),
            is_admin=user_dict.get("is_admin", False),
            is_active=user_dict.get("is_active", True),
            is_superuser=user_dict.get("is_superuser", False)
        )
        # 设置created_at和updated_at
        from datetime import datetime
        try:
            # 确保值不是 None 或 "None"
            created_at_value = user_dict.get("created_at")
            updated_at_value = user_dict.get("updated_at")
            
            # 处理 created_at
            if created_at_value and created_at_value != "None":
                try:
                    user.created_at = datetime.fromisoformat(created_at_value)
                except:
                    user.created_at = datetime.utcnow()
            else:
                user.created_at = datetime.utcnow()
            
            # 处理 updated_at
            if updated_at_value and updated_at_value != "None":
                try:
                    user.updated_at = datetime.fromisoformat(updated_at_value)
                except:
                    user.updated_at = datetime.utcnow()
            else:
                user.updated_at = datetime.utcnow()
        except Exception:
            # 如果解析失败，使用当前时间
            user.created_at = datetime.utcnow()
            user.updated_at = datetime.utcnow()
        return user
    
    def create(self, user: UserModel) -> UserModel:
        # 保存用户数据
        user_key = f"{self.user_key_prefix}{user.id}"
        user_dict = self._user_to_dict(user)
        self.redis.set(user_key, json.dumps(user_dict))
        
        # 创建邮箱索引
        self.redis.set(f"{self.email_index_key}{user.email}", str(user.id))
        
        return user
    
    def get_by_id(self, user_id: uuid.UUID) -> Optional[UserModel]:
        user_key = f"{self.user_key_prefix}{user_id}"
        user_data = self.redis.get(user_key)
        if not user_data:
            return None
        user_dict = json.loads(user_data)
        return self._dict_to_user(user_dict)
    
    def get_by_email(self, email: str) -> Optional[UserModel]:
        user_id = self.redis.get(f"{self.email_index_key}{email}")
        if not user_id:
            return None
        return self.get_by_id(uuid.UUID(user_id))
    
    def get_by_github_id(self, github_id: str) -> Optional[UserModel]:
        # 简化实现，实际应用中应该添加github_id索引
        all_users = self.list()
        for user in all_users:
            if user.github_id == github_id:
                return user
        return None
    
    def get_by_google_id(self, google_id: str) -> Optional[UserModel]:
        # 简化实现，实际应用中应该添加google_id索引
        all_users = self.list()
        for user in all_users:
            if user.google_id == google_id:
                return user
        return None
    
    def update(self, user: UserModel) -> UserModel:
        user_key = f"{self.user_key_prefix}{user.id}"
        user_dict = self._user_to_dict(user)
        self.redis.set(user_key, json.dumps(user_dict))
        return user
    
    def delete(self, user_id: uuid.UUID) -> bool:
        user = self.get_by_id(user_id)
        if not user:
            return False
        
        # 删除用户数据
        user_key = f"{self.user_key_prefix}{user_id}"
        self.redis.delete(user_key)
        
        # 删除邮箱索引
        self.redis.delete(f"{self.email_index_key}{user.email}")
        
        return True
    
    def list(self, skip: int = 0, limit: int = 100) -> List[UserModel]:
        users = []
        try:
            keys = self.redis.keys(f"{self.user_key_prefix}*")
            for key in keys[skip:skip+limit]:
                user_data = self.redis.get(key)
                if user_data:
                    try:
                        user_dict = json.loads(user_data)
                        users.append(self._dict_to_user(user_dict))
                    except json.JSONDecodeError:
                        # 跳过无效的JSON数据
                        continue
        except Exception:
            # 忽略Redis连接错误，返回空列表
            pass
        return users


class RedisUserSettingsRepository(UserSettingsRepository):
    """Redis 用户设置仓储实现"""
    
    def __init__(self):
        self.redis = get_redis()
        self.settings_key_prefix = "user:settings:"
        self.user_settings_index = "user:settings:user_id:"
    
    def _settings_to_dict(self, settings: UserSettingsModel) -> dict:
        """将用户设置模型转换为字典"""
        from datetime import datetime
        created_at = settings.created_at if settings.created_at else datetime.utcnow()
        updated_at = settings.updated_at if settings.updated_at else datetime.utcnow()
        return {
            "id": str(settings.id),
            "user_id": str(settings.user_id),
            "setting_config": settings.setting_config,
            "created_at": str(created_at),
            "updated_at": str(updated_at)
        }
    
    def _dict_to_settings(self, settings_dict: dict) -> UserSettingsModel:
        """将字典转换为用户设置模型"""
        settings = UserSettingsModel(
            id=uuid.UUID(settings_dict["id"]),
            user_id=uuid.UUID(settings_dict["user_id"]),
            setting_config=settings_dict["setting_config"]
        )
        # 设置created_at和updated_at
        from datetime import datetime
        try:
            settings.created_at = datetime.fromisoformat(settings_dict["created_at"]) if settings_dict["created_at"] not in [None, "None"] else datetime.utcnow()
            settings.updated_at = datetime.fromisoformat(settings_dict["updated_at"]) if settings_dict["updated_at"] not in [None, "None"] else datetime.utcnow()
        except Exception:
            # 如果解析失败，使用当前时间
            settings.created_at = datetime.utcnow()
            settings.updated_at = datetime.utcnow()
        return settings
    
    def create(self, settings: UserSettingsModel) -> UserSettingsModel:
        settings_key = f"{self.settings_key_prefix}{settings.id}"
        settings_dict = self._settings_to_dict(settings)
        self.redis.set(settings_key, json.dumps(settings_dict))
        
        # 创建用户ID索引
        self.redis.set(f"{self.user_settings_index}{settings.user_id}", str(settings.id))
        
        return settings
    
    def get_by_user_id(self, user_id: uuid.UUID) -> Optional[UserSettingsModel]:
        settings_id = self.redis.get(f"{self.user_settings_index}{user_id}")
        if not settings_id:
            return None
        settings_key = f"{self.settings_key_prefix}{settings_id}"
        settings_data = self.redis.get(settings_key)
        if not settings_data:
            return None
        settings_dict = json.loads(settings_data)
        return self._dict_to_settings(settings_dict)
    
    def update(self, settings: UserSettingsModel) -> UserSettingsModel:
        settings_key = f"{self.settings_key_prefix}{settings.id}"
        settings_dict = self._settings_to_dict(settings)
        self.redis.set(settings_key, json.dumps(settings_dict))
        return settings
    
    def delete(self, settings_id: uuid.UUID) -> bool:
        # 先获取设置，以便删除用户ID索引
        settings_key = f"{self.settings_key_prefix}{settings_id}"
        settings_data = self.redis.get(settings_key)
        if settings_data:
            settings_dict = json.loads(settings_data)
            user_id = settings_dict["user_id"]
            # 删除用户ID索引
            self.redis.delete(f"{self.user_settings_index}{user_id}")
        
        # 删除设置数据
        return bool(self.redis.delete(settings_key))
