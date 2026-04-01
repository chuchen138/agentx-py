from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Dict, Any


class WorkflowCreateRequest(BaseModel):
    session_id: str
    user_id: str
    agent_id: str


class WorkflowDTO(BaseModel):
    id: str
    workflow_id: str
    session_id: str
    user_id: str
    agent_id: str
    status: str
    current_state: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WorkflowListRequest(BaseModel):
    page: int = Field(default=1, ge=1)
    size: int = Field(default=10, ge=1, le=100)
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class TaskCreateRequest(BaseModel):
    workflow_id: str
    task_name: str
    task_type: str
    description: Optional[str] = None
    priority: int = 0
    depends_on: List[str] = []


class TaskUpdateRequest(BaseModel):
    status: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class TaskDTO(BaseModel):
    id: str
    task_id: str
    workflow_id: str
    parent_task_id: Optional[str] = None
    task_name: str
    task_type: str
    description: Optional[str] = None
    status: str
    priority: int
    depends_on: List[str]
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TaskStatusDTO(BaseModel):
    task_id: str
    status: str
    error_message: Optional[str] = None


class WorkflowEventDTO(BaseModel):
    id: str
    event_id: str
    workflow_id: str
    event_type: str
    event_data: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SummaryDTO(BaseModel):
    id: str
    summary_id: str
    session_id: str
    workflow_id: Optional[str] = None
    summary_text: str
    token_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True
