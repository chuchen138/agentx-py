from typing import Optional
import uuid
from app.domain.user.model import UserModel, UserUpdate
from app.domain.user.service import UserDomainService

class UserAppService:
    """用户应用服务"""
    
    def __init__(self, user_domain_service: UserDomainService):
        self.user_domain_service = user_domain_service
    
    def get_current_user(self, user_id: uuid.UUID) -> Optional[UserModel]:
        """获取当前登录用户信息"""
        return self.user_domain_service.get_user_by_id(user_id)
    
    def update_user_profile(self, user_id: uuid.UUID, update_data: UserUpdate) -> UserModel:
        """更新用户基本信息"""
        user = self.user_domain_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 更新用户信息
        if update_data.nickname:
            user.nickname = update_data.nickname
        if update_data.phone:
            user.phone = update_data.phone
        if update_data.avatar_url:
            user.avatar_url = update_data.avatar_url
        
        return self.user_domain_service.update_user(user)
    
    def delete_user(self, user_id: uuid.UUID) -> bool:
        """删除用户账号"""
        return self.user_domain_service.delete_user(user_id)
    
    def change_password(self, user_id: uuid.UUID, current_password: str, new_password: str) -> bool:
        """修改密码"""
        user = self.user_domain_service.get_user_by_id(user_id)
        if not user:
            raise ValueError("用户不存在")
        
        # 验证当前密码
        if not self.user_domain_service.verify_password(current_password, user.password_hash):
            raise ValueError("当前密码错误")
        
        # 更新密码
        user.password_hash = self.user_domain_service.get_password_hash(new_password)
        self.user_domain_service.update_user(user)
        return True
    
    def validate_user(self, user_id: uuid.UUID) -> bool:
        """验证用户状态"""
        user = self.user_domain_service.get_user_by_id(user_id)
        return user is not None
