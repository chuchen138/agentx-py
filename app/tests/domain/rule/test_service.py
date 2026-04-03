import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.domain.rule.model import Base, RuleEntity
from app.domain.rule.service import RuleDomainService
from app.domain.rule.exceptions import RuleValidationError





@pytest.mark.asyncio
async def test_create_rule():
    """测试创建规则"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = RuleDomainService()
        
        # 创建规则
        rule = await service.create_rule(
            name="测试规则",
            handler_key="model_usage_billing",
            description="测试计费规则",
            config={
                "input_price_per_1k_tokens": 0.03,
                "output_price_per_1k_tokens": 0.06
            },
            priority=100,
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
    
    assert rule is not None
    assert rule.name == "测试规则"
    assert rule.handler_key == "model_usage_billing"
    assert rule.version == 1


@pytest.mark.asyncio
async def test_get_rule():
    """测试获取规则"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = RuleDomainService()
        
        # 先创建规则
        rule = await service.create_rule(
            name="测试规则",
            handler_key="model_usage_billing",
            description="测试计费规则",
            config={
                "input_price_per_1k_tokens": 0.03,
                "output_price_per_1k_tokens": 0.06
            },
            priority=100,
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
        
        # 获取规则
        fetched_rule = await service.get_rule(rule.id, session=session)
        
        assert fetched_rule is not None
        assert fetched_rule.id == rule.id
        assert fetched_rule.name == rule.name


@pytest.mark.asyncio
async def test_update_rule():
    """测试更新规则"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = RuleDomainService()
        
        # 先创建规则
        rule = await service.create_rule(
            name="测试规则",
            handler_key="model_usage_billing",
            description="测试计费规则",
            config={
                "input_price_per_1k_tokens": 0.03,
                "output_price_per_1k_tokens": 0.06
            },
            priority=100,
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
        
        # 更新规则
        updated_rule = await service.update_rule(
            rule_id=rule.id,
            name="更新后的规则",
            description="更新后的描述",
            config={
                "input_price_per_1k_tokens": 0.04,
                "output_price_per_1k_tokens": 0.08
            },
            priority=200,
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
        
        assert updated_rule.name == "更新后的规则"
        assert updated_rule.description == "更新后的描述"
        assert updated_rule.config["input_price_per_1k_tokens"] == 0.04
        assert updated_rule.priority == 200
        assert updated_rule.version == 2


@pytest.mark.asyncio
async def test_list_rules():
    """测试查询规则列表"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = RuleDomainService()
        
        # 创建多个规则
        for i in range(3):
            await service.create_rule(
                name=f"测试规则{i}",
                handler_key="model_usage_billing",
                description=f"测试计费规则{i}",
                config={
                    "input_price_per_1k_tokens": 0.03,
                    "output_price_per_1k_tokens": 0.06
                },
                priority=100 + i,
                operator="test@example.com",
                ip_address="127.0.0.1",
                session=session
            )
        
        # 查询规则列表
        result = await service.list_rules(
            session=session,
            handler_key="model_usage_billing",
            page=1,
            page_size=10
        )
        
        assert result["total"] == 3
        assert len(result["records"]) == 3


@pytest.mark.asyncio
async def test_toggle_rule():
    """测试启用/禁用规则"""
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        service = RuleDomainService()
        
        # 创建规则
        rule = await service.create_rule(
            name="测试规则",
            handler_key="model_usage_billing",
            description="测试计费规则",
            config={
                "input_price_per_1k_tokens": 0.03,
                "output_price_per_1k_tokens": 0.06
            },
            priority=100,
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
        
        assert rule.enabled is True
        
        # 禁用规则
        disabled_rule = await service.toggle_rule(
            rule_id=rule.id,
            enabled=False,
            reason="测试禁用",
            operator="test@example.com",
            ip_address="127.0.0.1",
            session=session
        )
        
        assert disabled_rule.enabled is False
        assert disabled_rule.version == 2
