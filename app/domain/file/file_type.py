from enum import Enum


class FileType(Enum):
    """文件类型枚举"""
    AVATAR = "AVATAR"  # 用户头像
    GENERAL = "GENERAL"  # 通用文件
    RAG = "RAG"  # RAG 文档文件
