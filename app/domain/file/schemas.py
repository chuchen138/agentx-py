from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class FileRecordBase(BaseModel):
    """文件记录基础模型"""
    file_type: str
    original_filename: str
    stored_filename: str
    file_path: str
    file_url: str
    file_size: int
    mime_type: str
    storage_backend: str
    version: int = 1
    file_metadata: Dict[str, Any] = Field(default_factory=dict)


class FileRecordCreate(FileRecordBase):
    """创建文件记录模型"""
    user_id: UUID


class FileRecordUpdate(BaseModel):
    """更新文件记录模型"""
    original_filename: Optional[str] = None
    stored_filename: Optional[str] = None
    file_path: Optional[str] = None
    file_url: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    storage_backend: Optional[str] = None
    version: Optional[int] = None
    file_metadata: Optional[Dict[str, Any]] = None


class FileRecordResponse(FileRecordBase):
    """文件记录响应模型"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
    deleted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    file_id: UUID
    file_url: str
    file_name: str
    file_size: int
    mime_type: str


class FileURLResponse(BaseModel):
    """文件URL响应模型"""
    file_url: str
    expires_at: Optional[datetime] = None
