import threading
from typing import Dict, Optional, List, Set
from functools import lru_cache
from app.domain.tool.models import ToolDefinition
from app.domain.tool.provider import BuiltInToolProvider

class BuiltInToolRegistry:
    """工具注册表（单例模式）"""
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._providers: List[BuiltInToolProvider] = []
        self._blacklist: Set[str] = set()
        self._lock = threading.RLock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_tool(self, tool_def: ToolDefinition) -> None:
        """注册工具到注册表"""
        with self._lock:
            if tool_def.name in self._tools:
                existing = self._tools[tool_def.name]
                if existing.version != tool_def.version:
                    # 版本冲突，保留最新版本
                    self._tools[tool_def.name] = tool_def
            else:
                self._tools[tool_def.name] = tool_def
    
    def register_provider(self, provider: BuiltInToolProvider) -> None:
        """注册提供者"""
        with self._lock:
            if provider not in self._providers:
                self._providers.append(provider)
                # 自动注册提供者的所有工具
                for tool_class in provider.get_tools():
                    tool_def = tool_class.to_definition()
                    # 调用model_rebuild()确保Pydantic模型完全定义
                    tool_def.model_rebuild()
                    self.register_tool(tool_def)
    
    @lru_cache(maxsize=1000)
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """根据工具名称获取工具定义"""
        with self._lock:
            return self._tools.get(tool_name)
    
    def list_tools(self, filters: dict = None) -> List[ToolDefinition]:
        """查询工具列表"""
        with self._lock:
            tools = list(self._tools.values())
            if filters:
                if 'type' in filters:
                    tools = [t for t in tools if t.tool_type == filters['type']]
                if 'tags' in filters:
                    tags = filters['tags']
                    tools = [t for t in tools if any(tag in t.tags for tag in tags)]
                if 'provider_id' in filters:
                    tools = [t for t in tools if t.provider_id == filters['provider_id']]
            return tools
    
    def enable_tool(self, tool_name: str) -> None:
        """启用工具"""
        with self._lock:
            if tool_name in self._blacklist:
                self._blacklist.remove(tool_name)
    
    def disable_tool(self, tool_name: str) -> None:
        """禁用工具"""
        with self._lock:
            if tool_name in self._tools:
                self._blacklist.add(tool_name)
    
    def is_blacklisted(self, tool_name: str) -> bool:
        """检查工具是否在黑名单中"""
        return tool_name in self._blacklist
    
    def get_providers(self) -> List[BuiltInToolProvider]:
        """获取所有提供者"""
        return self._providers
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self.get_tool.cache_clear()
    
    def get_tool_count(self) -> int:
        """获取工具数量"""
        return len(self._tools)
    
    def get_provider_count(self) -> int:
        """获取提供者数量"""
        return len(self._providers)
