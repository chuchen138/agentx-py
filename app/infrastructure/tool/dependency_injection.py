from fastapi import Depends
from app.domain.tool.registry import BuiltInToolRegistry
from app.domain.tool.executor import DefaultToolExecutor
from app.infrastructure.tool.config import tool_settings
from app.application.tool.providers import rag_provider, system_provider

def get_tool_registry() -> BuiltInToolRegistry:
    """获取工具注册表实例"""
    registry = BuiltInToolRegistry()
    # 注册所有提供者
    # 注意：由于装饰器的作用，提供者已经在模块导入时注册
    # 这里需要确保所有提供者模块被导入
    return registry

def get_tool_executor(registry: BuiltInToolRegistry = Depends(get_tool_registry)) -> DefaultToolExecutor:
    """获取工具执行器实例"""
    return DefaultToolExecutor(
        registry=registry,
        timeout=tool_settings.tool_timeout,
        max_concurrency=tool_settings.max_concurrency
    )
