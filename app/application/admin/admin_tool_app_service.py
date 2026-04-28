from typing import List, Optional
from app.domain.admin.service import AdminToolService, AuditLogService, InsufficientPermissionException
from app.domain.admin.model.schemas import ToolAuditRecordDTO

class AdminToolAppService:
    def __init__(self, tool_service: AdminToolService, audit_log_service: AuditLogService):
        self._tool_service = tool_service
        self._audit_log_service = audit_log_service
    
    def submit_tool_for_audit(self, tool_data: dict, user_id: int) -> ToolAuditRecordDTO:
        """
        提交工具审核申请
        """
        # 提交审核申请
        audit_record = self._tool_service.submit_tool_for_audit(user_id, tool_data)
        
        return self._to_dto(audit_record)
    
    def start_review(self, record_id: str, admin_id: int) -> ToolAuditRecordDTO:
        """
        开始审核工具
        """
        # 开始审核
        audit_record = self._tool_service.start_review(admin_id, record_id)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="START_TOOL_AUDIT",
            resource_type="TOOL",
            resource_id=audit_record['tool_id'],
            details="开始审核工具",
            ip_address=""
        )
        
        return self._to_dto(audit_record)
    
    def approve_audit(self, record_id: str, comment: str, admin_id: int) -> ToolAuditRecordDTO:
        """
        审核通过
        """
        # 审核通过
        audit_record = self._tool_service.approve_audit(admin_id, record_id, comment)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="APPROVE_TOOL_AUDIT",
            resource_type="TOOL",
            resource_id=audit_record['tool_id'],
            details=f"审核通过工具: {comment}",
            ip_address=""
        )
        
        return self._to_dto(audit_record)
    
    def reject_audit(self, record_id: str, comment: str, admin_id: int) -> ToolAuditRecordDTO:
        """
        审核拒绝
        """
        # 审核拒绝
        audit_record = self._tool_service.reject_audit(admin_id, record_id, comment)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="REJECT_TOOL_AUDIT",
            resource_type="TOOL",
            resource_id=audit_record['tool_id'],
            details=f"审核拒绝工具: {comment}",
            ip_address=""
        )
        
        return self._to_dto(audit_record)
    
    def cancel_audit(self, record_id: str, user_id: int):
        """
        取消审核申请
        """
        # 取消审核
        self._tool_service.cancel_audit(user_id, record_id)
    
    def get_pending_audits(self, admin_id: int, page: int, size: int) -> dict:
        """
        获取待审核列表
        """
        # 获取待审核工具
        pending_audits = self._tool_service.get_pending_audits()
        
        # 手动分页
        start = (page - 1) * size
        end = start + size
        paginated_audits = pending_audits[start:end]
        total = len(pending_audits)
        
        # 转换为 DTO
        audit_dtos = [self._to_dto(audit) for audit in paginated_audits]
        
        return {
            "items": audit_dtos,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_audit_records(self, admin_id: int, page: int, size: int) -> dict:
        """
        获取审核历史记录
        """
        # TODO: 实现获取审核历史记录逻辑
        pass
    
    def get_audit_record(self, record_id: str) -> ToolAuditRecordDTO:
        """
        获取审核记录详情
        """
        # TODO: 实现获取审核记录详情逻辑
        pass
    
    def get_audit_history(self, tool_id: str) -> List[ToolAuditRecordDTO]:
        """
        获取工具审核历史
        """
        # 获取审核历史
        audit_history = self._tool_service.get_audit_history(tool_id)
        
        # 转换为 DTO
        return [self._to_dto(audit) for audit in audit_history]
    
    def _to_dto(self, audit_record) -> ToolAuditRecordDTO:
        """
        将实体转换为 DTO
        """
        return ToolAuditRecordDTO(
            id=audit_record.id,
            record_id=audit_record.record_id,
            tool_id=audit_record.tool_id,
            applicant_user_id=audit_record.applicant_user_id,
            auditor_admin_id=audit_record.auditor_admin_id,
            audit_status=audit_record.audit_status,
            audit_comment=audit_record.audit_comment,
            submitted_data=audit_record.submitted_data,
            audited_at=audit_record.audited_at,
            created_at=audit_record.created_at
        )
