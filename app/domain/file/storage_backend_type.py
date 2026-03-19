from enum import Enum


class StorageBackendType(Enum):
    """存储后端类型枚举"""
    LOCAL = "local"  # 本地存储
    OSS = "oss"  # 阿里云 OSS
    S3 = "s3"  # AWS S3
    COS = "cos"  # 腾讯云 COS
