from typing import Optional


class RuleExecutionError(Exception):
    """规则执行异常"""
    def __init__(self, message: str, error_code: str, rule_id: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.rule_id = rule_id
        super().__init__(self.message)


class RuleValidationError(Exception):
    """规则验证异常"""
    pass


class ConcurrencyError(Exception):
    """并发冲突异常"""
    pass
