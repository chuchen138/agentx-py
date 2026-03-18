from typing import Optional, Dict, Any
import uuid
from app.domain.user.model import UserModel, UserCreate
from app.domain.user.service import UserDomainService

class LoginAppService:
    """登录应用服务"""
    
    def __init__(self, user_domain_service: UserDomainService):
        self.user_domain_service = user_domain_service
    
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
        user = self.user_domain_service.authenticate_user(email, password)
        if not user:
            return None
        
        # 生成令牌
        access_token = self.user_domain_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        refresh_token = self.user_domain_service.create_refresh_token(
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
        payload = self.user_domain_service.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            return None
        
        # 获取用户
        user_id = uuid.UUID(payload.get("sub"))
        user = self.user_domain_service.get_user_by_id(user_id)
        if not user:
            return None
        
        # 生成新的访问令牌
        new_access_token = self.user_domain_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        new_refresh_token = self.user_domain_service.create_refresh_token(
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
        user = self.user_domain_service.authenticate_user(email, password)
        return user is not None
    
    def send_verification_code(self, email: str) -> bool:
        """发送验证码"""
        # 检查用户是否存在
        user = self.user_domain_service.user_repo.get_by_email(email)
        if not user:
            return False
        # 生成验证码
        code = self.user_domain_service.generate_verification_code()
        # 存储验证码到 Redis
        self.user_domain_service.store_verification_code(email, code)
        # 这里应该发送邮件，暂时打印验证码
        print(f"验证码: {code} 已发送到邮箱: {email}")
        return True
    
    def verify_code(self, email: str, code: str) -> bool:
        """验证验证码"""
        return self.user_domain_service.verify_verification_code(email, code)
    
    def reset_password(self, email: str, new_password: str) -> bool:
        """重置密码"""
        return self.user_domain_service.reset_password(email, new_password)
