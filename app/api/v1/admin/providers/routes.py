from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.application.admin.admin_llm_app_service import AdminLLMAppService
from app.domain.admin.service import AdminLLMService, AuditLogService
from app.domain.admin.repository import SQLAlchemyAuditLogRepository

router = APIRouter(prefix="/api/v1/admin/providers", tags=["admin_providers"])

# 依赖注入
def get_admin_llm_app_service(db: Session = Depends(get_db)) -> AdminLLMAppService:
    # 临时使用空实现，实际应该注入真实的 provider_repository
    provider_repository = None
    from app.domain.admin.repository import SQLAlchemyAdminUserRepository
    from app.domain.admin.service import AdminPermissionService
    admin_repository = SQLAlchemyAdminUserRepository(db)
    permission_service = AdminPermissionService(admin_repository)
    llm_service = AdminLLMService(provider_repository, permission_service)
    audit_log_repository = SQLAlchemyAuditLogRepository(db)
    audit_log_service = AuditLogService(audit_log_repository)
    return AdminLLMAppService(llm_service, audit_log_service)

@router.post("")
def create_official_provider(provider_config: dict, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    创建官方服务商
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_llm_app_service.create_official_provider(provider_config, admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("")
def get_official_providers(type: str = None, status: str = None, page: int = 1, size: int = 20, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    获取官方服务商列表
    """
    try:
        filters = {}
        if type:
            filters['type'] = type
        if status:
            filters['status'] = status
        return admin_llm_app_service.list_official_providers(filters, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{provider_id}")
def get_provider(provider_id: str, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    获取服务商详情
    """
    try:
        return admin_llm_app_service.get_provider(provider_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{provider_id}")
def update_official_provider(provider_id: str, provider_config: dict, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    更新官方服务商
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_llm_app_service.update_official_provider(provider_id, provider_config, admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{provider_id}")
def delete_official_provider(provider_id: str, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    删除官方服务商
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        admin_llm_app_service.delete_official_provider(provider_id, admin_id=1)
        return {"message": "服务商已删除"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{provider_id}/logs")
def get_provider_audit_logs(provider_id: str, page: int = 1, size: int = 20, admin_llm_app_service: AdminLLMAppService = Depends(get_admin_llm_app_service)):
    """
    获取操作日志
    """
    try:
        return admin_llm_app_service.get_provider_audit_logs(provider_id, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
