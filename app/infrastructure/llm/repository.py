from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update, and_, or_
from app.core.models.llm import Provider, Model
from app.domain.llm.entities import ProviderEntity, ModelEntity
from app.domain.llm.aggregate import ProviderAggregate
from app.domain.llm.enums import ProviderType
from datetime import datetime


class ProviderRepository:
    """服务商仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, entity: ProviderEntity) -> ProviderEntity:
        """创建服务商"""
        db_provider = Provider(
            id=entity.id,
            user_id=entity.user_id,
            protocol=entity.protocol.value,
            name=entity.name,
            description=entity.description,
            config=entity.config,
            is_official=entity.is_official,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at
        )
        self.session.add(db_provider)
        await self.session.commit()
        await self.session.refresh(db_provider)
        return self._to_entity(db_provider)
    
    async def update(self, entity: ProviderEntity) -> ProviderEntity:
        """更新服务商"""
        stmt = update(Provider).where(Provider.id == entity.id).values(
            name=entity.name,
            description=entity.description,
            config=entity.config,
            status=entity.status,
            updated_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.commit()
        db_provider = await self.session.get(Provider, entity.id)
        return self._to_entity(db_provider)
    
    async def delete(self, provider_id: str) -> None:
        """删除服务商（逻辑删除）"""
        stmt = update(Provider).where(Provider.id == provider_id).values(
            deleted_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def find_by_id(self, provider_id: str) -> Optional[ProviderEntity]:
        """根据ID查找服务商"""
        stmt = select(Provider).where(
            and_(Provider.id == provider_id, Provider.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_provider = result.scalar_one_or_none()
        return self._to_entity(db_provider) if db_provider else None
    
    async def find_by_user_id(self, user_id: str) -> List[ProviderEntity]:
        """根据用户ID查找服务商"""
        stmt = select(Provider).where(
            and_(Provider.user_id == user_id, Provider.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_providers = result.scalars().all()
        return [self._to_entity(p) for p in db_providers]
    
    async def find_official_providers(self) -> List[ProviderEntity]:
        """查找官方服务商"""
        stmt = select(Provider).where(
            and_(Provider.is_official == True, Provider.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_providers = result.scalars().all()
        return [self._to_entity(p) for p in db_providers]
    
    async def get_aggregate(self, provider_id: str) -> Optional[ProviderAggregate]:
        """获取服务商聚合根"""
        # 查询服务商
        stmt = select(Provider).where(
            and_(Provider.id == provider_id, Provider.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_provider = result.scalar_one_or_none()
        if not db_provider:
            return None
        
        # 查询该服务商下的所有模型
        stmt = select(Model).where(
            and_(Model.provider_id == provider_id, Model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_models = result.scalars().all()
        
        provider_entity = self._to_entity(db_provider)
        model_entities = [self._model_to_entity(m) for m in db_models]
        
        return ProviderAggregate(provider=provider_entity, models=model_entities)
    
    def _to_entity(self, db_provider: Provider) -> ProviderEntity:
        """转换为实体"""
        from app.domain.llm.enums import ProviderProtocol
        return ProviderEntity(
            id=db_provider.id,
            user_id=db_provider.user_id,
            protocol=ProviderProtocol(db_provider.protocol),
            name=db_provider.name,
            description=db_provider.description,
            config=db_provider.config,
            is_official=db_provider.is_official,
            status=db_provider.status,
            created_at=db_provider.created_at,
            updated_at=db_provider.updated_at,
            deleted_at=db_provider.deleted_at
        )
    
    def _model_to_entity(self, db_model: Model) -> ModelEntity:
        """转换模型为实体"""
        from app.domain.llm.enums import ModelType
        return ModelEntity(
            id=db_model.id,
            user_id=db_model.user_id,
            provider_id=db_model.provider_id,
            model_id=db_model.model_id,
            name=db_model.name,
            description=db_model.description,
            model_endpoint=db_model.model_endpoint,
            type=ModelType(db_model.type),
            is_official=db_model.is_official,
            status=db_model.status,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            deleted_at=db_model.deleted_at
        )


class ModelRepository:
    """模型仓库"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, entity: ModelEntity) -> ModelEntity:
        """创建模型"""
        db_model = Model(
            id=entity.id,
            user_id=entity.user_id,
            provider_id=entity.provider_id,
            model_id=entity.model_id,
            name=entity.name,
            description=entity.description,
            model_endpoint=entity.model_endpoint,
            type=entity.type.value,
            is_official=entity.is_official,
            status=entity.status,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
            deleted_at=entity.deleted_at
        )
        self.session.add(db_model)
        await self.session.commit()
        await self.session.refresh(db_model)
        return self._to_entity(db_model)
    
    async def update(self, entity: ModelEntity) -> ModelEntity:
        """更新模型"""
        stmt = update(Model).where(Model.id == entity.id).values(
            name=entity.name,
            description=entity.description,
            model_endpoint=entity.model_endpoint,
            status=entity.status,
            updated_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.commit()
        db_model = await self.session.get(Model, entity.id)
        return self._to_entity(db_model)
    
    async def delete(self, model_id: str) -> None:
        """删除模型（逻辑删除）"""
        stmt = update(Model).where(Model.id == model_id).values(
            deleted_at=datetime.utcnow()
        )
        await self.session.execute(stmt)
        await self.session.commit()
    
    async def find_by_id(self, model_id: str) -> Optional[ModelEntity]:
        """根据ID查找模型"""
        stmt = select(Model).where(
            and_(Model.id == model_id, Model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_model = result.scalar_one_or_none()
        return self._to_entity(db_model) if db_model else None
    
    async def find_by_provider_id(self, provider_id: str) -> List[ModelEntity]:
        """根据服务商ID查找模型"""
        stmt = select(Model).where(
            and_(Model.provider_id == provider_id, Model.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        db_models = result.scalars().all()
        return [self._to_entity(m) for m in db_models]
    
    async def find_active_models(self, provider_type: ProviderType, model_type: str) -> List[ModelEntity]:
        """查找激活的模型"""
        if provider_type == ProviderType.OFFICIAL:
            condition = Model.is_official == True
        elif provider_type == ProviderType.CUSTOM:
            condition = Model.is_official == False
        else:  # ALL
            condition = or_(Model.is_official == True, Model.is_official == False)
        
        stmt = select(Model).where(
            and_(
                condition,
                Model.type == model_type,
                Model.status == True,
                Model.deleted_at.is_(None)
            )
        )
        result = await self.session.execute(stmt)
        db_models = result.scalars().all()
        return [self._to_entity(m) for m in db_models]
    
    def _to_entity(self, db_model: Model) -> ModelEntity:
        """转换为实体"""
        from app.domain.llm.enums import ModelType
        return ModelEntity(
            id=db_model.id,
            user_id=db_model.user_id,
            provider_id=db_model.provider_id,
            model_id=db_model.model_id,
            name=db_model.name,
            description=db_model.description,
            model_endpoint=db_model.model_endpoint,
            type=ModelType(db_model.type),
            is_official=db_model.is_official,
            status=db_model.status,
            created_at=db_model.created_at,
            updated_at=db_model.updated_at,
            deleted_at=db_model.deleted_at
        )
