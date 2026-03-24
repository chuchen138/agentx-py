from pydantic import BaseModel
from app.domain.llm.entities import ModelEntity
from typing import List


class BaseEvent(BaseModel):
    """基础事件"""
    event_type: str
    timestamp: float


class ModelCreatedEvent(BaseEvent):
    """模型创建事件"""
    model: ModelEntity


class ModelUpdatedEvent(BaseEvent):
    """模型更新事件"""
    model: ModelEntity


class ModelDeletedEvent(BaseEvent):
    """模型删除事件"""
    model_id: str


class ModelStatusChangedEvent(BaseEvent):
    """模型状态变更事件"""
    model_id: str
    status: bool


class ModelsBatchDeletedEvent(BaseEvent):
    """批量删除模型事件"""
    model_ids: List[str]
