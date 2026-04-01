from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class Tool(ABC):
    """工具基类"""
    
    @abstractmethod
    def name(self) -> str:
        """工具名称"""
        pass
    
    @abstractmethod
    def description(self) -> str:
        """工具描述"""
        pass
    
    @abstractmethod
    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具"""
        pass


class ToolRegistry:
    """工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self._tools[tool.name()] = tool
    
    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """获取工具"""
        return self._tools.get(tool_name)
    
    def list_tools(self) -> List[str]:
        """列出所有工具"""
        return list(self._tools.keys())


class PermissionService:
    """权限服务"""
    
    def verify_permission(self, user_id: str, tool_name: str) -> bool:
        """验证用户是否有权限使用工具"""
        # 这里应该实现权限验证逻辑
        # 暂时返回True
        return True


class ToolManager:
    """工具管理器"""
    
    def __init__(self, tool_registry: ToolRegistry, permission_service: PermissionService):
        self._tool_registry = tool_registry
        self._permission_service = permission_service
        self._tool_blacklist = set()  # 工具黑名单
    
    def register_tool(self, tool: Tool):
        """注册工具"""
        self._tool_registry.register_tool(tool)
    
    def select_tool(self, task_requirement: Dict[str, Any]) -> Optional[Tool]:
        """选择工具"""
        required_tool = task_requirement.get("tool_name")
        if required_tool:
            return self._tool_registry.get_tool(required_tool)
        
        # 根据任务需求选择合适的工具
        task_type = task_requirement.get("task_type")
        if task_type == "DATA_ANALYSIS":
            return self._tool_registry.get_tool("data_analyzer")
        elif task_type == "INFORMATION_RETRIEVAL":
            return self._tool_registry.get_tool("information_retriever")
        
        return None
    
    def verify_permission(self, user_id: str, tool_name: str) -> bool:
        """验证权限"""
        if tool_name in self._tool_blacklist:
            return False
        return self._permission_service.verify_permission(user_id, tool_name)
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """调用工具"""
        tool = self._tool_registry.get_tool(tool_name)
        if not tool:
            return {"error": f"Tool {tool_name} not found"}
        
        try:
            result = tool.execute(arguments)
            return {"result": result, "status": "success"}
        except Exception as e:
            return {"error": str(e), "status": "error"}
    
    def parse_tool_result(self, tool_result: Dict[str, Any]) -> Dict[str, Any]:
        """解析工具结果"""
        if tool_result.get("status") == "success":
            return tool_result.get("result", {})
        return {"error": tool_result.get("error", "Tool execution failed")}
    
    def handle_tool_error(self, error: Exception) -> Dict[str, Any]:
        """处理工具错误"""
        return {"error": str(error), "status": "error"}
    
    def add_to_blacklist(self, tool_name: str):
        """添加工具到黑名单"""
        self._tool_blacklist.add(tool_name)
    
    def remove_from_blacklist(self, tool_name: str):
        """从黑名单移除工具"""
        if tool_name in self._tool_blacklist:
            self._tool_blacklist.remove(tool_name)
