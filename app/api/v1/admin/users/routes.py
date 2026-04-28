from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.application.admin.admin_user_app_service import AdminUserAppService
from app.domain.admin.repository import SQLAlchemyAdminUserRepository
from app.domain.admin.service import AdminPermissionService
from app.domain.admin.model.schemas import AdminUserDTO, AdminUserCreateRequest, AdminUserUpdateRequest

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin_users"])

# 依赖注入
def get_admin_user_app_service(db: Session = Depends(get_db)) -> AdminUserAppService:
    admin_repository = SQLAlchemyAdminUserRepository(db)
    permission_service = AdminPermissionService(admin_repository)
    return AdminUserAppService(admin_repository, permission_service)

@router.post("", response_model=AdminUserDTO)
def create_admin(admin_config: AdminUserCreateRequest, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    创建管理员
    """
    try:
        # 临时使用 admin_id=1 作为操作员，实际应该从请求头获取
        return admin_user_app_service.create_admin(admin_config, operator_admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("", response_model=dict)
def get_admin_list(role: str = None, page: int = 1, size: int = 20, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    获取管理员列表
    """
    try:
        return admin_user_app_service.list_admins(role_filter=role, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{admin_id}", response_model=AdminUserDTO)
def get_admin(admin_id: int, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    获取管理员详情
    """
    try:
        return admin_user_app_service.get_admin(admin_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{admin_id}/role", response_model=AdminUserDTO)
def update_admin_role(admin_id: int, role_data: dict, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    更新管理员角色
    """
    try:
        # 临时使用 admin_id=1 作为操作员，实际应该从请求头获取
        return admin_user_app_service.update_admin_role(admin_id, role_data.get("role"), operator_admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{admin_id}/permissions")
def update_admin_permissions(admin_id: int, permissions_data: dict, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    更新管理员权限
    """
    try:
        # 临时使用 admin_id=1 作为操作员，实际应该从请求头获取
        admin_user_app_service.update_admin_permissions(admin_id, permissions_data.get("permissions"), operator_admin_id=1)
        return {"message": "权限更新成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{admin_id}/deactivate")
def deactivate_admin(admin_id: int, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    停用管理员
    """
    try:
        # 临时使用 admin_id=1 作为操作员，实际应该从请求头获取
        admin_user_app_service.deactivate_admin(admin_id, operator_admin_id=1)
        return {"message": "管理员已停用"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{admin_id}")
def delete_admin(admin_id: int, admin_user_app_service: AdminUserAppService = Depends(get_admin_user_app_service)):
    """
    删除管理员
    """
    try:
        # 临时使用 admin_id=1 作为操作员，实际应该从请求头获取
        admin_user_app_service._admin_repository.delete(admin_id)
        return {"message": "管理员已删除"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
