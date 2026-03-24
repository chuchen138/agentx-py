from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.core.models.llm_preference import UserModelPreference


class UserModelPreferenceRepository:
    """用户模型偏好设置仓库"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_user_id(self, user_id: str) -> Optional[UserModelPreference]:
        """根据用户ID获取偏好设置"""
        stmt = select(UserModelPreference).where(UserModelPreference.user_id == user_id)
        result = self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    def create_or_update(self, user_id: str, provider_id: str, model_id: str) -> UserModelPreference:
        """创建或更新用户偏好设置"""
        # 先尝试获取现有设置
        existing = self.get_by_user_id(user_id)
        
        if existing:
            # 更新现有设置
            existing.provider_id = provider_id
            existing.model_id = model_id
            self.session.add(existing)
            self.session.commit()
            self.session.refresh(existing)
            return existing
        else:
            # 创建新设置
            import uuid
            new_preference = UserModelPreference(
                id=str(uuid.uuid4()),
                user_id=user_id,
                provider_id=provider_id,
                model_id=model_id
            )
            self.session.add(new_preference)
            self.session.commit()
            self.session.refresh(new_preference)
            return new_preference
    
    def delete(self, user_id: str) -> None:
        """删除用户偏好设置"""
        stmt = delete(UserModelPreference).where(UserModelPreference.user_id == user_id)
        self.session.execute(stmt)
        self.session.commit()
