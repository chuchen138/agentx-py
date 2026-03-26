from abc import ABC, abstractmethod
from typing import List, Type, Optional
from functools import wraps
from app.domain.tool.models import BaseTool

class BuiltInToolProvider(ABC):
    """工具提供者抽象基类"""
    
    @abstractmethod
    def get_tools(self) -> List[Type[BaseTool]]:
        """获取该提供者提供的所有工具类"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名称"""
        pass
    
    def get_tool(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """根据工具名称获取工具类"""
        for tool_class in self.get_tools():
            if tool_class.__name__.lower() == tool_name.lower():
                return tool_class
        return None

# 全局提供者注册表
_registered_providers = []

def register_provider(provider_class: Type[BuiltInToolProvider]) -> Type[BuiltInToolProvider]:
    """工具提供者注册装饰器"""
    @wraps(provider_class)
    def wrapper(*args, **kwargs):
        instance = provider_class(*args, **kwargs)
        _registered_providers.append(instance)
        return instance
    return wrapper

def get_registered_providers() -> List[BuiltInToolProvider]:
    """获取所有已注册的提供者"""
    return _registered_providers
