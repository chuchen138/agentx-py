from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from app.domain.llm.enums import ProviderProtocol, ModelType


class ProviderEntity(BaseModel):
    """服务商实体"""
    id: str = Field(..., description="服务商 ID")
    user_id: str = Field(..., description="用户 ID")
    protocol: ProviderProtocol = Field(..., description="协议类型")
    name: str = Field(..., description="服务商名称")
    description: Optional[str] = Field(None, description="描述")
    config: str = Field(..., description="配置（加密）")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")


class ModelEntity(BaseModel):
    """模型实体"""
    id: str = Field(..., description="模型 ID")
    user_id: str = Field(..., description="用户 ID")
    provider_id: str = Field(..., description="服务商 ID")
    model_id: str = Field(..., description="模型标识")
    name: str = Field(..., description="模型名称")
    description: Optional[str] = Field(None, description="描述")
    model_endpoint: Optional[str] = Field(None, description="模型部署名称")
    type: ModelType = Field(..., description="模型类型")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")
    deleted_at: Optional[datetime] = Field(None, description="删除时间")
