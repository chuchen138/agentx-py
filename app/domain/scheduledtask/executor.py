import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from app.domain.scheduledtask.model import ScheduledTask, TaskExecutionLog
from app.domain.scheduledtask.constant import ScheduleTaskStatus, RepeatType
from app.domain.scheduledtask.service import TaskScheduleService
from app.infrastructure.distributed_lock import ScheduledTaskLock, IdempotencyManager

logger = logging.getLogger(__name__)


class TaskExecutor(ABC):
    """任务执行器抽象基类"""

    @abstractmethod
    async def execute(self, task: ScheduledTask) -> Dict[str, Any]:
        """
        执行任务

        Args:
            task: 定时任务

        Returns:
            执行结果
        """
        pass


class AgentTaskExecutor(TaskExecutor):
    """Agent 任务执行器"""

    def __init__(self, agent_service=None):
        self.agent_service = agent_service
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute(self, task: ScheduledTask) -> Dict[str, Any]:
        """
        执行 Agent 任务

        Args:
            task: 定时任务

        Returns:
            执行结果
        """
        start_time = time.time()

        try:
            self.logger.info(f"Executing task {task.id} for agent {task.agent_id}")

            # TODO: 调用 Agent 执行服务
            # 这里应该调用 Agent 执行接口，传入 task.content 和 task.session_id
            # 暂时模拟执行成功
            result = {
                "success": True,
                "message": f"Task executed successfully: {task.content[:50]}...",
                "agent_id": task.agent_id,
                "session_id": task.session_id
            }

            # 如果有 agent_service，调用实际执行
            if self.agent_service:
                # result = await self.agent_service.execute(
                #     agent_id=task.agent_id,
                #     session_id=task.session_id,
                #     content=task.content
                # )
                pass

            duration = int((time.time() - start_time) * 1000)  # 毫秒

            return {
                "success": True,
                "result": str(result),
                "duration": duration,
                "container_id": None
            }

        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            self.logger.error(f"Task execution failed: {e}")

            return {
                "success": False,
                "error": str(e),
                "duration": duration,
                "container_id": None
            }


class ScheduledTaskExecutionService:
    """定时任务执行服务"""

    def __init__(
        self,
        task_repository,
        log_repository,
        schedule_service: TaskScheduleService,
        executor: TaskExecutor = None,
        redis_client=None
    ):
        self.task_repository = task_repository
        self.log_repository = log_repository
        self.schedule_service = schedule_service
        self.executor = executor or AgentTaskExecutor()
        self.idempotency = IdempotencyManager(redis_client)
        self.logger = logging.getLogger(self.__class__.__name__)

    async def execute_task(self, task_id: str) -> bool:
        """
        执行定时任务（带分布式锁和幂等性检查）

        Args:
            task_id: 任务ID

        Returns:
            是否执行成功
        """
        task = self.task_repository.get_by_id(task_id)
        if not task:
            self.logger.error(f"Task not found: {task_id}")
            return False

        # 检查任务状态
        if task.status not in [ScheduleTaskStatus.PENDING, ScheduleTaskStatus.RUNNING]:
            self.logger.warning(f"Task {task_id} is not in executable status: {task.status}")
            return False

        execute_time = datetime.utcnow()

        # 幂等性检查
        if not self.idempotency.check_and_set(task_id, execute_time):
            self.logger.info(f"Task {task_id} already executed at {execute_time}, skipping")
            return True

        # 获取分布式锁
        lock = ScheduledTaskLock(task_id, execute_time)
        if not lock.acquire(blocking=False):
            self.logger.info(f"Could not acquire lock for task {task_id}, skipping")
            return True

        try:
            return await self._do_execute(task, execute_time)
        finally:
            lock.release()

    async def _do_execute(self, task: ScheduledTask, execute_time: datetime) -> bool:
        """
        实际执行任务

        Args:
            task: 定时任务
            execute_time: 执行时间

        Returns:
            是否执行成功
        """
        # 更新任务状态为执行中
        task.status = ScheduleTaskStatus.RUNNING
        task.last_execute_time = execute_time
        self.task_repository.update(task)

        try:
            # 执行任务
            result = await self._execute_with_timeout(task)

            # 记录执行日志
            self.log_repository.create(TaskExecutionLog(
                task_id=task.id,
                execute_time=execute_time,
                status="SUCCESS" if result["success"] else "FAILED",
                result=result.get("result"),
                error_message=result.get("error"),
                duration=result.get("duration"),
                container_id=result.get("container_id")
            ))

            if result["success"]:
                # 执行成功
                task.status = ScheduleTaskStatus.COMPLETED
                task.last_error = None
                task.retry_count = 0

                # 如果是重复任务，重新计算下次执行时间
                if task.repeat_type != RepeatType.IMMEDIATE:
                    task.status = ScheduleTaskStatus.PENDING
                    task.next_execute_time = self.schedule_service.calculate_next_execute_time(task, execute_time)

            else:
                # 执行失败
                await self._handle_failure(task, result.get("error"))

            self.task_repository.update(task)
            return result["success"]

        except asyncio.TimeoutError:
            # 超时处理
            await self._handle_timeout(task, execute_time)
            return False

        except Exception as e:
            # 异常处理
            self.logger.exception(f"Unexpected error executing task {task.id}: {e}")
            await self._handle_failure(task, str(e))
            return False

    async def _execute_with_timeout(self, task: ScheduledTask) -> Dict[str, Any]:
        """
        带超时的任务执行

        Args:
            task: 定时任务

        Returns:
            执行结果
        """
        timeout_seconds = task.timeout_minutes * 60

        try:
            return await asyncio.wait_for(
                self.executor.execute(task),
                timeout=timeout_seconds
            )
        except asyncio.TimeoutError:
            self.logger.error(f"Task {task.id} execution timeout after {task.timeout_minutes} minutes")
            raise

    async def _handle_failure(self, task: ScheduledTask, error_message: str):
        """
        处理任务失败

        Args:
            task: 定时任务
            error_message: 错误信息
        """
        task.last_error = error_message
        task.retry_count += 1

        # 检查是否需要重试
        if task.retry_count < task.max_retry_count:
            # 指数退避重试
            retry_delay = self._calculate_retry_delay(task.retry_count)
            self.logger.info(f"Task {task.id} will retry in {retry_delay} seconds (attempt {task.retry_count}/{task.max_retry_count})")

            task.status = ScheduleTaskStatus.PENDING
            task.next_execute_time = datetime.utcnow() + timedelta(seconds=retry_delay)
        else:
            # 重试次数用尽
            self.logger.error(f"Task {task.id} failed after {task.max_retry_count} retries")
            task.status = ScheduleTaskStatus.FAILED

            # TODO: 发送失败通知
            if task.notify_on_failure:
                await self._send_failure_notification(task)

        self.task_repository.update(task)

        # 记录失败日志
        self.log_repository.create(TaskExecutionLog(
            task_id=task.id,
            execute_time=datetime.utcnow(),
            status="FAILED",
            error_message=error_message,
            duration=0
        ))

    async def _handle_timeout(self, task: ScheduledTask, execute_time: datetime):
        """
        处理任务超时

        Args:
            task: 定时任务
            execute_time: 执行时间
        """
        self.logger.error(f"Task {task.id} execution timeout")

        task.status = ScheduleTaskStatus.FAILED
        task.last_error = "Execution timeout"
        self.task_repository.update(task)

        # 记录超时日志
        self.log_repository.create(TaskExecutionLog(
            task_id=task.id,
            execute_time=execute_time,
            status="TIMEOUT",
            error_message=f"Execution timeout after {task.timeout_minutes} minutes",
            duration=task.timeout_minutes * 60 * 1000
        ))

        # TODO: 发送超时告警
        if task.notify_on_failure:
            await self._send_failure_notification(task, is_timeout=True)

    def _calculate_retry_delay(self, retry_count: int) -> int:
        """
        计算重试延迟（指数退避）

        Args:
            retry_count: 当前重试次数

        Returns:
            延迟秒数
        """
        # 指数退避：1分钟、5分钟、15分钟
        delays = [60, 300, 900]
        return delays[min(retry_count - 1, len(delays) - 1)]

    async def _send_failure_notification(self, task: ScheduledTask, is_timeout: bool = False):
        """
        发送失败通知

        Args:
            task: 定时任务
            is_timeout: 是否超时
        """
        # TODO: 实现通知逻辑（邮件、站内信、Webhook等）
        notification_type = "timeout" if is_timeout else "failure"
        self.logger.info(f"Sending {notification_type} notification for task {task.id} to user {task.user_id}")

    async def trigger_task_manually(self, task_id: str, user_id: str) -> bool:
        """
        手动触发任务执行

        Args:
            task_id: 任务ID
            user_id: 用户ID

        Returns:
            是否触发成功
        """
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        # 手动触发不检查状态，直接执行
        return await self.execute_task(task_id)

    async def check_and_execute_due_tasks(self):
        """
        检查并执行到期的任务
        由调度器定期调用
        """
        due_tasks = self.task_repository.get_due_tasks(datetime.utcnow())

        if due_tasks:
            self.logger.info(f"Found {len(due_tasks)} due tasks")

        for task in due_tasks:
            try:
                await self.execute_task(task.id)
            except Exception as e:
                self.logger.exception(f"Error executing due task {task.id}: {e}")
