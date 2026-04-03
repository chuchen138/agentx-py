from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
from pydantic import BaseModel
from ..exceptions import RuleExecutionError


class RuleContext(BaseModel):
    """规则执行上下文"""
    user_id: str
    action: str
    resource: Optional[str] = None
    metadata: Dict[str, Any] = {}


class RuleResult(BaseModel):
    """规则执行结果"""
    allowed: bool
    reason: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None


class IRuleHandler(ABC):
    """规则处理器接口"""
    
    @abstractmethod
    def get_handler_key(self) -> str:
        """返回处理器标识"""
        pass
    
    @abstractmethod
    async def execute(self, context: RuleContext, rule_config: Dict) -> RuleResult:
        """
        执行规则
        
        Args:
            context: 规则执行上下文
            rule_config: 规则配置（JSON 格式）
        
        Returns:
            RuleResult: 规则执行结果
        
        Raises:
            RuleExecutionError: 规则执行失败
        """
        pass


# 装饰器定义
def rule_handler(handler_key: str):
    """规则处理器注册装饰器"""
    def decorator(cls: Type[IRuleHandler]) -> Type[IRuleHandler]:
        from ..factory import RuleHandlerFactory
        RuleHandlerFactory.register(cls())
        return cls
    return decorator


# 自动发现处理器
import importlib
import pkgutil

def auto_discover_handlers():
    """自动发现并注册所有规则处理器"""
    package = importlib.import_module("app.domain.rule.handler")
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if is_pkg or name.endswith(".builtin"):
            importlib.import_module(name)
