from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.domain.scheduledtask.constant import RepeatType, ScheduleTaskStatus


class RepeatConfigSchema(BaseModel):
    """重复配置 Schema"""
    interval_hours: Optional[int] = Field(None, ge=1, le=8760, description="间隔小时数（INTERVAL类型使用）")
    execute_time: Optional[str] = Field(None, description="执行时间 HH:mm 格式（DAILY/WEEKLY类型使用）")
    week_days: Optional[List[int]] = Field(None, description="星期几列表（WEEKLY类型使用，1-7）")
    cron_expression: Optional[str] = Field(None, description="Cron表达式（CUSTOM类型使用）")

    @field_validator('execute_time')
    @classmethod
    def validate_execute_time(cls, v):
        if v is not None:
            import re
            if not re.match(r'^\d{2}:\d{2}$', v):
                raise ValueError('execute_time must be in HH:mm format')
            hour, minute = int(v.split(':')[0]), int(v.split(':')[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError('execute_time must be valid time')
        return v

    @field_validator('week_days')
    @classmethod
    def validate_week_days(cls, v):
        if v is not None:
            if not all(1 <= day <= 7 for day in v):
                raise ValueError('week_days must be between 1 and 7')
        return v

    @field_validator('cron_expression')
    @classmethod
    def validate_cron(cls, v):
        if v is not None:
            try:
                from croniter import croniter
                croniter(v)
            except Exception as e:
                raise ValueError(f'Invalid cron expression: {str(e)}')
        return v

    class Config:
        from_attributes = True


class ScheduledTaskDTO(BaseModel):
    """定时任务 DTO"""
    id: str
    user_id: str
    agent_id: str
    session_id: str
    content: str
    repeat_type: RepeatType
    repeat_config: Dict[str, Any]
    status: ScheduleTaskStatus
    last_execute_time: Optional[datetime] = None
    next_execute_time: datetime
    max_retry_count: int = 3
    timeout_minutes: int = 30
    last_error: Optional[str] = None
    retry_count: int = 0
    notify_on_failure: bool = True
    docker_image: str = "agentx/task-sandbox:latest"
    resource_quota: Dict[str, Any] = {"cpu_limit": 1.0, "memory_limit": "512M"}
    version: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateScheduledTaskRequest(BaseModel):
    """创建定时任务请求"""
    agent_id: str = Field(..., description="Agent ID")
    session_id: str = Field(..., description="会话 ID")
    content: str = Field(..., min_length=1, max_length=10000, description="任务内容")
    repeat_type: RepeatType = Field(..., description="重复类型")
    repeat_config: RepeatConfigSchema = Field(default_factory=RepeatConfigSchema, description="重复配置")
    max_retry_count: int = Field(3, ge=0, le=10, description="最大重试次数")
    timeout_minutes: int = Field(30, ge=1, le=1440, description="超时时间（分钟）")
    notify_on_failure: bool = Field(True, description="失败时是否通知")
    docker_image: Optional[str] = Field("agentx/task-sandbox:latest", description="执行容器镜像")
    resource_quota: Optional[Dict[str, Any]] = Field(None, description="资源配额")


class UpdateScheduledTaskRequest(BaseModel):
    """更新定时任务请求"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000, description="任务内容")
    repeat_type: Optional[RepeatType] = Field(None, description="重复类型")
    repeat_config: Optional[RepeatConfigSchema] = Field(None, description="重复配置")
    max_retry_count: Optional[int] = Field(None, ge=0, le=10, description="最大重试次数")
    timeout_minutes: Optional[int] = Field(None, ge=1, le=1440, description="超时时间（分钟）")
    notify_on_failure: Optional[bool] = Field(None, description="失败时是否通知")
    docker_image: Optional[str] = Field(None, description="执行容器镜像")
    resource_quota: Optional[Dict[str, Any]] = Field(None, description="资源配额")


class TaskExecutionLogDTO(BaseModel):
    """任务执行日志 DTO"""
    id: str
    task_id: str
    execute_time: datetime
    status: str
    result: Optional[str] = None
    error_message: Optional[str] = None
    duration: Optional[int] = None
    container_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ScheduledTaskListResponse(BaseModel):
    """定时任务列表响应"""
    items: List[ScheduledTaskDTO]
    total: int
    page: int
    page_size: int


class TaskExecutionLogListResponse(BaseModel):
    """任务执行日志列表响应"""
    items: List[TaskExecutionLogDTO]
    total: int
    page: int
    page_size: int
