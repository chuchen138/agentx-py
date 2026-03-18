from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from app.domain.user.repository import RedisUserRepository, RedisUserSettingsRepository
from app.domain.user.service import UserDomainService
import uuid

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """获取当前用户"""
    token = credentials.credentials
    
    # 验证令牌
    user_repo = RedisUserRepository()
    settings_repo = RedisUserSettingsRepository()
    user_domain_service = UserDomainService(user_repo, settings_repo)
    
    payload = user_domain_service.verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 获取用户
    user_id = uuid.UUID(payload.get("sub"))
    user = user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def optional_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """可选认证依赖"""
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None
