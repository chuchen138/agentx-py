from typing import List, Optional
from app.domain.admin.service import AuditLogService
from app.domain.admin.model.schemas import AuditLogDTO

class AuditLogAppService:
    def __init__(self, audit_log_service: AuditLogService):
        self._audit_log_service = audit_log_service
    
    def get_admin_logs(self, admin_id: int, page: int, size: int) -> dict:
        """
        查询管理员操作日志
        """
        # 查询日志
        result = self._audit_log_service.get_admin_logs(admin_id, page, size)
        
        # 转换为 DTO
        log_dtos = [
            AuditLogDTO(
                id=log.id,
                log_id=log.log_id,
                admin_user_id=log.admin_user_id,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action_details=log.action_details,
                ip_address=log.ip_address,
                created_at=log.created_at,
                prev_log_hash=log.prev_log_hash
            )
            for log in result.items
        ]
        
        return {
            "items": log_dtos,
            "total": result.total,
            "page": result.page,
            "size": result.size,
            "pages": result.pages
        }
    
    def get_resource_logs(self, resource_type: str, resource_id: str, page: int, size: int) -> dict:
        """
        查询资源操作日志
        """
        # 查询日志
        logs = self._audit_log_service.get_resource_logs(resource_type, resource_id)
        
        # 手动分页
        start = (page - 1) * size
        end = start + size
        paginated_logs = logs[start:end]
        total = len(logs)
        
        # 转换为 DTO
        log_dtos = [
            AuditLogDTO(
                id=log.id,
                log_id=log.log_id,
                admin_user_id=log.admin_user_id,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action_details=log.action_details,
                ip_address=log.ip_address,
                created_at=log.created_at,
                prev_log_hash=log.prev_log_hash
            )
            for log in paginated_logs
        ]
        
        return {
            "items": log_dtos,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_logs_by_timerange(self, start_time, end_time, page: int, size: int) -> dict:
        """
        按时间范围查询日志
        """
        # 查询日志
        logs = self._audit_log_service.get_logs_by_timerange(start_time, end_time, page, size)
        
        # 转换为 DTO
        log_dtos = [
            AuditLogDTO(
                id=log.id,
                log_id=log.log_id,
                admin_user_id=log.admin_user_id,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action_details=log.action_details,
                ip_address=log.ip_address,
                created_at=log.created_at,
                prev_log_hash=log.prev_log_hash
            )
            for log in logs.items
        ]
        
        return {
            "items": log_dtos,
            "total": logs.total,
            "page": logs.page,
            "size": logs.size,
            "pages": logs.pages
        }
    
    def search_logs(self, keyword: str, page: int, size: int) -> dict:
        """
        搜索日志
        """
        # 搜索日志
        result = self._audit_log_service.search_logs(keyword, page, size)
        
        # 转换为 DTO
        log_dtos = [
            AuditLogDTO(
                id=log.id,
                log_id=log.log_id,
                admin_user_id=log.admin_user_id,
                action_type=log.action_type,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                action_details=log.action_details,
                ip_address=log.ip_address,
                created_at=log.created_at,
                prev_log_hash=log.prev_log_hash
            )
            for log in result.items
        ]
        
        return {
            "items": log_dtos,
            "total": result.total,
            "page": result.page,
            "size": result.size,
            "pages": result.pages
        }
    
    def export_logs(self, format: str, filters: dict, admin_id: int) -> bytes:
        """
        导出审计日志
        """
        # 导出日志
        return self._audit_log_service.export_logs(format, filters)
    
    def get_action_types(self) -> List[str]:
        """
        获取所有操作类型
        """
        # TODO: 实现获取操作类型列表逻辑
        return [
            "CREATE_OFFICIAL_PROVIDER",
            "UPDATE_OFFICIAL_PROVIDER",
            "DELETE_OFFICIAL_PROVIDER",
            "START_TOOL_AUDIT",
            "APPROVE_TOOL_AUDIT",
            "REJECT_TOOL_AUDIT",
            "CREATE_ADMIN",
            "UPDATE_ADMIN",
            "DELETE_ADMIN"
        ]
    
    def get_resource_types(self) -> List[str]:
        """
        获取所有资源类型
        """
        # TODO: 实现获取资源类型列表逻辑
        return [
            "LLM_PROVIDER",
            "TOOL",
            "ADMIN_USER",
            "AUDIT_LOG"
        ]
