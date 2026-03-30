from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON, ARRAY
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime

# 自定义UUID类型，兼容SQLite
from app.domain.user.model import UUID

# 基础模型基类
from app.core.database import Base

# 记忆类型枚举
from app.domain.memory.constant.memory_type import MemoryType

# SQLAlchemy ORM 模型
class MemoryItemModel(Base):
    __tablename__ = "memory_items"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(String(64), nullable=False, index=True)
    type = Column(String(20), nullable=False, index=True)  # PROFILE/TASK/FACT/EPISODIC
    text = Column(Text, nullable=False)
    data = Column(JSONB, nullable=True, default={})
    importance = Column(Float, nullable=False, default=0.0)
    tags = Column(ARRAY(String), nullable=True, default=[])
    source_session_id = Column(String(64), nullable=True)
    dedupe_hash = Column(String(64), nullable=False, index=True)
    status = Column(Integer, nullable=False, default=1)  # 1=active, 0=archived
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)

class MemoryVectorStoreModel(Base):
    __tablename__ = "memory_vector_store"
    
    embedding_id = Column(UUID, primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID, ForeignKey("memory_items.id", ondelete="CASCADE"), nullable=False, index=True)
    embedding = Column("embedding", ARRAY(Float), nullable=False)  # 向量数据
    text = Column(Text, nullable=False)  # 冗余文本字段
    metadata = Column(JSONB, nullable=False, default={})  # 元数据
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    memory_item = relationship("MemoryItemModel", backref="vector_store")

# Pydantic 数据模型
class MemoryItemBase(BaseModel):
    type: str = Field(..., description="记忆类型")
    text: str = Field(..., description="记忆文本内容")
    importance: float = Field(..., ge=0.0, le=1.0, description="重要性评分")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    data: Dict[str, Any] = Field(default_factory=dict, description="结构化数据")

class MemoryItemCreate(MemoryItemBase):
    source_session_id: Optional[str] = Field(None, description="来源会话ID")

class MemoryItemUpdate(BaseModel):
    type: Optional[str] = Field(None, description="记忆类型")
    text: Optional[str] = Field(None, description="记忆文本内容")
    importance: Optional[float] = Field(None, ge=0.0, le=1.0, description="重要性评分")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    data: Optional[Dict[str, Any]] = Field(None, description="结构化数据")
    status: Optional[int] = Field(None, description="状态")

class MemoryItemDTO(BaseModel):
    id: uuid.UUID
    user_id: str
    type: str
    text: str
    data: Dict[str, Any]
    importance: float
    tags: List[str]
    source_session_id: Optional[str]
    status: int
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)

class CandidateMemory(BaseModel):
    type: str
    text: str
    importance: float
    tags: List[str]
    data: Dict[str, Any] = Field(default_factory=dict)

class MemoryResult(BaseModel):
    itemId: uuid.UUID
    type: str
    text: str
    importance: float
    tags: List[str]
    score: float

class QueryMemoryRequest(BaseModel):
    page: int = Field(default=1, ge=1, description="页码")
    pageSize: int = Field(default=20, ge=1, le=100, description="每页大小")
    type: Optional[str] = Field(None, description="记忆类型")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    importanceMin: Optional[float] = Field(None, ge=0.0, le=1.0, description="最小重要性")

class CreateMemoryRequest(BaseModel):
    type: str = Field(..., description="记忆类型")
    text: str = Field(..., description="记忆文本内容")
    importance: float = Field(..., ge=0.0, le=1.0, description="重要性评分")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    data: Dict[str, Any] = Field(default_factory=dict, description="结构化数据")
