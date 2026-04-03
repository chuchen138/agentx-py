import pytest
from app.domain.rule.handler import RuleContext, RuleResult
from app.domain.rule.handler.builtin.billing import ModelUsageBillingHandler
from app.domain.rule.handler.builtin.permission import FeatureAccessPermissionHandler


@pytest.mark.asyncio
async def test_model_usage_billing_handler():
    """测试模型使用计费处理器"""
    handler = ModelUsageBillingHandler()
    
    # 测试正常计费
    context = RuleContext(
        user_id="user-123",
        action="model_inference",
        metadata={
            "usage_data": {
                "input_tokens": 1000,
                "output_tokens": 500
            }
        }
    )
    
    config = {
        "input_price_per_1k_tokens": 0.03,
        "output_price_per_1k_tokens": 0.06,
        "currency": "USD",
        "min_charge": 0.001
    }
    
    result = await handler.execute(context, config)
    
    assert result.allowed is True
    assert result.reason == "Billing calculated successfully"
    assert "cost" in result.data
    assert result.data["cost"] == 0.06  # 1000输入 * 0.03 + 500输出 * 0.06
    assert result.data["currency"] == "USD"
    
    # 测试最小费用
    context2 = RuleContext(
        user_id="user-123",
        action="model_inference",
        metadata={
            "usage_data": {
                "input_tokens": 10,
                "output_tokens": 10
            }
        }
    )
    
    result2 = await handler.execute(context2, config)
    assert result2.data["cost"] == 0.001  # 低于最小费用


@pytest.mark.asyncio
async def test_feature_access_permission_handler():
    """测试功能访问权限处理器"""
    handler = FeatureAccessPermissionHandler()
    
    # 测试权限不足
    context = RuleContext(
        user_id="user-123",
        action="access_feature",
        metadata={"user_level": "free"}
    )
    
    config = {"required_level": "pro"}
    
    result = await handler.execute(context, config)
    
    assert result.allowed is False
    assert result.reason == "Insufficient permission level"
    assert result.data["user_level"] == "free"
    assert result.data["required_level"] == "pro"
    
    # 测试权限足够
    context2 = RuleContext(
        user_id="user-123",
        action="access_feature",
        metadata={"user_level": "enterprise"}
    )
    
    result2 = await handler.execute(context2, config)
    
    assert result2.allowed is True
    assert result2.reason == "Access granted"
    assert result2.data["user_level"] == "enterprise"
    assert result2.data["required_level"] == "pro"
