import pytest
from unittest.mock import Mock, MagicMock
from app.domain.admin.service import AdminPermissionService
from app.domain.admin.constant.admin_role import AdminRole, AdminPermission

@pytest.fixture
def permission_service():
    # 创建 mock 管理员仓库
    mock_admin_repo = Mock()
    # 模拟 get_by_id 方法返回 None
    mock_admin_repo.get_by_id.return_value = None
    return AdminPermissionService(mock_admin_repo)

def test_admin_permission_service(permission_service):
    """
    测试管理员权限服务
    """
    # 测试验证角色
    assert permission_service.verify_admin_role(1, AdminRole.AUDITOR) is False
    
    # 测试验证权限
    assert permission_service.verify_permission(1, AdminPermission.AUDIT_TOOL) is False

def test_admin_role_hierarchy():
    """
    测试角色层级关系
    """
    from app.domain.admin.constant.admin_role import ROLE_HIERARCHY
    assert AdminRole.ADMIN in ROLE_HIERARCHY[AdminRole.SUPER_ADMIN]
    assert AdminRole.AUDITOR in ROLE_HIERARCHY[AdminRole.ADMIN]

def test_audit_status_transition():
    """
    测试审核状态转换
    """
    from app.domain.admin.constant.audit_status import AuditStatus, validate_status_transition
    assert validate_status_transition(AuditStatus.PENDING, AuditStatus.IN_REVIEW) is True
    assert validate_status_transition(AuditStatus.IN_REVIEW, AuditStatus.APPROVED) is True
    assert validate_status_transition(AuditStatus.APPROVED, AuditStatus.REJECTED) is False
