from typing import List, TYPE_CHECKING
from pydantic import BaseModel
from app.domain.llm.entities import ProviderEntity, ModelEntity
from app.domain.llm.config import decrypt_provider_config, ProviderConfig
from app.domain.llm.dto import ProviderDTO, ModelDTO

if TYPE_CHECKING:
    from app.domain.llm.assembler import ProviderAssembler, ModelAssembler


class ProviderAggregate(BaseModel):
    """服务商聚合根"""
    provider: ProviderEntity
    models: List[ModelEntity]
    
    def get_decrypted_config(self) -> ProviderConfig:
        """获取解密后的配置"""
        return decrypt_provider_config(self.provider.config)
    
    def to_dto(self, mask_api_key: bool = True) -> ProviderDTO:
        """转换为DTO，可选择掩码API Key"""
        from app.domain.llm.assembler import ProviderAssembler
        return ProviderAssembler.to_dto(self, mask_api_key=mask_api_key)
