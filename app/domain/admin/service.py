from typing import Set, List, Optional
import json
from app.domain.admin.repository import AdminUserRepository
from app.domain.admin.constant.admin_role import AdminRole, AdminPermission, ROLE_PERMISSIONS, ROLE_HIERARCHY
from app.core.redis import redis_client

class AdminPermissionService:
    def __init__(self, admin_repository: AdminUserRepository):
        self._admin_repository = admin_repository
        self._cache_ttl = 300  # 5分钟缓存
    
    def verify_admin_role(self, admin_id: int, required_role: AdminRole) -> bool:
        """
        验证管理员角色
        """
        admin = self._admin_repository.get_by_id(admin_id)
        if not admin:
            return False
        
        # 检查角色层级
        admin_role = AdminRole(admin.role)
        if admin_role == required_role:
            return True
        
        # 检查角色继承关系
        return self._check_role_hierarchy(admin_role, required_role)
    
    def verify_permission(self, admin_id: int, permission: AdminPermission) -> bool:
        """
        验证具体权限
        """
        # 先尝试从缓存获取权限
        permissions = self._get_cached_permissions(admin_id)
        if permissions:
            return permission in permissions
        
        # 从数据库获取权限
        permissions = self.get_admin_permissions(admin_id)
        return permission in permissions
    
    def has_any_permission(self, admin_id: int, permissions: List[AdminPermission]) -> bool:
        """
        验证是否拥有任一权限
        """
        admin_permissions = self.get_admin_permissions(admin_id)
        return any(perm in admin_permissions for perm in permissions)
    
    def has_all_permissions(self, admin_id: int, permissions: List[AdminPermission]) -> bool:
        """
        验证是否拥有所有权限
        """
        admin_permissions = self.get_admin_permissions(admin_id)
        return all(perm in admin_permissions for perm in permissions)
    
    def get_admin_permissions(self, admin_id: int) -> Set[AdminPermission]:
        """
        获取管理员所有权限
        """
        # 先尝试从缓存获取
        cached_permissions = self._get_cached_permissions(admin_id)
        if cached_permissions:
            return cached_permissions
        
        # 从数据库获取
        admin = self._admin_repository.get_by_id(admin_id)
        if not admin:
            return set()
        
        # 获取角色权限
        admin_role = AdminRole(admin.role)
        permissions = set(ROLE_PERMISSIONS.get(admin_role, set()))
        
        # 添加继承的权限
        for inherited_role in ROLE_HIERARCHY.get(admin_role, []):
            permissions.update(ROLE_PERMISSIONS.get(inherited_role, set()))
        
        # 添加自定义权限（如果有）
        if admin.permissions:
            try:
                custom_perms = json.loads(admin.permissions)
                for perm in custom_perms:
                    try:
                        permissions.add(AdminPermission(perm))
                    except ValueError:
                        pass
            except json.JSONDecodeError:
                pass
        
        # 缓存权限
        self._cache_permissions(admin_id, permissions)
        
        return permissions
    
    def _check_role_hierarchy(self, admin_role: AdminRole, required_role: AdminRole) -> bool:
        """
        检查角色层级关系
        """
        if admin_role == required_role:
            return True
        
        # 检查继承关系
        for role in ROLE_HIERARCHY.get(admin_role, []):
            if role == required_role or self._check_role_hierarchy(role, required_role):
                return True
        
        return False
    
    def _get_cached_permissions(self, admin_id: int) -> Optional[Set[AdminPermission]]:
        """
        从缓存获取权限
        """
        try:
            key = f"admin:permissions:{admin_id}"
            cached_data = redis_client.get(key)
            if cached_data:
                perm_strings = json.loads(cached_data)
                return {AdminPermission(perm) for perm in perm_strings}
        except Exception:
            pass
        return None
    
    def _cache_permissions(self, admin_id: int, permissions: Set[AdminPermission]):
        """
        缓存权限
        """
        try:
            key = f"admin:permissions:{admin_id}"
            perm_strings = [perm.value for perm in permissions]
            redis_client.set(key, json.dumps(perm_strings))
        except Exception:
            pass
    
    def refresh_permission_cache(self, admin_id: int):
        """
        刷新权限缓存
        """
        try:
            key = f"admin:permissions:{admin_id}"
            redis_client.delete(key)
        except Exception:
            pass

class AdminLLMService:
    def __init__(self, provider_repository, permission_service: AdminPermissionService):
        self._provider_repository = provider_repository
        self._permission_service = permission_service
    
    def create_official_provider(self, admin_id: int, provider_config) -> dict:
        """
        创建官方服务商
        """
        # 验证权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.CREATE_OFFICIAL_PROVIDER):
            raise InsufficientPermissionException("权限不足，无法创建官方服务商")
        
        # 设置为官方服务商
        provider_config['is_official'] = True
        
        # 加密存储 API Key
        # TODO: 实现 API Key 加密逻辑
        
        # 记录创建日志
        # TODO: 实现日志记录
        
        # 创建服务商
        return self._provider_repository.create(provider_config)
    
    def update_official_provider(self, admin_id: int, provider_id: str, provider_config) -> dict:
        """
        更新官方服务商
        """
        # 验证权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.MODIFY_OFFICIAL_PROVIDER):
            raise InsufficientPermissionException("权限不足，无法更新官方服务商")
        
        # 支持密钥掩码处理
        # TODO: 实现密钥掩码处理逻辑
        
        # 记录更新日志
        # TODO: 实现日志记录
        
        # 更新服务商
        return self._provider_repository.update(provider_id, provider_config)
    
    def set_admin_level(self, provider_id: str, admin_level):
        """
        设置管理员级别
        """
        # TODO: 实现设置管理员级别逻辑
        pass
    
    def delete_official_provider(self, admin_id: int, provider_id: str):
        """
        删除官方服务商
        """
        # 验证权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.DELETE_OFFICIAL_PROVIDER):
            raise InsufficientPermissionException("权限不足，无法删除官方服务商")
        
        # 软删除或标记为禁用
        # TODO: 实现删除逻辑
        
        # 记录删除日志
        # TODO: 实现日志记录
        pass
    
    def list_official_providers(self, filters) -> List[dict]:
        """
        查询所有官方服务商
        """
        # 只查询官方服务商
        filters['is_official'] = True
        return self._provider_repository.find_all(filters)

class AdminToolService:
    def __init__(self, tool_repository, audit_repository, permission_service: AdminPermissionService):
        self._tool_repository = tool_repository
        self._audit_repository = audit_repository
        self._permission_service = permission_service
    
    def submit_tool_for_audit(self, user_id: int, tool_data) -> dict:
        """
        创建工具审核申请
        """
        # 创建审核记录
        audit_record = {
            'tool_id': tool_data['tool_id'],
            'applicant_user_id': user_id,
            'audit_status': 'PENDING',
            'submitted_data': json.dumps(tool_data)
        }
        return self._audit_repository.create_audit_record(audit_record)
    
    def start_review(self, admin_id: int, record_id: str) -> dict:
        """
        开始审核
        """
        # 验证审核权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.AUDIT_TOOL):
            raise InsufficientPermissionException("权限不足，无法审核工具")
        
        # 设置状态为 IN_REVIEW
        # TODO: 实现状态更新逻辑
        pass
    
    def approve_audit(self, admin_id: int, record_id: str, comment: str) -> dict:
        """
        审核通过
        """
        # 验证审核权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.AUDIT_TOOL):
            raise InsufficientPermissionException("权限不足，无法审核工具")
        
        # 设置状态为 APPROVED
        # 标记工具为官方工具
        # 发布工具
        # 记录审核通过日志
        # TODO: 实现审核通过逻辑
        pass
    
    def reject_audit(self, admin_id: int, record_id: str, comment: str) -> dict:
        """
        审核拒绝
        """
        # 验证审核权限
        if not self._permission_service.verify_permission(admin_id, AdminPermission.AUDIT_TOOL):
            raise InsufficientPermissionException("权限不足，无法审核工具")
        
        # 设置状态为 REJECTED
        # 提供审核意见
        # 通知申请人
        # TODO: 实现审核拒绝逻辑
        pass
    
    def cancel_audit(self, user_id: int, record_id: str):
        """
        取消待审核的申请
        """
        # 设置状态为 CANCELLED
        # TODO: 实现取消审核逻辑
        pass
    
    def get_pending_audits(self) -> List[dict]:
        """
        获取所有待审核工具
        """
        return self._audit_repository.get_pending_audits()
    
    def get_audit_history(self, tool_id: str) -> List[dict]:
        """
        获取工具审核历史
        """
        return self._audit_repository.get_audit_history(tool_id)

class AuditLogService:
    def __init__(self, log_repository):
        self._log_repository = log_repository
    
    def log_action(self, admin_user_id: int, action_type: str, resource_type: str, resource_id: str, details: str, ip_address: str):
        """
        记录操作日志
        """
        # 生成 log_id
        # 计算 prev_log_hash
        # 异步写入数据库
        # TODO: 实现日志记录逻辑
        pass
    
    def get_admin_logs(self, admin_id: int, page: int, size: int) -> dict:
        """
        查询管理员操作日志
        """
        return self._log_repository.get_by_admin_user_id(admin_id, page, size)
    
    def get_resource_logs(self, resource_type: str, resource_id: str) -> List[dict]:
        """
        查询资源操作历史
        """
        return self._log_repository.get_by_resource(resource_type, resource_id)
    
    def get_logs_by_timerange(self, start_time, end_time, page: int, size: int) -> dict:
        """
        按时间范围查询日志
        """
        return self._log_repository.get_by_time_range(start_time, end_time)
    
    def search_logs(self, keyword: str, page: int, size: int) -> dict:
        """
        搜索日志
        """
        return self._log_repository.search_logs(keyword, page, size)
    
    def export_logs(self, format: str, filters) -> bytes:
        """
        导出日志为 CSV/Excel
        """
        # TODO: 实现日志导出逻辑
        pass

# 异常类
class InsufficientPermissionException(Exception):
    pass

class AdminUserNotFoundException(Exception):
    pass

class InvalidAuditStateException(Exception):
    pass

class AuditAlreadyCompletedException(Exception):
    pass

class SecretKeyMaskInvalidException(Exception):
    pass

class ResourceNotFoundException(Exception):
    pass
