from typing import Dict, Type, Optional
from .handler import IRuleHandler
from .exceptions import RuleExecutionError


class RuleHandlerFactory:
    """规则处理器工厂"""
    _handlers: Dict[str, IRuleHandler] = {}
    
    @classmethod
    def register(cls, handler: IRuleHandler):
        """注册处理器实例"""
        cls._handlers[handler.get_handler_key()] = handler
    
    @classmethod
    def get_handler(cls, handler_key: str) -> IRuleHandler:
        """根据 handlerKey 获取处理器"""
        if handler_key not in cls._handlers:
            raise RuleExecutionError(
                f"Handler not found: {handler_key}",
                error_code="HANDLER_NOT_FOUND"
            )
        return cls._handlers[handler_key]
    
    @classmethod
    def get_all_handlers(cls) -> Dict[str, IRuleHandler]:
        """获取所有已注册的处理器"""
        return cls._handlers.copy()
