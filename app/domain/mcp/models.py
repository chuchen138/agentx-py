from typing import Dict, List, Optional
from pydantic import BaseModel


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict
    output_schema: Optional[Dict] = None
    is_global: bool = False


class ContainerInfo(BaseModel):
    container_id: str
    name: str
    status: str
    host: str
    port: int
    env_vars: Dict[str, str] = {}


class MCPToolCall(BaseModel):
    tool_name: str
    args: Dict
    idempotency_key: str


class MCPToolResult(BaseModel):
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
