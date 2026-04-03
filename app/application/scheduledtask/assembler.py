from typing import List, Dict, Any
from datetime import datetime

from app.domain.scheduledtask.model import ScheduledTask, TaskExecutionLog
from app.domain.scheduledtask.schemas import (
    ScheduledTaskDTO,
    TaskExecutionLogDTO,
    CreateScheduledTaskRequest,
    UpdateScheduledTaskRequest
)
from app.domain.scheduledtask.constant import RepeatType, ScheduleTaskStatus


class ScheduledTaskAssembler:
    """定时任务组装器 - 负责实体和DTO之间的转换"""

    @staticmethod
    def to_entity(request: CreateScheduledTaskRequest, user_id: str) -> ScheduledTask:
        """
        将创建请求转换为实体

        Args:
            request: 创建请求
            user_id: 用户ID

        Returns:
            定时任务实体
        """
        return ScheduledTask(
            user_id=user_id,
            agent_id=request.agent_id,
            session_id=request.session_id,
            content=request.content,
            repeat_type=request.repeat_type,
            repeat_config=request.repeat_config.model_dump(exclude_none=True) if request.repeat_config else {},
            status=ScheduleTaskStatus.PENDING,
            max_retry_count=request.max_retry_count,
            timeout_minutes=request.timeout_minutes,
            notify_on_failure=request.notify_on_failure,
            docker_image=request.docker_image or "agentx/task-sandbox:latest",
            resource_quota=request.resource_quota or {"cpu_limit": 1.0, "memory_limit": "512M"},
            next_execute_time=datetime.utcnow()  # 临时值，会被重新计算
        )

    @staticmethod
    def to_dto(entity: ScheduledTask) -> ScheduledTaskDTO:
        """
        将实体转换为DTO

        Args:
            entity: 定时任务实体

        Returns:
            定时任务DTO
        """
        return ScheduledTaskDTO(
            id=entity.id,
            user_id=entity.user_id,
            agent_id=entity.agent_id,
            session_id=entity.session_id,
            content=entity.content,
            repeat_type=entity.repeat_type,
            repeat_config=entity.repeat_config or {},
            status=entity.status,
            last_execute_time=entity.last_execute_time,
            next_execute_time=entity.next_execute_time,
            max_retry_count=entity.max_retry_count,
            timeout_minutes=entity.timeout_minutes,
            last_error=entity.last_error,
            retry_count=entity.retry_count,
            notify_on_failure=entity.notify_on_failure,
            docker_image=entity.docker_image,
            resource_quota=entity.resource_quota or {"cpu_limit": 1.0, "memory_limit": "512M"},
            version=entity.version,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

    @staticmethod
    def to_dto_list(entities: List[ScheduledTask]) -> List[ScheduledTaskDTO]:
        """
        将实体列表转换为DTO列表

        Args:
            entities: 实体列表

        Returns:
            DTO列表
        """
        return [ScheduledTaskAssembler.to_dto(entity) for entity in entities]

    @staticmethod
    def execution_log_to_dto(entity: TaskExecutionLog) -> TaskExecutionLogDTO:
        """
        将执行日志实体转换为DTO

        Args:
            entity: 执行日志实体

        Returns:
            执行日志DTO
        """
        return TaskExecutionLogDTO(
            id=entity.id,
            task_id=entity.task_id,
            execute_time=entity.execute_time,
            status=entity.status,
            result=entity.result,
            error_message=entity.error_message,
            duration=entity.duration,
            container_id=entity.container_id,
            created_at=entity.created_at
        )

    @staticmethod
    def execution_log_to_dto_list(entities: List[TaskExecutionLog]) -> List[TaskExecutionLogDTO]:
        """
        将执行日志实体列表转换为DTO列表

        Args:
            entities: 实体列表

        Returns:
            DTO列表
        """
        return [ScheduledTaskAssembler.execution_log_to_dto(entity) for entity in entities]

    @staticmethod
    def extract_update_data(request: UpdateScheduledTaskRequest) -> Dict[str, Any]:
        """
        从更新请求中提取更新数据

        Args:
            request: 更新请求

        Returns:
            更新数据字典
        """
        updates = {}

        if request.content is not None:
            updates["content"] = request.content
        if request.repeat_type is not None:
            updates["repeat_type"] = request.repeat_type
        if request.repeat_config is not None:
            updates["repeat_config"] = request.repeat_config.model_dump(exclude_none=True)
        if request.max_retry_count is not None:
            updates["max_retry_count"] = request.max_retry_count
        if request.timeout_minutes is not None:
            updates["timeout_minutes"] = request.timeout_minutes
        if request.notify_on_failure is not None:
            updates["notify_on_failure"] = request.notify_on_failure
        if request.docker_image is not None:
            updates["docker_image"] = request.docker_image
        if request.resource_quota is not None:
            updates["resource_quota"] = request.resource_quota

        return updates
