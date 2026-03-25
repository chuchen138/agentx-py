from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.domain.tool.enums import ToolType, UploadType, ToolStatus, ToolVersionStatus


class InstallCommand(BaseModel):
    command: str
    env_vars: Optional[Dict[str, str]] = None
    dependencies: Optional[List[str]] = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]


class CreateToolRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    icon: Optional[str] = None
    subtitle: Optional[str] = None
    description: str = Field(..., min_length=1)
    labels: Optional[List[str]] = None
    tool_type: ToolType = ToolType.MCP
    upload_type: UploadType = UploadType.GITHUB
    upload_url: str = Field(..., min_length=1)
    install_command: Optional[InstallCommand] = None
    tool_list: Optional[List[ToolDefinition]] = None


class UpdateToolRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    icon: Optional[str] = None
    subtitle: Optional[str] = None
    description: Optional[str] = Field(None, min_length=1)


class ToolResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    subtitle: Optional[str] = None
    description: str
    user_id: int
    labels: Optional[List[str]] = None
    tool_type: str
    upload_type: str
    upload_url: str
    install_command: Optional[InstallCommand] = None
    tool_list: Optional[List[ToolDefinition]] = None
    status: str
    is_office: bool
    reject_reason: Optional[str] = None
    failed_step_status: Optional[str] = None
    mcp_server_name: Optional[str] = None
    is_global: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolVersionRequest(BaseModel):
    tool_id: int
    version_number: str = Field(..., min_length=1)
    config: Optional[Dict[str, Any]] = None


class ToolVersionResponse(BaseModel):
    id: int
    tool_id: int
    version_number: str
    config: Optional[Dict[str, Any]] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserToolResponse(BaseModel):
    id: int
    user_id: int
    tool_id: int
    installed_at: datetime

    class Config:
        from_attributes = True


class ToolStatisticsDTO(BaseModel):
    total_tools: int
    published_tools: int
    pending_tools: int
    rejected_tools: int


class InstallToolRequest(BaseModel):
    tool_id: int


class UninstallToolRequest(BaseModel):
    tool_id: int


class ToolMarketResponse(BaseModel):
    id: int
    name: str
    icon: Optional[str] = None
    subtitle: Optional[str] = None
    description: str
    tool_type: str
    install_count: int
    is_installed: bool


class ToolReviewRequest(BaseModel):
    approve: bool
    reject_reason: Optional[str] = None


class ToolPublishRequest(BaseModel):
    version_number: str = Field(..., min_length=1)