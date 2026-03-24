from typing import List, Optional
from app.domain.llm.entities import ProviderEntity, ModelEntity
from app.domain.llm.aggregate import ProviderAggregate
from app.domain.llm.enums import ProviderType, ModelType, ProviderProtocol
from app.domain.llm.config import ProviderConfig, encrypt_provider_config, decrypt_provider_config
from app.domain.llm.events import ModelCreatedEvent, ModelUpdatedEvent, ModelDeletedEvent, ModelStatusChangedEvent, ModelsBatchDeletedEvent
from app.domain.llm.protocol import ProtocolAdapterFactory
import time


class LLMDomainService:
    """LLM领域服务"""
    
    def __init__(self):
        self.protocol_factory = ProtocolAdapterFactory()
    
    async def create_provider(self, entity: ProviderEntity) -> ProviderEntity:
        """创建服务商"""
        # 验证协议配置
        config = decrypt_provider_config(entity.config)
        adapter = self.protocol_factory.get_adapter(entity.protocol)
        if not adapter.validate_config(config):
            # 重新验证并获取具体的错误信息
            if not config.api_key:
                raise ValueError("apikey 认证失败: API key 不能为空")
            if config.base_url and not config.base_url.startswith("https://"):
                raise ValueError("apikey 认证失败: Base URL 必须使用 https")
            if not config.api_key.strip():
                raise ValueError("apikey 认证失败: API key 不能只包含空白字符")
            raise ValueError("apikey 认证失败: 无效的配置")
        
        # 这里应该调用Repository保存实体
        return entity
    
    async def update_provider(self, entity: ProviderEntity) -> ProviderEntity:
        """更新服务商"""
        # 验证协议配置
        config = decrypt_provider_config(entity.config)
        adapter = self.protocol_factory.get_adapter(entity.protocol)
        if not adapter.validate_config(config):
            raise ValueError("Invalid provider configuration")
        
        # 这里应该调用Repository更新实体
        entity.updated_at = entity.updated_at.__class__(time.time())
        return entity
    
    async def delete_provider(self, provider_id: str) -> None:
        """删除服务商"""
        # 这里应该调用Repository删除实体
        pass
    
    async def get_provider(self, provider_id: str) -> ProviderAggregate:
        """获取服务商聚合根"""
        # 这里应该从Repository获取服务商和模型
        # 现在返回模拟数据
        mock_provider = ProviderEntity(
            id=provider_id,
            user_id="system",
            protocol=ProviderProtocol.OPENAI,
            name="OpenAI Official",
            config=encrypt_provider_config(ProviderConfig(api_key="sk-xxxxxxxxxx")),
            is_official=True,
            status=True
        )
        
        mock_models = [
            ModelEntity(
                id="model-1",
                user_id="system",
                provider_id=provider_id,
                model_id="gpt-4",
                name="GPT-4",
                type=ModelType.CHAT,
                status=True
            ),
            ModelEntity(
                id="model-2",
                user_id="system",
                provider_id=provider_id,
                model_id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                type=ModelType.CHAT,
                status=True
            )
        ]
        
        return ProviderAggregate(provider=mock_provider, models=mock_models)
    
    async def get_all_providers(self, user_id: str, provider_type: ProviderType) -> List[ProviderAggregate]:
        """获取所有服务商"""
        # 这里应该从Repository获取服务商列表
        # 现在返回模拟数据
        mock_aggregates = []
        
        # 添加官方服务商
        if provider_type in [ProviderType.ALL, ProviderType.OFFICIAL]:
            official_provider = ProviderEntity(
                id="official-provider-1",
                user_id="system",
                protocol=ProviderProtocol.OPENAI,
                name="OpenAI Official",
                config=encrypt_provider_config(ProviderConfig(api_key="sk-xxxxxxxxxx")),
                is_official=True,
                status=True
            )
            
            official_models = [
                ModelEntity(
                    id="model-1",
                    user_id="system",
                    provider_id="official-provider-1",
                    model_id="gpt-4",
                    name="GPT-4",
                    type=ModelType.CHAT,
                    status=True
                )
            ]
            
            mock_aggregates.append(ProviderAggregate(provider=official_provider, models=official_models))
        
        # 添加用户自定义服务商
        if provider_type in [ProviderType.ALL, ProviderType.CUSTOM]:
            custom_provider = ProviderEntity(
                id="custom-provider-1",
                user_id=user_id,
                protocol=ProviderProtocol.CUSTOM,
                name="Custom Provider",
                config=encrypt_provider_config(ProviderConfig(api_key="sk-custom", base_url="https://api.custom.com/v1")),
                is_official=False,
                status=True
            )
            
            custom_models = [
                ModelEntity(
                    id="model-3",
                    user_id=user_id,
                    provider_id="custom-provider-1",
                    model_id="custom-model",
                    name="Custom Model",
                    type=ModelType.CHAT,
                    status=True
                )
            ]
            
            mock_aggregates.append(ProviderAggregate(provider=custom_provider, models=custom_models))
        
        return mock_aggregates
    
    async def update_provider_status(self, provider_id: str, status: bool) -> None:
        """更新服务商状态"""
        # 这里应该调用Repository更新状态
        pass
    
    async def create_model(self, entity: ModelEntity) -> ModelEntity:
        """创建模型"""
        # 这里应该调用Repository保存实体
        return entity
    
    async def update_model(self, entity: ModelEntity) -> ModelEntity:
        """更新模型"""
        # 这里应该调用Repository更新实体
        entity.updated_at = entity.updated_at.__class__(time.time())
        return entity
    
    async def delete_model(self, model_id: str) -> None:
        """删除模型"""
        # 这里应该调用Repository删除实体
        pass
    
    async def update_model_status(self, model_id: str, status: bool) -> None:
        """更新模型状态"""
        # 这里应该调用Repository更新状态
        pass
    
    async def get_active_model_list(self, provider_type: ProviderType, model_type: ModelType) -> List[ModelEntity]:
        """获取激活的模型列表"""
        # 这里应该从Repository获取激活的模型
        # 现在返回模拟数据
        mock_models = [
            ModelEntity(
                id="model-1",
                user_id="system",
                provider_id="official-provider-1",
                model_id="gpt-4",
                name="GPT-4",
                type=model_type,
                status=True
            ),
            ModelEntity(
                id="model-2",
                user_id="system",
                provider_id="official-provider-1",
                model_id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                type=model_type,
                status=True
            )
        ]
        return mock_models
    
    async def check_provider_exists(self, provider_id: str) -> bool:
        """检查服务商是否存在"""
        # 这里应该调用Repository检查
        return True
    
    async def get_provider_aggregate(self, provider_id: str) -> ProviderAggregate:
        """获取服务商聚合根"""
        return await self.get_provider(provider_id)
    
    def get_provider_protocols(self) -> List[ProviderProtocol]:
        """获取支持的协议列表"""
        return list(ProviderProtocol)
