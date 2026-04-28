from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.admin.repository import SQLAlchemyAdminUserRepository
from app.domain.admin.service import AdminPermissionService

security = HTTPBearer()

class AdminAuthMiddleware:
    def __init__(self):
        pass
    
    async def __call__(self, request: Request, call_next):
        # 跳过非管理后台路由
        if not request.url.path.startswith("/api/v1/admin"):
            return await call_next(request)
        
        # 获取数据库会话
        db = get_db()
        
        # 验证管理员身份
        try:
            credentials: HTTPAuthorizationCredentials = await security(request)
            token = credentials.credentials
            
            # 临时实现，实际应该解析 JWT token
            admin_id = 1
            
            # 验证管理员是否存在
            admin_repository = SQLAlchemyAdminUserRepository(db)
            admin = admin_repository.get_by_id(admin_id)
            if not admin or not admin.is_active:
                raise HTTPException(status_code=401, detail="未授权的管理员")
            
            # 将管理员信息添加到请求中
            request.state.admin_id = admin_id
            request.state.admin_role = admin.role
            
        except Exception as e:
            raise HTTPException(status_code=401, detail="未授权的访问")
        
        response = await call_next(request)
        return response

def require_role(role):
    """
    需要特定角色的装饰器
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            from app.domain.admin.constant.admin_role import AdminRole
            admin_role = request.state.admin_role
            
            # 检查角色层级
            if admin_role == role:
                return await func(request, *args, **kwargs)
            
            # 检查角色继承关系
            from app.domain.admin.constant.admin_role import ROLE_HIERARCHY
            current_role = AdminRole(admin_role)
            required_role = AdminRole(role)
            
            def check_hierarchy(current, required):
                if current == required:
                    return True
                for sub_role in ROLE_HIERARCHY.get(current, []):
                    if check_hierarchy(sub_role, required):
                        return True
                return False
            
            if check_hierarchy(current_role, required_role):
                return await func(request, *args, **kwargs)
            
            raise HTTPException(status_code=403, detail="权限不足")
        return wrapper
    return decorator

def require_permission(permission):
    """
    需要特定权限的装饰器
    """
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            admin_id = request.state.admin_id
            
            # 验证权限
            db = get_db()
            admin_repository = SQLAlchemyAdminUserRepository(db)
            permission_service = AdminPermissionService(admin_repository)
            
            from app.domain.admin.constant.admin_role import AdminPermission
            try:
                perm = AdminPermission(permission)
                if not permission_service.verify_permission(admin_id, perm):
                    raise HTTPException(status_code=403, detail="权限不足")
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的权限")
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator
