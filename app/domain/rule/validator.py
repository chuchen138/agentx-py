import json
import ast
from typing import Dict
from .exceptions import RuleValidationError


class RuleValidator:
    """规则验证器"""
    
    # 黑名单：禁止的 Python 关键字
    FORBIDDEN_KEYWORDS = [
        'eval', 'exec', 'compile', '__import__', 
        'globals', 'locals', 'getattr', 'setattr',
        'delattr', 'vars', 'dir', 'breakpoint'
    ]
    
    # 白名单：允许的 simpleeval 函数
    ALLOWED_FUNCTIONS = ['abs', 'round', 'min', 'max', 'sum', 'len']
    
    @staticmethod
    def validate_config(config: Dict) -> None:
        """验证规则配置安全性"""
        config_str = json.dumps(config)
        
        # 检查黑名单关键字
        for keyword in RuleValidator.FORBIDDEN_KEYWORDS:
            if keyword in config_str:
                raise RuleValidationError(
                    f"Forbidden keyword detected: {keyword}",
                    error_code="SECURITY_VIOLATION"
                )
        
        # 如果需要使用表达式，限制使用 simpleeval
        if "expression" in config:
            RuleValidator._validate_expression(config["expression"])
    
    @staticmethod
    def _validate_expression(expr: str) -> None:
        """验证表达式安全性"""
        try:
            # 解析表达式，检查是否包含危险操作
            tree = ast.parse(expr, mode='eval')
            # 遍历 AST，检查节点类型
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # 检查调用的函数是否在白名单中
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in RuleValidator.ALLOWED_FUNCTIONS:
                            raise RuleValidationError(
                                f"Function not allowed: {node.func.id}"
                            )
        except Exception as e:
            raise RuleValidationError(f"Invalid expression: {str(e)}")
