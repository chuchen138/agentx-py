from abc import ABC, abstractmethod
import asyncio
import time
from typing import Dict, Any
from pydantic import ValidationError
from app.domain.tool.registry import BuiltInToolRegistry
from app.domain.tool.models import ToolResult

class ToolExecutor(ABC):
    @abstractmethod
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        """执行工具调用"""
        pass
    
    @abstractmethod
    def validate_parameters(self, tool_name: str, params: dict) -> bool:
        """验证参数合法性"""
        pass

class ToolNotFoundException(Exception):
    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' not found")

class InvalidParameterException(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class ToolExecutionException(Exception):
    def __init__(self, tool_name: str, message: str):
        super().__init__(f"Tool '{tool_name}' execution failed: {message}")

class ToolTimeoutException(Exception):
    def __init__(self, tool_name: str):
        super().__init__(f"Tool '{tool_name}' execution timed out")

class PermissionDeniedException(Exception):
    def __init__(self, tool_name: str):
        super().__init__(f"Permission denied for tool '{tool_name}'")

class DefaultToolExecutor(ToolExecutor):
    def __init__(self, registry: BuiltInToolRegistry, timeout: int = 30, max_concurrency: int = 100):
        self.registry = registry
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        # 1. 检查黑名单
        if self.registry.is_blacklisted(tool_name):
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is blacklisted",
                duration=0
            )
        
        # 2. 获取工具定义
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' not found",
                duration=0
            )
        
        # 3. 验证参数
        try:
            self.validate_parameters(tool_name, params)
        except InvalidParameterException as e:
            return ToolResult(
                success=False,
                error=str(e),
                duration=0
            )
        
        # 4. 执行工具（带超时控制）
        start_time = time.time()
        try:
            async with self.semaphore:
                result = await asyncio.wait_for(
                    tool_def.execute(params),
                    timeout=self.timeout
                )
                duration = time.time() - start_time
                return ToolResult(
                    success=True,
                    data=result,
                    duration=duration
                )
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                error=f"Tool execution timed out after {self.timeout} seconds",
                duration=duration
            )
        except Exception as e:
            duration = time.time() - start_time
            return ToolResult(
                success=False,
                error=str(e),
                duration=duration
            )
    
    def validate_parameters(self, tool_name: str, params: dict) -> bool:
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            raise ToolNotFoundException(tool_name)
        
        try:
            tool_def.parameters(**params)
            return True
        except ValidationError as e:
            raise InvalidParameterException(str(e))
    
    async def execute_batch(self, tool_calls: list) -> list:
        """批量执行工具调用"""
        tasks = []
        for call in tool_calls:
            task = self.execute(call['tool_name'], call.get('params', {}))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
