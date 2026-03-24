from typing import List, Optional
from app.domain.llm.dto import ProviderDTO, ModelDTO, ProviderCreateDTO, ProviderUpdateDTO, ModelCreateDTO, ModelUpdateDTO
from app.domain.llm.entities import ProviderEntity, ModelEntity
from app.domain.llm.aggregate import ProviderAggregate
from app.domain.llm.enums import ProviderType, ModelType
from app.domain.llm.service import LLMDomainService
from app.domain.llm.assembler import ProviderAssembler, ModelAssembler
from app.domain.llm.high_availability import HighAvailabilityDomainService
from app.domain.llm.events import ModelCreatedEvent, ModelUpdatedEvent, ModelDeletedEvent, ModelStatusChangedEvent, ModelsBatchDeletedEvent
import uuid
import time
from fastapi import BackgroundTasks


class LLMAppService:
    """LLM应用服务"""
    
    def __init__(self):
        self.domain_service = LLMDomainService()
        self.ha_service = HighAvailabilityDomainService()
        from app.core.database import get_db
        from app.infrastructure.llm.preference_repository import UserModelPreferenceRepository
        self.db = next(get_db())
        self.preference_repo = UserModelPreferenceRepository(self.db)
    
    async def create_provider(self, dto: ProviderCreateDTO, user_id: str) -> ProviderDTO:
        """创建服务商"""
        provider_id = str(uuid.uuid4())
        entity = ProviderAssembler.to_entity(dto, user_id, provider_id)
        try:
            created_entity = await self.domain_service.create_provider(entity)
        except ValueError as e:
            # API key 认证失败，将状态设置为 false
            entity.status = False
            created_entity = entity
            print(f"创建服务商失败: {str(e)}")
        aggregate = ProviderAggregate(provider=created_entity, models=[])
        return aggregate.to_dto()
    
    async def update_provider(self, provider_id: str, dto: ProviderUpdateDTO, user_id: str) -> ProviderDTO:
        """更新服务商"""
        aggregate = await self.domain_service.get_provider(provider_id)
        # 这里应该检查权限
        
        # 更新字段
        if dto.name:
            aggregate.provider.name = dto.name
        if dto.description:
            aggregate.provider.description = dto.description
        if dto.config:
            from app.domain.llm.config import encrypt_provider_config
            aggregate.provider.config = encrypt_provider_config(dto.config)
        if dto.status is not None:
            aggregate.provider.status = dto.status
        
        updated_entity = await self.domain_service.update_provider(aggregate.provider)
        updated_aggregate = ProviderAggregate(provider=updated_entity, models=aggregate.models)
        return updated_aggregate.to_dto()
    
    async def delete_provider(self, provider_id: str, user_id: str) -> None:
        """删除服务商"""
        # 这里应该检查权限
        await self.domain_service.delete_provider(provider_id)
    
    async def get_all_providers(self, user_id: str, provider_type: ProviderType) -> List[ProviderDTO]:
        """获取所有服务商"""
        aggregates = await self.domain_service.get_all_providers(user_id, provider_type)
        return [agg.to_dto() for agg in aggregates]
    
    async def update_provider_status(self, provider_id: str, status: bool, user_id: str) -> None:
        """更新服务商状态"""
        # 这里应该检查权限
        await self.domain_service.update_provider_status(provider_id, status)
    
    async def refresh_provider_status(self, provider_id: str, user_id: str) -> bool:
        """刷新服务商状态，测试配置是否可用"""
        # 这里应该检查权限
        aggregate = await self.domain_service.get_provider(provider_id)
        try:
            # 测试配置是否可用
            from app.domain.llm.config import decrypt_provider_config
            config = decrypt_provider_config(aggregate.provider.config)
            from app.domain.llm.protocol import ProtocolAdapterFactory
            factory = ProtocolAdapterFactory()
            adapter = factory.get_adapter(aggregate.provider.protocol)
            if adapter.validate_config(config):
                # 配置有效，更新状态为 true
                aggregate.provider.status = True
                # 这里应该调用Repository更新状态
                return True
            else:
                # 配置无效，更新状态为 false
                aggregate.provider.status = False
                # 这里应该调用Repository更新状态
                return False
        except Exception as e:
            # 测试失败，更新状态为 false
            aggregate.provider.status = False
            # 这里应该调用Repository更新状态
            print(f"测试服务商配置失败: {str(e)}")
            return False
    
    async def create_model(self, dto: ModelCreateDTO, user_id: str, background_tasks: BackgroundTasks) -> ModelDTO:
        """创建模型"""
        # 检查服务商是否存在
        if not await self.domain_service.check_provider_exists(dto.provider_id):
            raise ValueError("Provider not found")
        
        model_id = str(uuid.uuid4())
        entity = ModelAssembler.to_entity(dto, user_id, model_id)
        created_entity = await self.domain_service.create_model(entity)
        
        # 发布事件
        event = ModelCreatedEvent(
            event_type="ModelCreated",
            timestamp=time.time(),
            model=created_entity
        )
        background_tasks.add_task(self._process_event, event)
        
        # 同步到高可用网关
        background_tasks.add_task(self.ha_service.sync_model_to_gateway, created_entity)
        
        return ModelAssembler.to_dto(created_entity)
    
    async def update_model(self, model_id: str, dto: ModelUpdateDTO, user_id: str, background_tasks: BackgroundTasks) -> ModelDTO:
        """更新模型"""
        # 这里应该从Repository获取模型并检查权限
        # 现在使用模拟数据
        mock_model = ModelEntity(
            id=model_id,
            user_id=user_id,
            provider_id="test-provider",
            model_id="test-model",
            name="Test Model",
            type=ModelType.CHAT,
            status=True
        )
        
        # 更新字段
        if dto.name:
            mock_model.name = dto.name
        if dto.description:
            mock_model.description = dto.description
        if dto.model_endpoint:
            mock_model.model_endpoint = dto.model_endpoint
        if dto.status is not None:
            mock_model.status = dto.status
        
        updated_entity = await self.domain_service.update_model(mock_model)
        
        # 发布事件
        event = ModelUpdatedEvent(
            event_type="ModelUpdated",
            timestamp=time.time(),
            model=updated_entity
        )
        background_tasks.add_task(self._process_event, event)
        
        # 同步到高可用网关
        background_tasks.add_task(self.ha_service.update_model_in_gateway, updated_entity)
        
        return ModelAssembler.to_dto(updated_entity)
    
    async def delete_model(self, model_id: str, user_id: str, background_tasks: BackgroundTasks) -> None:
        """删除模型"""
        # 这里应该检查权限
        await self.domain_service.delete_model(model_id)
        
        # 发布事件
        event = ModelDeletedEvent(
            event_type="ModelDeleted",
            timestamp=time.time(),
            model_id=model_id
        )
        background_tasks.add_task(self._process_event, event)
        
        # 从高可用网关移除
        background_tasks.add_task(self.ha_service.remove_model_from_gateway, model_id)
    
    async def update_model_status(self, model_id: str, status: bool, user_id: str, background_tasks: BackgroundTasks) -> None:
        """更新模型状态"""
        # 这里应该检查权限
        await self.domain_service.update_model_status(model_id, status)
        
        # 发布事件
        event = ModelStatusChangedEvent(
            event_type="ModelStatusChanged",
            timestamp=time.time(),
            model_id=model_id,
            status=status
        )
        background_tasks.add_task(self._process_event, event)
    
    async def get_active_models_by_type(self, provider_type: ProviderType, model_type: ModelType) -> List[ModelDTO]:
        """获取激活的模型"""
        models = await self.domain_service.get_active_model_list(provider_type, model_type)
        return [ModelAssembler.to_dto(model) for model in models]
    
    def save_user_preference(self, user_id: str, provider_id: str, model_id: str) -> None:
        """保存用户模型偏好设置"""
        self.preference_repo.create_or_update(user_id, provider_id, model_id)
    
    def get_user_preference(self, user_id: str) -> dict:
        """获取用户模型偏好设置"""
        preference = self.preference_repo.get_by_user_id(user_id)
        if preference:
            return {
                "provider_id": preference.provider_id,
                "model_id": preference.model_id
            }
        return {}
    
    async def _process_event(self, event):
        """处理事件"""
        # 这里可以添加事件处理逻辑
        print(f"Processing event: {event.event_type}")


class AdminLLMAppService:
    """管理员LLM应用服务"""
    
    def __init__(self):
        self.domain_service = LLMDomainService()
        self.ha_service = HighAvailabilityDomainService()
    
    async def create_provider(self, dto: ProviderCreateDTO) -> ProviderDTO:
        """创建官方服务商"""
        provider_id = str(uuid.uuid4())
        # 管理员创建的服务商默认为官方
        dto.is_official = True
        entity = ProviderAssembler.to_entity(dto, "system", provider_id)
        created_entity = await self.domain_service.create_provider(entity)
        aggregate = ProviderAggregate(provider=created_entity, models=[])
        return aggregate.to_dto()
    
    async def update_provider(self, provider_id: str, dto: ProviderUpdateDTO) -> ProviderDTO:
        """更新官方服务商"""
        aggregate = await self.domain_service.get_provider(provider_id)
        
        # 更新字段
        if dto.name:
            aggregate.provider.name = dto.name
        if dto.description:
            aggregate.provider.description = dto.description
        if dto.config:
            from app.domain.llm.config import encrypt_provider_config
            aggregate.provider.config = encrypt_provider_config(dto.config)
        if dto.status is not None:
            aggregate.provider.status = dto.status
        
        updated_entity = await self.domain_service.update_provider(aggregate.provider)
        updated_aggregate = ProviderAggregate(provider=updated_entity, models=aggregate.models)
        return updated_aggregate.to_dto()
    
    async def delete_provider(self, provider_id: str) -> None:
        """删除官方服务商"""
        await self.domain_service.delete_provider(provider_id)
    
    async def create_model(self, dto: ModelCreateDTO, background_tasks: BackgroundTasks) -> ModelDTO:
        """创建官方模型"""
        # 检查服务商是否存在
        if not await self.domain_service.check_provider_exists(dto.provider_id):
            raise ValueError("Provider not found")
        
        model_id = str(uuid.uuid4())
        # 管理员创建的模型默认为官方
        dto.is_official = True
        entity = ModelAssembler.to_entity(dto, "system", model_id)
        created_entity = await self.domain_service.create_model(entity)
        
        # 同步到高可用网关
        background_tasks.add_task(self.ha_service.sync_model_to_gateway, created_entity)
        
        return ModelAssembler.to_dto(created_entity)
    
    async def update_model(self, model_id: str, dto: ModelUpdateDTO, background_tasks: BackgroundTasks) -> ModelDTO:
        """更新官方模型"""
        # 这里应该从Repository获取模型
        # 现在使用模拟数据
        mock_model = ModelEntity(
            id=model_id,
            user_id="system",
            provider_id="test-provider",
            model_id="test-model",
            name="Test Model",
            type=ModelType.CHAT,
            status=True,
            is_official=True
        )
        
        # 更新字段
        if dto.name:
            mock_model.name = dto.name
        if dto.description:
            mock_model.description = dto.description
        if dto.model_endpoint:
            mock_model.model_endpoint = dto.model_endpoint
        if dto.status is not None:
            mock_model.status = dto.status
        
        updated_entity = await self.domain_service.update_model(mock_model)
        
        # 同步到高可用网关
        background_tasks.add_task(self.ha_service.update_model_in_gateway, updated_entity)
        
        return ModelAssembler.to_dto(updated_entity)
    
    async def delete_model(self, model_id: str, background_tasks: BackgroundTasks) -> None:
        """删除官方模型"""
        await self.domain_service.delete_model(model_id)
        
        # 从高可用网关移除
        background_tasks.add_task(self.ha_service.remove_model_from_gateway, model_id)
