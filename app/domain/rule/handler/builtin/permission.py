from .. import IRuleHandler, RuleContext, RuleResult, rule_handler
from ...constants import RuleHandlerKey


@rule_handler(RuleHandlerKey.FEATURE_ACCESS_PERMISSION)
class FeatureAccessPermissionHandler(IRuleHandler):
    """功能访问权限处理器"""
    
    def get_handler_key(self) -> str:
        return RuleHandlerKey.FEATURE_ACCESS_PERMISSION
    
    async def execute(self, context: RuleContext, rule_config: dict) -> RuleResult:
        """执行权限规则"""
        user_level = context.metadata.get("user_level", "normal")
        required_level = rule_config.get("required_level", "normal")
        
        # 权限等级映射
        level_map = {
            "free": 0,
            "basic": 1,
            "pro": 2,
            "enterprise": 3
        }
        
        user_level_value = level_map.get(user_level, 0)
        required_level_value = level_map.get(required_level, 0)
        
        allowed = user_level_value >= required_level_value
        
        if allowed:
            return RuleResult(
                allowed=True,
                reason="Access granted",
                data={
                    "user_level": user_level,
                    "required_level": required_level
                }
            )
        else:
            return RuleResult(
                allowed=False,
                reason="Insufficient permission level",
                data={
                    "user_level": user_level,
                    "required_level": required_level
                }
            )
