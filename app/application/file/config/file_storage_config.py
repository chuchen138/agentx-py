from pydantic_settings import BaseSettings
from typing import Dict, Any, Optional


class FileStorageSettings(BaseSettings):
    """文件存储配置"""
    # 启用状态
    enabled: bool = True
    # 默认存储后端
    default_platform: str = "local"
    # 存储平台配置
    platforms: Dict[str, Dict[str, Any]] = {
        "local": {
            "domain": "http://localhost:8000",
            "path-prefix": "/uploads/"
        },
        "oss": {
            "endpoint": "oss-cn-hangzhou.aliyuncs.com",
            "bucket": "agentx-files"
        },
        "s3": {
            "region": "us-east-1",
            "bucket": "agentx-files"
        },
        "cos": {
            "region": "ap-shanghai",
            "bucket": "agentx-files"
        }
    }
    # 上传限制
    upload_limits: Dict[str, int] = {
        "max_file_size": 50 * 1024 * 1024,  # 50MB
        "chunk_size": 5 * 1024 * 1024,  # 5MB
        "max_avatar_size": 2 * 1024 * 1024,  # 2MB
        "max_rag_size": 500 * 1024 * 1024  # 500MB
    }
    # 文件路径规则
    path_rules: Dict[str, str] = {
        "avatar": "/avatar/{user_id}/{timestamp}_{filename}",
        "general": "/general/{user_id}/{date}/{uuid}_{filename}",
        "rag": "/rag/{user_id}/{dataset_id}/{uuid}_{filename}"
    }
    # URL签名配置
    url_signing: Dict[str, Any] = {
        "enabled": False,
        "expires_in": 3600  # 1小时
    }
    # 缓存配置
    cache: Dict[str, Any] = {
        "enabled": True,
        "ttl": 3600,  # 1小时
        "max_size": 1000  # 最大缓存数
    }
    # 安全配置
    security: Dict[str, Any] = {
        "virus_scan": False,
        "file_type_whitelist": True
    }

    class Config:
        env_file = ".env"
        env_prefix = "FILE_STORAGE_"


# 全局配置实例
file_storage_settings = FileStorageSettings()
