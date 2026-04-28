from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.core.database import get_db
from app.application.admin.admin_tool_app_service import AdminToolAppService
from app.domain.admin.service import AdminToolService, AuditLogService
from app.domain.admin.repository import SQLAlchemyToolAuditRecordRepository, SQLAlchemyAuditLogRepository

router = APIRouter(prefix="/api/v1/admin/tools/audit", tags=["admin_tool_audit"])

# 依赖注入
def get_admin_tool_app_service(db: Session = Depends(get_db)) -> AdminToolAppService:
    # 临时使用空实现，实际应该注入真实的 tool_repository
    tool_repository = None
    audit_repository = SQLAlchemyToolAuditRecordRepository(db)
    from app.domain.admin.repository import SQLAlchemyAdminUserRepository
    from app.domain.admin.service import AdminPermissionService
    admin_repository = SQLAlchemyAdminUserRepository(db)
    permission_service = AdminPermissionService(admin_repository)
    tool_service = AdminToolService(tool_repository, audit_repository, permission_service)
    audit_log_repository = SQLAlchemyAuditLogRepository(db)
    audit_log_service = AuditLogService(audit_log_repository)
    return AdminToolAppService(tool_service, audit_log_service)

@router.post("")
def submit_tool_for_audit(tool_data: dict, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    提交工具审核申请
    """
    try:
        # 临时使用 user_id=1，实际应该从请求头获取
        return admin_tool_app_service.submit_tool_for_audit(tool_data, user_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/pending")
def get_pending_audits(page: int = 1, size: int = 20, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    获取待审核列表
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_tool_app_service.get_pending_audits(admin_id=1, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/records")
def get_audit_records(status: str = None, page: int = 1, size: int = 20, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    获取审核记录列表
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_tool_app_service.get_audit_records(admin_id=1, page=page, size=size)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{record_id}")
def get_audit_record(record_id: str, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    获取审核记录详情
    """
    try:
        return admin_tool_app_service.get_audit_record(record_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{record_id}/start")
def start_review(record_id: str, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    开始审核
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_tool_app_service.start_review(record_id, admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{record_id}/approve")
def approve_audit(record_id: str, comment_data: dict, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    审核通过
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_tool_app_service.approve_audit(record_id, comment_data.get("comment"), admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{record_id}/reject")
def reject_audit(record_id: str, comment_data: dict, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    审核拒绝
    """
    try:
        # 临时使用 admin_id=1，实际应该从请求头获取
        return admin_tool_app_service.reject_audit(record_id, comment_data.get("comment"), admin_id=1)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{record_id}/cancel")
def cancel_audit(record_id: str, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    取消审核
    """
    try:
        # 临时使用 user_id=1，实际应该从请求头获取
        admin_tool_app_service.cancel_audit(record_id, user_id=1)
        return {"message": "审核已取消"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tool/{tool_id}/history")
def get_audit_history(tool_id: str, admin_tool_app_service: AdminToolAppService = Depends(get_admin_tool_app_service)):
    """
    获取审核历史
    """
    try:
        return admin_tool_app_service.get_audit_history(tool_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
