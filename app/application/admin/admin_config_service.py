from app.domain.admin.constant.admin_role import AdminRole

class AdminConfigService:
    def __init__(self):
        # 从配置文件或环境变量加载配置
        # TODO: 实现配置加载逻辑
        pass
    
    def get_audit_log_retention_days(self) -> int:
        """
        审计日志保留天数
        """
        # 默认 90 天热数据，2 年冷数据
        return 90
    
    def get_max_upload_size(self) -> int:
        """
        工具上传最大大小
        """
        # 默认 10MB
        return 10 * 1024 * 1024
    
    def get_audit_timeout(self) -> int:
        """
        审核超时时间
        """
        # 默认 24 小时
        return 24
    
    def is_auto_audit_enabled(self) -> bool:
        """
        是否启用自动审核
        """
        # 默认禁用
        return False
    
    def get_required_approval_level(self) -> AdminRole:
        """
        获取需要的审批级别
        """
        # 默认需要 ADMIN 级别
        return AdminRole.ADMIN
