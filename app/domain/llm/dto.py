from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.domain.llm.enums import ProviderProtocol, ModelType, ProviderType
from app.domain.llm.config import ProviderConfig


class ProviderBase(BaseModel):
    """服务商基础DTO"""
    name: str = Field(..., description="服务商名称")
    protocol: ProviderProtocol = Field(..., description="协议类型")
    description: Optional[str] = Field(None, description="描述")
    config: ProviderConfig = Field(..., description="配置")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")


class ProviderCreateDTO(ProviderBase):
    """创建服务商DTO"""
    pass


class ProviderUpdateDTO(BaseModel):
    """更新服务商DTO"""
    name: Optional[str] = Field(None, description="服务商名称")
    description: Optional[str] = Field(None, description="描述")
    config: Optional[ProviderConfig] = Field(None, description="配置")
    status: Optional[bool] = Field(None, description="状态")


class ModelBase(BaseModel):
    """模型基础DTO"""
    provider_id: str = Field(..., description="服务商 ID")
    model_id: str = Field(..., description="模型标识")
    name: str = Field(..., description="模型名称")
    description: Optional[str] = Field(None, description="描述")
    model_endpoint: Optional[str] = Field(None, description="模型部署名称")
    type: ModelType = Field(..., description="模型类型")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")


class ModelCreateDTO(ModelBase):
    """创建模型DTO"""
    pass


class ModelUpdateDTO(BaseModel):
    """更新模型DTO"""
    name: Optional[str] = Field(None, description="模型名称")
    description: Optional[str] = Field(None, description="描述")
    model_endpoint: Optional[str] = Field(None, description="模型部署名称")
    status: Optional[bool] = Field(None, description="状态")


class ModelDTO(BaseModel):
    """模型DTO"""
    id: str = Field(..., description="模型 ID")
    provider_id: str = Field(..., description="服务商 ID")
    model_id: str = Field(..., description="模型标识")
    name: str = Field(..., description="模型名称")
    description: Optional[str] = Field(None, description="描述")
    model_endpoint: Optional[str] = Field(None, description="模型部署名称")
    type: ModelType = Field(..., description="模型类型")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")


class ProviderDTO(BaseModel):
    """服务商DTO"""
    id: str = Field(..., description="服务商 ID")
    name: str = Field(..., description="服务商名称")
    protocol: ProviderProtocol = Field(..., description="协议类型")
    description: Optional[str] = Field(None, description="描述")
    is_official: bool = Field(False, description="是否官方")
    status: bool = Field(True, description="状态")
    config: ProviderConfig = Field(..., description="配置")
    models: List[ModelDTO] = Field(default_factory=list, description="模型列表")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
