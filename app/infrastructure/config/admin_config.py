from pydantic_settings import BaseSettings
from typing import Optional

class AdminConfig(BaseSettings):
    """
    管理后台配置
    """
    # 管理后台启用状态
    enabled: bool = True
    
    # 审计日志配置
    audit:
        log_retention_days: int = 90  # 热数据保留天数
        auto_cleanup: bool = True  # 是否自动清理
    
    # 工具配置
    tool:
        max_upload_size: int = 10 * 1024 * 1024  # 工具上传最大大小 (10MB)
        audit_timeout: int = 24  # 审核超时时间 (小时)
        auto_audit_enabled: bool = False  # 是否启用自动审核
    
    # 权限缓存配置
    permission:
        cache_enabled: bool = True  # 是否启用权限缓存
        cache_ttl: int = 300  # 缓存 TTL (秒)
    
    # 敏感操作配置
    sensitive_actions: list = [
        "DELETE_OFFICIAL_PROVIDER",
        "DELETE_OFFICIAL_TOOL",
        "BATCH_AUDIT",
        "MANAGE_ADMINS"
    ]
    
    # 审核员分配方式
    auditor_assignment: str = "ROUND_ROBIN"  # ROUND_ROBIN, MANUAL
    
    class Config:
        env_file = ".env"
        env_nested_delimiter = "__"

# 创建配置实例
admin_config = AdminConfig()
