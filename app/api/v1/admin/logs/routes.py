from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.application.admin.audit_log_app_service import AuditLogAppService
from app.domain.admin.service import AuditLogService
from app.domain.admin.repository import SQLAlchemyAuditLogRepository

router = APIRouter(prefix="/api/v1/admin/logs", tags=["admin_audit_logs"])

# 依赖注入
def get_audit_log_app_service(db: Session = Depends(get_db)) -> AuditLogAppService:
    audit_log_repository = SQLAlchemyAuditLogRepository(db)
    audit_log_service = AuditLogService(audit_log_repository)
    return AuditLogAppService(audit_log_service)

@router.get("")
def get_audit_logs(admin_id: int = None, action_type: str = None, resource_type: str = None, page: int = 1, size: int = 20, audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    获取审计日志列表
    """
    try:
        if admin_id:
            return audit_log_app_service.get_admin_logs(admin_id, page=page, size=size)
        else:
            # 临时返回空列表，实际应该实现全量查询
            return {"items": [], "total": 0, "page": page, "size": size, "pages": 0}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/resource/{resource_type}/{resource_id}")
def get_resource_logs(resource_type: str, resource_id: str, page: int = 1, size: int = 20, audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    获取资源操作日志
    """
    try:
        return audit_log_app_service.get_resource_logs(resource_type, resource_id, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/timerange")
def get_logs_by_timerange(start_time: str, end_time: str, page: int = 1, size: int = 20, audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    按时间范围查询日志
    """
    try:
        # 临时使用空实现，实际应该解析时间字符串
        return audit_log_app_service.get_logs_by_timerange(start_time, end_time, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/search")
def search_logs(keyword: str, page: int = 1, size: int = 20, audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    搜索日志
    """
    try:
        return audit_log_app_service.search_logs(keyword, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/export")
def export_logs(format: str, filters: dict = None, audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    导出日志
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        data = audit_log_app_service.export_logs(format, filters or {}, admin_id=1)
        return {"data": data.decode() if isinstance(data, bytes) else data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/action-types")
def get_action_types(audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    获取操作类型列表
    """
    try:
        return audit_log_app_service.get_action_types()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/resource-types")
def get_resource_types(audit_log_app_service: AuditLogAppService = Depends(get_audit_log_app_service)):
    """
    获取资源类型列表
    """
    try:
        return audit_log_app_service.get_resource_types()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
