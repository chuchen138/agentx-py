import logging
from typing import Optional, Dict, Any, List

from app.domain.scheduledtask.model import ScheduledTask
from app.domain.scheduledtask.schemas import (
    ScheduledTaskDTO,
    CreateScheduledTaskRequest,
    UpdateScheduledTaskRequest,
    TaskExecutionLogDTO,
    ScheduledTaskListResponse,
    TaskExecutionLogListResponse
)
from app.domain.scheduledtask.service import ScheduledTaskDomainService, TaskScheduleService
from app.domain.scheduledtask.executor import ScheduledTaskExecutionService
from app.domain.scheduledtask.constant import ScheduleTaskStatus
from app.domain.scheduledtask.repository import (
    ScheduledTaskRepository,
    TaskExecutionLogRepository,
    SQLAlchemyScheduledTaskRepository,
    SQLAlchemyTaskExecutionLogRepository
)
from app.application.scheduledtask.assembler import ScheduledTaskAssembler
from app.application.scheduledtask.validator import TaskValidator

logger = logging.getLogger(__name__)


class ScheduledTaskAppService:
    """定时任务应用服务"""

    def __init__(
        self,
        domain_service: ScheduledTaskDomainService,
        execution_service: ScheduledTaskExecutionService
    ):
        self.domain_service = domain_service
        self.execution_service = execution_service
        self.assembler = ScheduledTaskAssembler()
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_task(self, request: CreateScheduledTaskRequest, user_id: str) -> ScheduledTaskDTO:
        """
        创建定时任务

        Args:
            request: 创建请求
            user_id: 用户ID

        Returns:
            创建的定时任务DTO
        """
        # 验证任务内容
        valid, error = TaskValidator.validate_content(request.content)
        if not valid:
            raise ValueError(error)

        # 验证重复配置
        valid, error = TaskValidator.validate_repeat_config(request.repeat_type, request.repeat_config.model_dump(exclude_none=True))
        if not valid:
            raise ValueError(error)

        # 验证资源配额
        if request.resource_quota:
            valid, error = TaskValidator.validate_resource_quota(request.resource_quota)
            if not valid:
                raise ValueError(error)

        # 验证 Docker 镜像
        valid, error = TaskValidator.validate_docker_image(request.docker_image or "agentx/task-sandbox:latest")
        if not valid:
            raise ValueError(error)

        # 转换为实体
        task = self.assembler.to_entity(request, user_id)

        # 创建任务
        created_task = self.domain_service.create_task(task)

        self.logger.info(f"Created scheduled task {created_task.id} for user {user_id}")

        return self.assembler.to_dto(created_task)

    def update_task(self, task_id: str, request: UpdateScheduledTaskRequest, user_id: str) -> ScheduledTaskDTO:
        """
        更新定时任务

        Args:
            task_id: 任务ID
            request: 更新请求
            user_id: 用户ID

        Returns:
            更新后的定时任务DTO
        """
        # 验证任务内容
        if request.content is not None:
            valid, error = TaskValidator.validate_content(request.content)
            if not valid:
                raise ValueError(error)

        # 验证重复配置
        if request.repeat_type is not None or request.repeat_config is not None:
            # 获取现有任务以获取当前配置
            existing_task = self.domain_service.get_task(task_id, user_id)
            repeat_type = request.repeat_type or existing_task.repeat_type
            repeat_config = request.repeat_config.model_dump(exclude_none=True) if request.repeat_config else existing_task.repeat_config

            valid, error = TaskValidator.validate_repeat_config(repeat_type, repeat_config)
            if not valid:
                raise ValueError(error)

        # 验证资源配额
        if request.resource_quota is not None:
            valid, error = TaskValidator.validate_resource_quota(request.resource_quota)
            if not valid:
                raise ValueError(error)

        # 验证 Docker 镜像
        if request.docker_image is not None:
            valid, error = TaskValidator.validate_docker_image(request.docker_image)
            if not valid:
                raise ValueError(error)

        # 提取更新数据
        updates = self.assembler.extract_update_data(request)

        # 更新任务
        updated_task = self.domain_service.update_task(task_id, updates, user_id)

        self.logger.info(f"Updated scheduled task {task_id}")

        return self.assembler.to_dto(updated_task)

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """
        删除定时任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        result = self.domain_service.delete_task(task_id, user_id)

        self.logger.info(f"Deleted scheduled task {task_id}")

        return result

    def get_task(self, task_id: str, user_id: str) -> Optional[ScheduledTaskDTO]:
        """
        获取任务详情

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            定时任务DTO
        """
        task = self.domain_service.get_task(task_id, user_id)
        if not task:
            return None

        return self.assembler.to_dto(task)

    def list_tasks(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 10,
        status: Optional[ScheduleTaskStatus] = None
    ) -> ScheduledTaskListResponse:
        """
        获取任务列表

        Args:
            user_id: 用户ID
            page: 页码
            page_size: 每页数量
            status: 状态过滤

        Returns:
            任务列表响应
        """
        result = self.domain_service.list_tasks(user_id, page, page_size, status)

        return ScheduledTaskListResponse(
            items=self.assembler.to_dto_list(result["items"]),
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )

    def pause_task(self, task_id: str, user_id: str) -> bool:
        """
        暂停任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否暂停成功
        """
        result = self.domain_service.pause_task(task_id, user_id)

        self.logger.info(f"Paused scheduled task {task_id}")

        return result

    def resume_task(self, task_id: str, user_id: str) -> bool:
        """
        恢复任务

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否恢复成功
        """
        result = self.domain_service.resume_task(task_id, user_id)

        self.logger.info(f"Resumed scheduled task {task_id}")

        return result

    async def trigger_task_manually(self, task_id: str, user_id: str) -> bool:
        """
        手动触发任务执行

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否触发成功
        """
        result = await self.execution_service.trigger_task_manually(task_id, user_id)

        self.logger.info(f"Manually triggered task {task_id}")

        return result

    def get_execution_logs(
        self,
        task_id: str,
        user_id: str,
        page: int = 1,
        page_size: int = 10
    ) -> TaskExecutionLogListResponse:
        """
        获取任务执行日志

        Args:
            task_id: 任务ID
            user_id: 用户ID
            page: 页码
            page_size: 每页数量

        Returns:
            执行日志列表响应
        """
        result = self.domain_service.get_execution_logs(task_id, user_id, page, page_size)

        return TaskExecutionLogListResponse(
            items=self.assembler.execution_log_to_dto_list(result["items"]),
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"]
        )


def create_scheduled_task_app_service(db_session) -> ScheduledTaskAppService:
    """
    创建定时任务应用服务实例

    Args:
        db_session: 数据库会话

    Returns:
        定时任务应用服务实例
    """
    # 创建仓储
    task_repository = SQLAlchemyScheduledTaskRepository(db_session)
    log_repository = SQLAlchemyTaskExecutionLogRepository(db_session)

    # 创建领域服务
    schedule_service = TaskScheduleService()
    domain_service = ScheduledTaskDomainService(task_repository, log_repository, schedule_service)

    # 创建执行服务
    execution_service = ScheduledTaskExecutionService(
        task_repository,
        log_repository,
        schedule_service
    )

    # 创建应用服务
    return ScheduledTaskAppService(domain_service, execution_service)
