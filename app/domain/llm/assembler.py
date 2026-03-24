from typing import TYPE_CHECKING
from app.domain.llm.entities import ProviderEntity, ModelEntity
from app.domain.llm.dto import ProviderDTO, ModelDTO, ProviderCreateDTO, ModelCreateDTO
from app.domain.llm.config import ProviderConfig, encrypt_provider_config

if TYPE_CHECKING:
    from app.domain.llm.aggregate import ProviderAggregate


class ProviderAssembler:
    """服务商转换器"""
    
    @staticmethod
    def to_entity(dto: ProviderCreateDTO, user_id: str, provider_id: str) -> ProviderEntity:
        """转换为实体"""
        encrypted_config = encrypt_provider_config(dto.config)
        return ProviderEntity(
            id=provider_id,
            user_id=user_id,
            protocol=dto.protocol,
            name=dto.name,
            description=dto.description,
            config=encrypted_config,
            is_official=dto.is_official,
            status=dto.status
        )
    
    @staticmethod
    def to_dto(aggregate: 'ProviderAggregate', mask_api_key: bool = True) -> ProviderDTO:
        """转换为DTO"""
        config = aggregate.get_decrypted_config()
        if mask_api_key:
            config.api_key = "******"
        
        return ProviderDTO(
            id=aggregate.provider.id,
            name=aggregate.provider.name,
            protocol=aggregate.provider.protocol,
            description=aggregate.provider.description,
            is_official=aggregate.provider.is_official,
            status=aggregate.provider.status,
            config=config,
            models=[ModelAssembler.to_dto(m) for m in aggregate.models],
            created_at=aggregate.provider.created_at,
            updated_at=aggregate.provider.updated_at
        )


class ModelAssembler:
    """模型转换器"""
    
    @staticmethod
    def to_entity(dto: ModelCreateDTO, user_id: str, model_id: str) -> ModelEntity:
        """转换为实体"""
        return ModelEntity(
            id=model_id,
            user_id=user_id,
            provider_id=dto.provider_id,
            model_id=dto.model_id,
            name=dto.name,
            description=dto.description,
            model_endpoint=dto.model_endpoint,
            type=dto.type,
            is_official=dto.is_official,
            status=dto.status
        )
    
    @staticmethod
    def to_dto(entity: ModelEntity) -> ModelDTO:
        """转换为DTO"""
        return ModelDTO(
            id=entity.id,
            provider_id=entity.provider_id,
            model_id=entity.model_id,
            name=entity.name,
            description=entity.description,
            model_endpoint=entity.model_endpoint,
            type=entity.type,
            is_official=entity.is_official,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )
