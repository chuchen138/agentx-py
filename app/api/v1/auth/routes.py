from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from app.domain.user.model import UserCreate, UserResponse
from app.domain.user.repository import SQLAlchemyUserRepository, SQLAlchemyUserSettingsRepository
from app.domain.user.service import UserDomainService, UserSettingsDomainService
from app.application.user.sso_app_service import SsoAppService
from app.application.auth.auth_app_service import AuthAppService
from app.domain.auth.model import AuthSettingModel, AuthSettingResponse, AuthConfigDTO, AuthSettingUpdate, AuthSettingCreate
from app.domain.auth.service import AuthSettingDomainService
from app.domain.auth.constant import FeatureType, AuthFeatureKey
from app.domain.auth.repository import SQLAlchemyAuthSettingRepository
from app.core.database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
import uuid

router = APIRouter()

# 依赖项
def get_user_domain_service(db: Session = Depends(get_db)):
    user_repo = SQLAlchemyUserRepository(db)
    settings_repo = SQLAlchemyUserSettingsRepository(db)
    return UserDomainService(user_repo, settings_repo, db)

def get_auth_app_service(db: Session = Depends(get_db)):
    user_repo = SQLAlchemyUserRepository(db)
    settings_repo = SQLAlchemyUserSettingsRepository(db)
    return AuthAppService(user_repo, settings_repo, db)

def get_sso_app_service(user_domain_service: UserDomainService = Depends(get_user_domain_service), db: Session = Depends(get_db)):
    user_repo = SQLAlchemyUserRepository(db)
    return SsoAppService(user_domain_service, user_repo)

# 认证设置依赖项已合并到AuthAppService

# 请求/响应模型
class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(..., min_length=8, description="密码")
    nickname: str
    phone: str = None

class RegisterResponse(BaseModel):
    user_id: str
    email: str
    nickname: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int

class ForgotPasswordRequest(BaseModel):
    email: str

class ForgotPasswordResponse(BaseModel):
    message: str

class VerifyCodeRequest(BaseModel):
    email: str
    code: str

class VerifyCodeResponse(BaseModel):
    message: str

class ResetPasswordRequest(BaseModel):
    email: str
    code: str
    new_password: str = Field(..., min_length=8, description="新密码")

class ResetPasswordResponse(BaseModel):
    message: str

# 路由
@router.post("/register", response_model=RegisterResponse)
def register(
    request: RegisterRequest,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """用户注册"""
    try:
        user = auth_app_service.register(
            UserCreate(
                email=request.email,
                password=request.password,
                nickname=request.nickname,
                phone=request.phone
            )
        )
        return RegisterResponse(
            user_id=str(user.id),
            email=user.email,
            nickname=user.nickname
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """用户登录"""
    tokens = auth_app_service.login(request.email, request.password)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return LoginResponse(**tokens)

@router.post("/logout")
def logout(
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """用户登出"""
    auth_app_service.logout(None)  # 简化处理
    return {"message": "登出成功"}

@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token(
    request: RefreshTokenRequest,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """刷新 Token"""
    tokens = auth_app_service.refresh_token(request.refresh_token)
    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return RefreshTokenResponse(**tokens)

@router.get("/sso/{provider}/authorize")
def get_sso_authorization_url(
    provider: str,
    redirect_uri: str,
    sso_app_service: SsoAppService = Depends(get_sso_app_service)
):
    """SSO 授权入口"""
    try:
        auth_url = sso_app_service.get_sso_authorization_url(provider, redirect_uri)
        return {"authorize_url": auth_url}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/sso/{provider}/callback")
def handle_sso_callback(
    provider: str,
    code: str,
    state: str,
    sso_app_service: SsoAppService = Depends(get_sso_app_service)
):
    """SSO 回调"""
    try:
        tokens = sso_app_service.handle_sso_callback(provider, code, state)
        # 重定向到前端页面，附带token参数
        redirect_uri = "http://localhost:8080"
        query_params = "&".join([f"{k}={v}" for k, v in tokens.items()])
        return RedirectResponse(url=f"{redirect_uri}?{query_params}")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """找回密码"""
    try:
        success = auth_app_service.send_verification_code(request.email)
        if success:
            return ForgotPasswordResponse(message="验证码已发送到您的邮箱")
        else:
            # 邮箱不存在，返回错误信息
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱不存在"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败"
        )

@router.post("/verify-code", response_model=VerifyCodeResponse)
def verify_code(
        request: VerifyCodeRequest,
        auth_app_service: AuthAppService = Depends(get_auth_app_service)
    ):
        """验证验证码"""
        try:
            success = auth_app_service.verify_code(request.email, request.code, mark_as_used=False)
            if success:
                return VerifyCodeResponse(message="验证码验证成功")
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="验证码错误或已过期"
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="验证验证码失败"
            )

@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    request: ResetPasswordRequest,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """重置密码"""
    try:
        # 先验证验证码
        code_verified = auth_app_service.verify_code(request.email, request.code)
        if not code_verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证码错误或已过期"
            )
        # 重置密码
        success = auth_app_service.reset_password(request.email, request.new_password)
        if success:
            return ResetPasswordResponse(message="密码重置成功")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="重置密码失败"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="重置密码失败"
        )

# 认证设置路由
@router.get("/config", response_model=AuthConfigDTO)
def get_auth_config(
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """获取前端认证配置"""
    try:
        return auth_app_service.get_auth_config()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/settings", response_model=list[AuthSettingResponse])
def get_all_auth_settings(
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """获取所有认证配置"""
    try:
        return auth_app_service.get_all_auth_settings()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/settings/{setting_id}", response_model=AuthSettingResponse)
def get_auth_setting_by_id(
    setting_id: str,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """根据 ID 获取认证配置"""
    try:
        setting = auth_app_service.get_auth_setting_by_id(setting_id)
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"认证设置不存在，ID: {setting_id}"
            )
        return setting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/settings/{setting_id}/toggle", response_model=AuthSettingResponse)
def toggle_auth_setting(
    setting_id: str,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """切换认证配置启用状态"""
    try:
        return auth_app_service.toggle_auth_setting(setting_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.put("/settings/{setting_id}", response_model=AuthSettingResponse)
def update_auth_setting(
    setting_id: str,
    request: AuthSettingUpdate,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """更新认证配置"""
    try:
        return auth_app_service.update_auth_setting(setting_id, request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/settings/{setting_id}")
def delete_auth_setting(
    setting_id: str,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """删除认证配置"""
    try:
        success = auth_app_service.delete_auth_setting(setting_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"认证设置不存在，ID: {setting_id}"
            )
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/settings", response_model=AuthSettingResponse)
def create_auth_setting(
    request: AuthSettingCreate,
    auth_app_service: AuthAppService = Depends(get_auth_app_service)
):
    """创建认证配置"""
    try:
        setting = AuthSettingModel(
            feature_type=request.feature_type,
            feature_key=request.feature_key,
            feature_name=request.feature_name,
            enabled=request.enabled,
            config_data=request.config_data,
            display_order=request.display_order,
            description=request.description
        )
        return auth_app_service.create_auth_setting(setting)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
