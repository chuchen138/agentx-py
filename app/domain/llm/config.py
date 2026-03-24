from pydantic import BaseModel, Field
from typing import Optional
import os
from cryptography.fernet import Fernet


class ProviderConfig(BaseModel):
    """服务商配置"""
    api_key: str = Field(..., description="API 密钥")
    base_url: Optional[str] = Field(None, description="自定义 Endpoint URL")


class ProviderConfigEncrypted(BaseModel):
    """加密后的服务商配置"""
    encrypted_config: str


# 加密密钥管理
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_provider_config(config: ProviderConfig) -> str:
    """加密服务商配置"""
    config_json = config.model_dump_json()
    encrypted = fernet.encrypt(config_json.encode())
    return encrypted.decode()


def decrypt_provider_config(encrypted_config: str) -> ProviderConfig:
    """解密服务商配置"""
    decrypted = fernet.decrypt(encrypted_config.encode())
    config = ProviderConfig.model_validate_json(decrypted)
    return config
