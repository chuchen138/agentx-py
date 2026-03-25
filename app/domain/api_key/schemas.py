from __future__ import annotations
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID


class ApiKeyBase(BaseModel):
    agent_id: UUID
    name: str = Field(..., min_length=1, max_length=100)


class ApiKeyCreate(ApiKeyBase):
    pass


class ApiKeyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    status: Optional[bool] = None


class ApiKeyStatusUpdate(BaseModel):
    status: bool


class ApiKeyResponse(BaseModel):
    id: UUID
    api_key: Optional[str] = None  # 仅创建时返回
    agent_id: UUID
    agent_name: Optional[str] = None
    user_id: UUID
    name: str
    status: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_expired: bool
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ApiKeyListResponse(BaseModel):
    id: UUID
    api_key: str  # 脱敏显示
    agent_id: UUID
    agent_name: Optional[str] = None
    name: str
    status: bool
    usage_count: int
    last_used_at: Optional[datetime] = None
    is_expired: bool
    is_available: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApiKeyValidationResponse(BaseModel):
    valid: bool
    user_id: Optional[UUID] = None
    agent_id: Optional[UUID] = None
    message: Optional[str] = None


class ApiKeyResetResponse(BaseModel):
    id: UUID
    new_api_key: str
    message: str
