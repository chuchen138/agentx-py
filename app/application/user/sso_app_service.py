from typing import Optional, Dict, Any
import uuid
import os
from app.domain.user.model import UserModel
from app.domain.user.service import UserDomainService
from app.domain.user.repository import UserRepository

class SsoProvider:
    """SSO 提供者抽象接口"""
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        """获取授权 URL"""
        pass
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        """处理回调并获取用户信息"""
        pass

class GitHubSsoProvider(SsoProvider):
    """GitHub SSO 提供者"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        # 使用真实的GitHub OAuth授权URL
        # 注意：需要在GitHub开发者设置中注册应用并获取client_id
        # 回调地址需要在GitHub应用设置中配置为：http://localhost:8000/api/v1/auth/sso/github/callback
        return f"https://github.com/login/oauth/authorize?client_id={self.client_id}&redirect_uri=http://localhost:8000/api/v1/auth/sso/github/callback&scope=user:email&state=mock_state"
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        # 简化实现，返回模拟用户信息
        return {
            'id': '123456',
            'login': 'testuser',
            'email': 'test@example.com',
            'name': 'Test User',
            'avatar_url': 'https://example.com/avatar.jpg'
        }

class GoogleSsoProvider(SsoProvider):
    """Google SSO 提供者"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
    
    def get_authorization_url(self, redirect_uri: str) -> str:
        # 使用真实的Google OAuth授权URL
        # 注意：需要在Google开发者控制台中注册应用并获取client_id
        # 回调地址需要在Google应用设置中配置为：http://localhost:8000/api/v1/auth/sso/google/callback
        return f"https://accounts.google.com/o/oauth2/auth?client_id={self.client_id}&redirect_uri=http://localhost:8000/api/v1/auth/sso/google/callback&scope=openid%20email%20profile&response_type=code&state=mock_state"
    
    def handle_callback(self, code: str, state: str) -> Dict[str, Any]:
        # 简化实现，返回模拟用户信息
        return {
            'id': '123456789',
            'email': 'test@example.com',
            'name': 'Test User',
            'avatar_url': 'https://example.com/avatar.jpg'
        }

class SsoAppService:
    """SSO 应用服务"""
    
    def __init__(self, user_domain_service: UserDomainService, user_repo: UserRepository):
        self.user_domain_service = user_domain_service
        self.user_repo = user_repo
        # 初始化 SSO 提供者
        self.providers = {
            'github': GitHubSsoProvider(
                client_id=os.getenv('GITHUB_CLIENT_ID', 'your-github-client-id'),
                client_secret=os.getenv('GITHUB_CLIENT_SECRET', 'your-github-client-secret')
            ),
            'google': GoogleSsoProvider(
                client_id=os.getenv('GOOGLE_CLIENT_ID', 'your-google-client-id'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')
            )
        }
    
    def get_sso_authorization_url(self, provider: str, redirect_uri: str) -> str:
        """生成 SSO 授权 URL"""
        if provider not in self.providers:
            raise ValueError(f"不支持的 SSO 提供商: {provider}")
        return self.providers[provider].get_authorization_url(redirect_uri)
    
    def handle_sso_callback(self, provider: str, code: str, state: str) -> Dict[str, Any]:
        """处理 SSO 回调"""
        if provider not in self.providers:
            raise ValueError(f"不支持的 SSO 提供商: {provider}")
        
        # 获取用户信息
        user_info = self.providers[provider].handle_callback(code, state)
        
        # 创建或关联用户
        user = self.create_or_link_user(provider, user_info)
        
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
            "expires_in": 15 * 60
        }
    
    def create_or_link_user(self, provider: str, user_info: Dict[str, Any]) -> UserModel:
        """创建新用户或关联现有用户"""
        # 先根据 provider_id 查找
        provider_id = user_info.get('id')
        if provider == 'github':
            existing_user = self.user_repo.get_by_github_id(provider_id)
        elif provider == 'google':
            existing_user = self.user_repo.get_by_google_id(provider_id)
        else:
            existing_user = None
        
        # 如果找到现有用户，更新信息
        if existing_user:
            existing_user.nickname = user_info.get('name', existing_user.nickname)
            existing_user.avatar_url = user_info.get('avatar_url', existing_user.avatar_url)
            return self.user_domain_service.update_user(existing_user)
        
        # 否则，根据邮箱查找
        email = user_info.get('email')
        if email:
            existing_user = self.user_repo.get_by_email(email)
            if existing_user:
                # 关联到现有用户
                if provider == 'github':
                    existing_user.github_id = provider_id
                    existing_user.github_login = user_info.get('login')
                elif provider == 'google':
                    existing_user.google_id = provider_id
                existing_user.nickname = user_info.get('name', existing_user.nickname)
                existing_user.avatar_url = user_info.get('avatar_url', existing_user.avatar_url)
                return self.user_domain_service.update_user(existing_user)
        
        # 创建新用户
        nickname = user_info.get('name', user_info.get('login', f"{provider}_user"))
        user = UserModel(
            id=uuid.uuid4(),
            email=email or f"{provider}_{provider_id}@example.com",
            password_hash=self.user_domain_service.get_password_hash(str(uuid.uuid4())),  # 生成随机密码
            nickname=nickname,
            avatar_url=user_info.get('avatar_url'),
            github_id=provider_id if provider == 'github' else None,
            github_login=user_info.get('login') if provider == 'github' else None,
            google_id=provider_id if provider == 'google' else None,
            login_platform=provider,
            is_admin=False
        )
        
        # 保存用户
        user = self.user_repo.create(user)
        
        # 创建默认用户设置
        from app.domain.user.model import UserSettingsModel, UserSettingsConfig
        
        # 直接创建 UserSettingsModel 并添加到数据库
        # 这里假设 user_repo 有一个 db 属性可以访问数据库会话
        default_settings = UserSettingsModel(
            id=uuid.uuid4(),
            user_id=user.id,
            setting_config=UserSettingsConfig().model_dump()
        )
        self.user_repo.db.add(default_settings)
        self.user_repo.db.commit()
        
        return user
    
    def verify_sso_token(self, token: str) -> Optional[Dict[str, Any]]:
        """验证 SSO Token"""
        # 简化实现，实际应用中需要根据不同提供商验证
        return self.user_domain_service.verify_token(token)
