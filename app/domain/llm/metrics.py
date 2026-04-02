from prometheus_client import Gauge, Counter, Histogram

# Gauge 指标
instance_health_status = Gauge(
    'ha_instance_health_status',
    'Instance health status (1=healthy, 0=unhealthy)',
    ['instance_id', 'provider', 'model']
)

circuit_breaker_state = Gauge(
    'ha_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['instance_id']
)

# Counter 指标
failover_total = Counter(
    'ha_failover_total',
    'Total number of failovers',
    ['from_instance', 'to_instance']
)

fallback_triggered_total = Counter(
    'ha_fallback_triggered_total',
    'Total number of fallback triggers',
    ['chain_name', 'level']
)

health_check_failed_total = Counter(
    'ha_health_check_failed_total',
    'Total number of failed health checks',
    ['instance_id', 'check_type']
)

# Histogram 指标
selection_latency_seconds = Histogram(
    'ha_selection_latency_seconds',
    'Instance selection latency',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

health_check_duration_seconds = Histogram(
    'ha_health_check_duration_seconds',
    'Health check duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

model_inference_duration_seconds = Histogram(
    'ha_model_inference_duration_seconds',
    'Model inference duration',
    ['model_id', 'provider'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# Summary 指标
instance_success_rate = Gauge(
    'ha_instance_success_rate',
    'Instance success rate over last 100 requests',
    ['instance_id']
)

active_instances = Gauge(
    'ha_active_instances',
    'Number of active instances',
    ['provider']
)

# 辅助函数
def update_instance_health_status(instance_id: str, provider: str, model: str, status: bool):
    """更新实例健康状态指标
    
    Args:
        instance_id: 实例ID
        provider: 提供商
        model: 模型
        status: 健康状态
    """
    instance_health_status.labels(
        instance_id=instance_id,
        provider=provider,
        model=model
    ).set(1 if status else 0)

def update_circuit_breaker_state(instance_id: str, state: str):
    """更新熔断器状态指标
    
    Args:
        instance_id: 实例ID
        state: 状态（closed, open, half_open）
    """
    state_map = {
        'closed': 0,
        'open': 1,
        'half_open': 2
    }
    circuit_breaker_state.labels(instance_id=instance_id).set(state_map.get(state, 0))

def increment_failover(from_instance: str, to_instance: str):
    """增加故障切换计数
    
    Args:
        from_instance: 从实例
        to_instance: 到实例
    """
    failover_total.labels(
        from_instance=from_instance,
        to_instance=to_instance
    ).inc()

def increment_fallback(chain_name: str, level: int):
    """增加降级计数
    
    Args:
        chain_name: 降级链名称
        level: 降级级别
    """
    fallback_triggered_total.labels(
        chain_name=chain_name,
        level=str(level)
    ).inc()

def increment_health_check_failure(instance_id: str, check_type: str):
    """增加健康检查失败计数
    
    Args:
        instance_id: 实例ID
        check_type: 检查类型
    """
    health_check_failed_total.labels(
        instance_id=instance_id,
        check_type=check_type
    ).inc()

def observe_selection_latency(seconds: float):
    """记录选择延迟
    
    Args:
        seconds: 延迟时间（秒）
    """
    selection_latency_seconds.observe(seconds)

def observe_health_check_duration(seconds: float):
    """记录健康检查持续时间
    
    Args:
        seconds: 持续时间（秒）
    """
    health_check_duration_seconds.observe(seconds)

def observe_model_inference_duration(model_id: str, provider: str, seconds: float):
    """记录模型推理持续时间
    
    Args:
        model_id: 模型ID
        provider: 提供商
        seconds: 持续时间（秒）
    """
    model_inference_duration_seconds.labels(
        model_id=model_id,
        provider=provider
    ).observe(seconds)

def update_instance_success_rate(instance_id: str, rate: float):
    """更新实例成功率
    
    Args:
        instance_id: 实例ID
        rate: 成功率（0-1）
    """
    instance_success_rate.labels(instance_id=instance_id).set(rate)

def update_active_instances(provider: str, count: int):
    """更新活跃实例数
    
    Args:
        provider: 提供商
        count: 实例数
    """
    active_instances.labels(provider=provider).set(count)