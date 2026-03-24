from enum import Enum


class ProviderProtocol(str, Enum):
    """服务商协议类型"""
    OPENAI = "OPENAI"
    MOONSHOT = "MOONSHOT"
    AZURE_OPENAI = "AZURE_OPENAI"
    CUSTOM = "CUSTOM"


class ModelType(str, Enum):
    """模型类型"""
    CHAT = "CHAT"
    EMBEDDING = "EMBEDDING"


class ProviderType(str, Enum):
    """服务商类型"""
    ALL = "ALL"
    OFFICIAL = "OFFICIAL"
    CUSTOM = "CUSTOM"


class OperatorType(str, Enum):
    """操作者类型"""
    USER = "USER"
    ADMIN = "ADMIN"
