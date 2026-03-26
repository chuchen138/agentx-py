from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from app.domain.tool.registry import BuiltInToolRegistry
from app.domain.tool.executor import DefaultToolExecutor, ToolResult
from app.infrastructure.tool.dependency_injection import get_tool_registry, get_tool_executor

router = APIRouter(prefix="/api/v1/tools", tags=["tools"])

@router.get("/builtin/list")
async def list_builtin_tools(
    tool_type: str = None,
    tags: str = None,
    registry: BuiltInToolRegistry = Depends(get_tool_registry)
):
    """列出所有内置工具"""
    filters = {}
    if tool_type:
        filters['type'] = tool_type
    if tags:
        filters['tags'] = tags.split(',')
    
    tools = registry.list_tools(filters)
    return [{
        "name": tool.name,
        "description": tool.description,
        "type": tool.tool_type.value,
        "version": tool.version,
        "provider_id": tool.provider_id,
        "tags": tool.tags,
        "permission": tool.permission.value
    } for tool in tools]

@router.get("/builtin/{tool_name}")
async def get_builtin_tool(
    tool_name: str,
    registry: BuiltInToolRegistry = Depends(get_tool_registry)
):
    """获取指定工具的详细信息"""
    tool = registry.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    return {
        "name": tool.name,
        "description": tool.description,
        "type": tool.tool_type.value,
        "version": tool.version,
        "provider_id": tool.provider_id,
        "tags": tool.tags,
        "permission": tool.permission.value,
        "parameters": tool.parameters.model_json_schema(),
        "output": tool.output
    }

@router.post("/builtin/execute/{tool_name}")
async def execute_builtin_tool(
    tool_name: str,
    params: dict,
    executor: DefaultToolExecutor = Depends(get_tool_executor)
):
    """执行内置工具"""
    result = await executor.execute(tool_name, params)
    return result.model_dump()

@router.post("/builtin/execute/batch")
async def execute_builtin_tools_batch(
    tool_calls: List[Dict[str, Any]],
    executor: DefaultToolExecutor = Depends(get_tool_executor)
):
    """批量执行内置工具"""
    results = await executor.execute_batch(tool_calls)
    return [
        r.model_dump() if hasattr(r, 'model_dump') else str(r)
        for r in results
    ]

@router.post("/builtin/{tool_name}/disable")
async def disable_builtin_tool(
    tool_name: str,
    registry: BuiltInToolRegistry = Depends(get_tool_registry)
):
    """禁用内置工具"""
    registry.disable_tool(tool_name)
    return {"message": f"Tool '{tool_name}' disabled successfully"}

@router.post("/builtin/{tool_name}/enable")
async def enable_builtin_tool(
    tool_name: str,
    registry: BuiltInToolRegistry = Depends(get_tool_registry)
):
    """启用内置工具"""
    registry.enable_tool(tool_name)
    return {"message": f"Tool '{tool_name}' enabled successfully"}
