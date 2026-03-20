from fastapi import APIRouter, Depends, HTTPException, status
from app.api.middleware.auth import get_current_user
from app.domain.user.model import UserModel, UserUpdate, UserResponse, UserSettingsResponse, UserSettingsConfig
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
from app.domain.user.service import UserDomainService, UserSettingsDomainService
from app.application.user.user_app_service import UserAppService
from app.application.user.user_settings_app_service import UserSettingsAppService
from app.core.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = APIRouter()

# 依赖项
def get_user_app_service(db: Session = Depends(get_db)):
    user_repo = SQLAlchemyUserRepository(db)
    settings_repo = SQLAlchemyUserSettingsRepository(db)
    user_domain_service = UserDomainService(user_repo, settings_repo, db)
    return UserAppService(user_domain_service)

def get_user_settings_app_service(db: Session = Depends(get_db)):
    settings_repo = SQLAlchemyUserSettingsRepository(db)
    settings_domain_service = UserSettingsDomainService(settings_repo)
    return UserSettingsAppService(settings_domain_service)

# 请求/响应模型
class UpdateUserRequest(BaseModel):
    nickname: str = None
    phone: str = None
    avatar_url: str = None

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str

class UpdateUserSettingsRequest(BaseModel):
    default_model: str = None
    default_ocr_model: str = None
    default_embedding_model: str = None
    fallback_config: dict = None
    theme: str = None
    language: str = None

# 路由
@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: UserModel = Depends(get_current_user)
):
    """获取当前用户信息"""
    return current_user

@router.put("/me", response_model=UserResponse)
def update_current_user(
    request: UpdateUserRequest,
    current_user: UserModel = Depends(get_current_user),
    user_app_service: UserAppService = Depends(get_user_app_service)
):
    """更新当前用户信息"""
    user_update = UserUpdate(
        nickname=request.nickname,
        phone=request.phone,
        avatar_url=request.avatar_url
    )
    return user_app_service.update_user_profile(current_user.id, user_update)

@router.delete("/me")
def delete_current_user(
    current_user: UserModel = Depends(get_current_user),
    user_app_service: UserAppService = Depends(get_user_app_service)
):
    """删除当前用户账号"""
    user_app_service.delete_user(current_user.id)
    return {"message": "用户删除成功"}

@router.post("/me/change-password")
def change_password(
    request: ChangePasswordRequest,
    current_user: UserModel = Depends(get_current_user),
    user_app_service: UserAppService = Depends(get_user_app_service)
):
    """修改密码"""
    if request.new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致"
        )
    
    try:
        user_app_service.change_password(
            current_user.id,
            request.current_password,
            request.new_password
        )
        return {"message": "密码修改成功"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me/settings", response_model=UserSettingsResponse)
def get_user_settings(
    current_user: UserModel = Depends(get_current_user),
    settings_app_service: UserSettingsAppService = Depends(get_user_settings_app_service)
):
    """获取用户设置"""
    settings = settings_app_service.get_user_settings(current_user.id)
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户设置不存在"
        )
    return settings

@router.put("/me/settings", response_model=UserSettingsResponse)
def update_user_settings(
    request: UpdateUserSettingsRequest,
    current_user: UserModel = Depends(get_current_user),
    settings_app_service: UserSettingsAppService = Depends(get_user_settings_app_service)
):
    """更新用户设置"""
    # 构建设置配置
    settings_config = UserSettingsConfig(
        default_model=request.default_model,
        default_ocr_model=request.default_ocr_model,
        default_embedding_model=request.default_embedding_model,
        fallback_config=request.fallback_config,
        theme=request.theme,
        language=request.language
    )
    return settings_app_service.update_user_settings(current_user.id, settings_config)
