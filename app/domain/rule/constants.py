class RuleHandlerKey:
    """规则处理器标识常量"""
    
    # 计费规则
    MODEL_USAGE_BILLING = "model_usage_billing"  # 模型使用计费
    AGENT_CREATION_BILLING = "agent_creation_billing"  # Agent 创建计费
    API_CALL_BILLING = "api_call_billing"  # API 调用计费
    STORAGE_USAGE_BILLING = "storage_usage_billing"  # 存储使用计费
    
    # 权限规则
    FEATURE_ACCESS_PERMISSION = "feature_access_permission"  # 功能访问权限
    OPERATION_PERMISSION = "operation_permission"  # 操作权限
    DATA_ACCESS_PERMISSION = "data_access_permission"  # 数据访问权限
    
    # 业务策略
    RATE_LIMITING = "rate_limiting"  # 限流策略
    AB_TEST_ONBOARDING = "ab_test_onboarding"  # A/B 测试 - 引导流程
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断降级
