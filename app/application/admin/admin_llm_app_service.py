from typing import List, Optional
from app.domain.admin.service import AdminLLMService, AuditLogService, InsufficientPermissionException
from app.domain.admin.model.schemas import AuditLogDTO

class AdminLLMAppService:
    def __init__(self, llm_service: AdminLLMService, audit_log_service: AuditLogService):
        self._llm_service = llm_service
        self._audit_log_service = audit_log_service
    
    def create_official_provider(self, provider_config: dict, admin_id: int) -> dict:
        """
        创建官方服务商
        """
        # 创建官方服务商
        provider = self._llm_service.create_official_provider(admin_id, provider_config)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="CREATE_OFFICIAL_PROVIDER",
            resource_type="LLM_PROVIDER",
            resource_id=provider['id'],
            details=f"创建官方服务商: {provider['name']}",
            ip_address=""
        )
        
        return provider
    
    def update_official_provider(self, provider_id: str, provider_config: dict, admin_id: int) -> dict:
        """
        更新官方服务商
        """
        # 更新官方服务商
        provider = self._llm_service.update_official_provider(admin_id, provider_id, provider_config)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="UPDATE_OFFICIAL_PROVIDER",
            resource_type="LLM_PROVIDER",
            resource_id=provider_id,
            details=f"更新官方服务商: {provider['name']}",
            ip_address=""
        )
        
        return provider
    
    def delete_official_provider(self, provider_id: str, admin_id: int):
        """
        删除官方服务商
        """
        # 删除官方服务商
        self._llm_service.delete_official_provider(admin_id, provider_id)
        
        # 记录审计日志
        self._audit_log_service.log_action(
            admin_user_id=admin_id,
            action_type="DELETE_OFFICIAL_PROVIDER",
            resource_type="LLM_PROVIDER",
            resource_id=provider_id,
            details="删除官方服务商",
            ip_address=""
        )
    
    def list_official_providers(self, filters: dict, page: int, size: int) -> dict:
        """
        查询官方服务商列表
        """
        # 查询官方服务商
        providers = self._llm_service.list_official_providers(filters)
        
        # 手动分页
        start = (page - 1) * size
        end = start + size
        paginated_providers = providers[start:end]
        total = len(providers)
        
        return {
            "items": paginated_providers,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def get_provider(self, provider_id: str) -> dict:
        """
        获取服务商详情
        """
        # TODO: 实现获取服务商详情逻辑
        pass
    
    def get_provider_audit_logs(self, provider_id: str, page: int, size: int) -> dict:
        """
        获取服务商操作日志
        """
        # 查询操作日志
        logs = self._audit_log_service.get_resource_logs("LLM_PROVIDER", provider_id)
        
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
