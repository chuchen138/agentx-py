from typing import List, Optional
import json
from app.domain.admin.repository import AdminUserRepository
from app.domain.admin.service import AdminPermissionService, AdminUserNotFoundException, InsufficientPermissionException
from app.domain.admin.constant.admin_role import AdminRole
from app.domain.admin.model.schemas import AdminUserDTO, AdminUserCreateRequest, AdminUserUpdateRequest

class AdminUserAppService:
    def __init__(self, admin_repository: AdminUserRepository, permission_service: AdminPermissionService):
        self._admin_repository = admin_repository
        self._permission_service = permission_service
    
    def create_admin(self, admin_config: AdminUserCreateRequest, operator_admin_id: int) -> AdminUserDTO:
        """
        创建管理员账户
        """
        # 验证操作员权限
        if not self._permission_service.verify_admin_role(operator_admin_id, AdminRole.SUPER_ADMIN):
            raise InsufficientPermissionException("权限不足，无法创建管理员")
        
        # 检查用户是否已存在
        existing_admin = self._admin_repository.get_by_user_id(admin_config.user_id)
        if existing_admin:
            raise ValueError("该用户已存在管理员账户")
        
        # 创建管理员
        from app.domain.admin.model.admin_user import AdminUser
        admin = AdminUser(
            user_id=admin_config.user_id,
            username=admin_config.username,
            role=admin_config.role
        )
        
        created_admin = self._admin_repository.create(admin)
        return self._to_dto(created_admin)
    
    def update_admin_role(self, admin_id: int, new_role: str, operator_admin_id: int) -> AdminUserDTO:
        """
        更新管理员角色
        """
        # 验证操作员权限
        if not self._permission_service.verify_admin_role(operator_admin_id, AdminRole.SUPER_ADMIN):
            raise InsufficientPermissionException("权限不足，无法更新管理员角色")
        
        # 检查不能创建比自己级别高的管理员
        operator_admin = self._admin_repository.get_by_id(operator_admin_id)
        if not operator_admin:
            raise AdminUserNotFoundException("操作员管理员不存在")
        
        # 检查角色层级
        if new_role == AdminRole.SUPER_ADMIN.value and operator_admin.role != AdminRole.SUPER_ADMIN.value:
            raise InsufficientPermissionException("无法创建超级管理员")
        
        # 更新角色
        self._admin_repository.update_role(admin_id, new_role)
        
        # 刷新权限缓存
        self._permission_service.refresh_permission_cache(admin_id)
        
        # 返回更新后的管理员
        admin = self._admin_repository.get_by_id(admin_id)
        if not admin:
            raise AdminUserNotFoundException("管理员不存在")
        
        return self._to_dto(admin)
    
    def update_admin_permissions(self, admin_id: int, permissions: List[str], operator_admin_id: int):
        """
        更新管理员权限
        """
        # 验证操作员权限
        if not self._permission_service.verify_admin_role(operator_admin_id, AdminRole.SUPER_ADMIN):
            raise InsufficientPermissionException("权限不足，无法更新管理员权限")
        
        # 更新权限
        permissions_json = json.dumps(permissions)
        self._admin_repository.update_permissions(admin_id, permissions_json)
        
        # 刷新权限缓存
        self._permission_service.refresh_permission_cache(admin_id)
    
    def deactivate_admin(self, admin_id: int, operator_admin_id: int):
        """
        停用管理员账户
        """
        # 验证操作员权限
        if not self._permission_service.verify_admin_role(operator_admin_id, AdminRole.SUPER_ADMIN):
            raise InsufficientPermissionException("权限不足，无法停用管理员")
        
        # 不能停用自己
        if admin_id == operator_admin_id:
            raise ValueError("不能停用自己的账户")
        
        # 停用管理员
        self._admin_repository.deactivate(admin_id)
    
    def get_admin(self, admin_id: int) -> AdminUserDTO:
        """
        获取管理员详情
        """
        admin = self._admin_repository.get_by_id(admin_id)
        if not admin:
            raise AdminUserNotFoundException("管理员不存在")
        
        return self._to_dto(admin)
    
    def list_admins(self, role_filter: Optional[str], page: int, size: int) -> dict:
        """
        获取管理员列表
        """
        if role_filter:
            admins = self._admin_repository.get_admins_by_role(role_filter)
            # 手动分页
            start = (page - 1) * size
            end = start + size
            paginated_admins = admins[start:end]
            total = len(admins)
        else:
            result = self._admin_repository.get_all_admins(page, size)
            paginated_admins = result.items
            total = result.total
        
        # 转换为 DTO
        admin_dtos = [self._to_dto(admin) for admin in paginated_admins]
        
        return {
            "items": admin_dtos,
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    
    def check_admin_permission(self, admin_id: int, permission: str) -> bool:
        """
        检查管理员权限
        """
        from app.domain.admin.constant.admin_role import AdminPermission
        try:
            perm = AdminPermission(permission)
            return self._permission_service.verify_permission(admin_id, perm)
        except ValueError:
            return False
    
    def _to_dto(self, admin) -> AdminUserDTO:
        """
        将实体转换为 DTO
        """
        permissions = None
        if admin.permissions:
            try:
                permissions = json.loads(admin.permissions)
            except json.JSONDecodeError:
                permissions = []
        
        return AdminUserDTO(
            id=admin.id,
            user_id=admin.user_id,
            username=admin.username,
            role=admin.role,
            permissions=permissions,
            is_active=admin.is_active,
            created_at=admin.created_at,
            last_login_at=admin.last_login_at
        )
