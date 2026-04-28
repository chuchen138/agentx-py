from enum import Enum
from typing import Dict, Set

class AdminRole(Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"

class AdminPermission(Enum):
    CREATE_OFFICIAL_PROVIDER = "CREATE_OFFICIAL_PROVIDER"
    MODIFY_OFFICIAL_PROVIDER = "MODIFY_OFFICIAL_PROVIDER"
    DELETE_OFFICIAL_PROVIDER = "DELETE_OFFICIAL_PROVIDER"
    AUDIT_TOOL = "AUDIT_TOOL"
    MANAGE_OFFICIAL_TOOL = "MANAGE_OFFICIAL_TOOL"
    VIEW_AUDIT_LOGS = "VIEW_AUDIT_LOGS"
    MANAGE_ADMINS = "MANAGE_ADMINS"

# 角色权限映射
ROLE_PERMISSIONS: Dict[AdminRole, Set[AdminPermission]] = {
    AdminRole.SUPER_ADMIN: {
        AdminPermission.CREATE_OFFICIAL_PROVIDER,
        AdminPermission.MODIFY_OFFICIAL_PROVIDER,
        AdminPermission.DELETE_OFFICIAL_PROVIDER,
        AdminPermission.AUDIT_TOOL,
        AdminPermission.MANAGE_OFFICIAL_TOOL,
        AdminPermission.VIEW_AUDIT_LOGS,
        AdminPermission.MANAGE_ADMINS,
    },
    AdminRole.ADMIN: {
        AdminPermission.CREATE_OFFICIAL_PROVIDER,
        AdminPermission.MODIFY_OFFICIAL_PROVIDER,
        AdminPermission.DELETE_OFFICIAL_PROVIDER,
        AdminPermission.AUDIT_TOOL,
        AdminPermission.MANAGE_OFFICIAL_TOOL,
        AdminPermission.VIEW_AUDIT_LOGS,
    },
    AdminRole.AUDITOR: {
        AdminPermission.AUDIT_TOOL,
        AdminPermission.VIEW_AUDIT_LOGS,
    },
}

# 角色层级关系（用于权限继承）
ROLE_HIERARCHY = {
    AdminRole.SUPER_ADMIN: [AdminRole.ADMIN, AdminRole.AUDITOR],
    AdminRole.ADMIN: [AdminRole.AUDITOR],
    AdminRole.AUDITOR: [],
}
