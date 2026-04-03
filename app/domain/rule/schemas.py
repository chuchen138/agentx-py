from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class RuleCreate(BaseModel):
    """创建规则请求"""
    name: str = Field(..., description="规则名称")
    handlerKey: str = Field(..., description="规则处理器标识")
    description: Optional[str] = Field(None, description="规则描述")
    config: Dict[str, Any] = Field(default_factory=dict, description="规则配置")
    priority: int = Field(default=0, description="优先级")


class RuleUpdate(BaseModel):
    """更新规则请求"""
    name: Optional[str] = Field(None, description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    config: Optional[Dict[str, Any]] = Field(None, description="规则配置")
    priority: Optional[int] = Field(None, description="优先级")


class RuleToggle(BaseModel):
    """启用/禁用规则请求"""
    enabled: bool = Field(..., description="是否启用")
    reason: Optional[str] = Field(None, description="操作原因")


class RuleRollback(BaseModel):
    """回滚规则请求"""
    reason: str = Field(..., description="回滚原因")


class RuleResponse(BaseModel):
    """规则响应"""
    id: str
    name: str
    handlerKey: str
    description: Optional[str]
    config: Dict[str, Any]
    enabled: bool
    priority: int
    version: int
    createdAt: datetime
    updatedAt: datetime
    updatedBy: Optional[str]
    
    class Config:
        from_attributes = True


class RuleListResponse(BaseModel):
    """规则列表响应"""
    records: List[Dict[str, Any]]
    current: int
    size: int
    total: int


class RuleVersion(BaseModel):
    """规则版本"""
    version: int
    snapshot: Dict[str, Any]
    changed_by: Optional[str]
    changed_at: datetime
    change_reason: Optional[str]


class RuleVersionsResponse(BaseModel):
    """规则版本列表响应"""
    versions: List[RuleVersion]


class RuleExecuteRequest(BaseModel):
    """执行规则请求"""
    ruleId: str = Field(..., description="规则ID")
    context: Dict[str, Any] = Field(..., description="执行上下文")


class RuleExecuteResponse(BaseModel):
    """执行规则响应"""
    allowed: bool
    reason: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
