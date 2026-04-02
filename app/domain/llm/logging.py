import structlog
import logging
import sys

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.stdlib.render_to_log_kwargs,
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

# 创建根日志记录器
root_logger = structlog.get_logger()

# 配置标准日志
logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=logging.INFO,
)

# 创建特定模块的日志记录器
def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """获取日志记录器
    
    Args:
        name: 模块名称
    
    Returns:
        structlog.stdlib.BoundLogger: 日志记录器
    """
    return structlog.get_logger(name)

# 日志记录器实例
high_availability_logger = get_logger("high_availability")
circuit_breaker_logger = get_logger("circuit_breaker")
health_check_logger = get_logger("health_check")
fallback_logger = get_logger("fallback")
alert_logger = get_logger("alert")
gateway_logger = get_logger("gateway")

# 日志记录辅助函数
def log_model_synced(model_id: str, provider: str, duration_ms: float):
    """记录模型同步日志
    
    Args:
        model_id: 模型ID
        provider: 提供商
        duration_ms: 同步时间（毫秒）
    """
    high_availability_logger.info(
        "model_synced_to_gateway",
        model_id=model_id,
        provider=provider,
        success=True,
        duration_ms=duration_ms
    )

def log_failover_triggered(from_instance: str, to_instance: str, reason: str, consecutive_failures: int):
    """记录故障切换日志
    
    Args:
        from_instance: 从实例
        to_instance: 到实例
        reason: 切换原因
        consecutive_failures: 连续失败次数
    """
    high_availability_logger.warning(
        "failover_triggered",
        from_instance=from_instance,
        to_instance=to_instance,
        reason=reason,
        consecutive_failures=consecutive_failures
    )

def log_fallback_triggered(chain_name: str, from_model: str, to_model: str, trigger_reason: str):
    """记录降级日志
    
    Args:
        chain_name: 降级链名称
        from_model: 从模型
        to_model: 到模型
        trigger_reason: 触发原因
    """
    fallback_logger.info(
        "fallback_triggered",
        chain_name=chain_name,
        from_model=from_model,
        to_model=to_model,
        trigger_reason=trigger_reason
    )

def log_circuit_breaker_opened(instance_id: str, failure_rate: float, consecutive_failures: int):
    """记录熔断器打开日志
    
    Args:
        instance_id: 实例ID
        failure_rate: 错误率
        consecutive_failures: 连续失败次数
    """
    circuit_breaker_logger.warning(
        "circuit_breaker_opened",
        instance_id=instance_id,
        failure_rate=failure_rate,
        consecutive_failures=consecutive_failures
    )

def log_health_check_failed(instance_id: str, check_type: str, error: str):
    """记录健康检查失败日志
    
    Args:
        instance_id: 实例ID
        check_type: 检查类型
        error: 错误信息
    """
    health_check_logger.warning(
        "health_check_failed",
        instance_id=instance_id,
        check_type=check_type,
        error=error
    )

def log_alert_sent(level: str, title: str, source: str):
    """记录告警发送日志
    
    Args:
        level: 告警级别
        title: 告警标题
        source: 告警来源
    """
    alert_logger.info(
        "alert_sent",
        level=level,
        title=title,
        source=source
    )

def log_gateway_request(path: str, method: str, status_code: int, duration_ms: float):
    """记录网关请求日志
    
    Args:
        path: 请求路径
        method: 请求方法
        status_code: 状态码
        duration_ms: 持续时间（毫秒）
    """
    gateway_logger.info(
        "gateway_request",
        path=path,
        method=method,
        status_code=status_code,
        duration_ms=duration_ms
    )