import pytest
import asyncio
from app.domain.llm.high_availability import HighAvailabilityDomainService, RoundRobinStrategy, RandomStrategy, ResponseTimeStrategy, WeightedRoundRobinStrategy
from app.domain.llm.circuit_breaker import CircuitBreakerService, CircuitState
from app.domain.llm.health_check import HealthCheckScheduler, HealthStatus
from app.domain.llm.fallback import FallbackChainManager, FallbackChain, FallbackModel, FallbackTriggerConditions, RecoveryConfig
from app.domain.llm.enums import ModelType


@pytest.mark.asyncio
async def test_high_availability_domain_service():
    """测试高可用领域服务"""
    # 创建服务实例
    ha_service = HighAvailabilityDomainService()
    
    # 测试选择最佳提供商
    result = await ha_service.select_best_provider(ModelType.CHAT, session_id="test-session")
    assert result.provider_id == "mock-provider-1"
    assert result.model_id == "gpt-4"
    assert not result.is_fallback
    
    # 测试上报调用结果
    await ha_service.report_call_result("gpt-4", True, 100.5)
    assert "gpt-4" in ha_service.model_health
    assert ha_service.model_health["gpt-4"]["success"] is True
    
    # 测试设置负载均衡策略
    ha_service.set_load_balance_strategy(RandomStrategy())
    result2 = await ha_service.select_best_provider(ModelType.CHAT)
    assert result2.provider_id == "mock-provider-1"


@pytest.mark.asyncio
async def test_circuit_breaker_service():
    """测试熔断器服务"""
    # 创建服务实例
    circuit_breaker_service = CircuitBreakerService()
    
    # 测试初始状态
    state = await circuit_breaker_service.get_circuit_state("test-model")
    assert state == CircuitState.CLOSED
    
    # 测试记录成功
    await circuit_breaker_service.record_call_result("test-model", True, 50.0)
    should_allow = await circuit_breaker_service.should_allow_request("test-model")
    assert should_allow is True
    
    # 测试记录失败
    for _ in range(11):  # 超过连续失败阈值
        await circuit_breaker_service.record_call_result("test-model", False, 100.0)
    
    # 测试熔断状态
    state = await circuit_breaker_service.get_circuit_state("test-model")
    assert state == CircuitState.OPEN
    
    # 测试是否允许请求
    should_allow = await circuit_breaker_service.should_allow_request("test-model")
    assert should_allow is False


@pytest.mark.asyncio
async def test_health_check_scheduler():
    """测试健康检查调度器"""
    # 创建调度器
    scheduler = HealthCheckScheduler(max_concurrent=10)
    
    # 启动调度器
    await scheduler.start()
    
    # 等待一段时间，让健康检查执行
    await asyncio.sleep(1)
    
    # 停止调度器
    await scheduler.stop()
    
    # 测试获取健康状态
    status = scheduler.get_health_status("model-1")
    assert status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]


@pytest.mark.asyncio
async def test_fallback_chain_manager():
    """测试降级链管理器"""
    # 创建降级链
    fallback_chain = FallbackChain(
        primary_model={"provider": "openai", "model": "gpt-4"},
        fallback_chain=[
            FallbackModel(provider="openai", model="gpt-3.5-turbo", weight=1.0),
            FallbackModel(provider="anthropic", model="claude-3-sonnet", weight=0.9)
        ],
        trigger_conditions=FallbackTriggerConditions(consecutive_failures=2),
        recovery=RecoveryConfig(auto_recovery=True)
    )
    
    # 创建管理器
    manager = FallbackChainManager()
    manager.add_fallback_chain("test-chain", fallback_chain)
    
    # 模拟执行函数
    async def mock_execute(model_config, *args, **kwargs):
        if model_config.get("model") == "gpt-4":
            raise Exception("Primary model failed")
        return f"Success with {model_config.get('model')}"
    
    # 测试降级
    result = await manager.execute_with_fallback("test-chain", mock_execute)
    assert "gpt-3.5-turbo" in result
    
    # 测试获取状态
    status = manager.get_chain_status("test-chain")
    assert status["is_degraded"] is True
    assert status["current_index"] == 1


@pytest.mark.asyncio
async def test_load_balance_strategies():
    """测试负载均衡策略"""
    # 创建策略实例
    round_robin = RoundRobinStrategy()
    random_strategy = RandomStrategy()
    response_time = ResponseTimeStrategy()
    weighted = WeightedRoundRobinStrategy()
    
    # 创建模拟模型实例
    from app.domain.llm.entities import ModelEntity
    models = [
        ModelEntity(
            id="model-1",
            user_id="system",
            provider_id="openai",
            model_id="gpt-4",
            name="GPT-4",
            type=ModelType.CHAT,
            status=True
        ),
        ModelEntity(
            id="model-2",
            user_id="system",
            provider_id="openai",
            model_id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo",
            type=ModelType.CHAT,
            status=True
        )
    ]
    
    # 测试轮询策略
    instance1 = await round_robin.select_instance(models)
    instance2 = await round_robin.select_instance(models)
    assert instance1.id != instance2.id
    
    # 测试随机策略
    instance = await random_strategy.select_instance(models)
    assert instance is not None
    
    # 测试响应时间策略
    response_time.record_response_time("model-1", 100.0)
    response_time.record_response_time("model-2", 50.0)
    instance = await response_time.select_instance(models)
    assert instance.id == "model-2"
    
    # 测试加权轮询策略
    weighted.update_weights({"model-1": 0.5, "model-2": 1.0})
    instance = await weighted.select_instance(models)
    assert instance.id == "model-2"


if __name__ == "__main__":
    pytest.main([__file__])