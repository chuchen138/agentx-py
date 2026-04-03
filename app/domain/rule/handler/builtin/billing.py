from .. import IRuleHandler, RuleContext, RuleResult, rule_handler
from ...constants import RuleHandlerKey


@rule_handler(RuleHandlerKey.MODEL_USAGE_BILLING)
class ModelUsageBillingHandler(IRuleHandler):
    """模型使用计费处理器"""
    
    def get_handler_key(self) -> str:
        return RuleHandlerKey.MODEL_USAGE_BILLING
    
    async def execute(self, context: RuleContext, rule_config: dict) -> RuleResult:
        """执行计费规则"""
        usage_data = context.metadata.get("usage_data", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        
        input_price = rule_config.get("input_price_per_1k_tokens", 0.03)
        output_price = rule_config.get("output_price_per_1k_tokens", 0.06)
        
        cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        cost = max(cost, rule_config.get("min_charge", 0.001))
        
        return RuleResult(
            allowed=True,
            reason="Billing calculated successfully",
            data={
                "cost": cost,
                "currency": rule_config.get("currency", "USD"),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens
            }
        )
