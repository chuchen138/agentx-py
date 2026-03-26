import importlib
import inspect
from app.domain.tool.registry import BuiltInToolRegistry
from app.domain.tool.provider import get_registered_providers

def init_builtin_tools() -> BuiltInToolRegistry:
    """初始化内置工具系统"""
    registry = BuiltInToolRegistry()
    
    # 导入所有提供者模块
    # 这里确保所有提供者模块被导入，触发装饰器注册
    try:
        # 导入RAG提供者
        from app.application.tool.providers.rag_provider import RagBuiltInToolProvider
        rag_provider = RagBuiltInToolProvider()
        registry.register_provider(rag_provider)
        
        # 导入系统提供者
        from app.application.tool.providers.system_provider import SystemBuiltInToolProvider
        system_provider = SystemBuiltInToolProvider()
        registry.register_provider(system_provider)
        
    except ImportError as e:
        print(f"Warning: Failed to import tool providers: {e}")
    
    # 打印注册信息
    tool_count = registry.get_tool_count()
    provider_count = registry.get_provider_count()
    print(f"Built-in tools initialized: {tool_count} tools from {provider_count} providers")
    
    return registry
