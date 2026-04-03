from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import logging

try:
    from croniter import croniter
except ImportError:
    croniter = None

from app.domain.scheduledtask.model import ScheduledTask
from app.domain.scheduledtask.constant import RepeatType, ScheduleTaskStatus

logger = logging.getLogger(__name__)


class TaskScheduleService:
    """任务调度服务 - 负责计算下次执行时间和管理调度"""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    def calculate_next_execute_time(self, task: ScheduledTask, base_time: datetime = None) -> datetime:
        """
        计算下次执行时间

        Args:
            task: 定时任务
            base_time: 基准时间，默认为当前时间

        Returns:
            下次执行时间
        """
        base_time = base_time or datetime.utcnow()
        repeat_config = task.repeat_config or {}

        if task.repeat_type == RepeatType.IMMEDIATE:
            # 立即执行类型，返回当前时间
            return base_time

        elif task.repeat_type == RepeatType.INTERVAL:
            # 间隔重复
            interval_hours = repeat_config.get("interval_hours", 1)
            return base_time + timedelta(hours=interval_hours)

        elif task.repeat_type == RepeatType.DAILY:
            # 每日重复
            execute_time_str = repeat_config.get("execute_time", "00:00")
            hour, minute = map(int, execute_time_str.split(":"))

            next_time = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if next_time <= base_time:
                next_time += timedelta(days=1)
            return next_time

        elif task.repeat_type == RepeatType.WEEKLY:
            # 每周重复
            week_days = repeat_config.get("week_days", [1])  # 默认周一
            execute_time_str = repeat_config.get("execute_time", "00:00")
            hour, minute = map(int, execute_time_str.split(":"))

            current_weekday = base_time.isoweekday()
            target_days = sorted(week_days)

            # 找到下一个执行的星期几
            days_ahead = None
            for target_day in target_days:
                if target_day > current_weekday:
                    days_ahead = target_day - current_weekday
                    break
                elif target_day == current_weekday:
                    target_time = base_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if target_time > base_time:
                        days_ahead = 0
                        break

            if days_ahead is None:
                # 本周没有更多执行日，取下周的第一个执行日
                days_ahead = 7 - current_weekday + target_days[0]

            next_time = base_time + timedelta(days=days_ahead)
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return next_time

        elif task.repeat_type == RepeatType.CUSTOM:
            # 自定义 Cron 表达式
            cron_expression = repeat_config.get("cron_expression", "0 0 * * *")
            if croniter:
                cron = croniter(cron_expression, base_time)
                return cron.get_next(datetime)
            else:
                # 如果没有 croniter，默认每小时执行
                self.logger.warning("croniter not installed, using default interval")
                return base_time + timedelta(hours=1)

        else:
            # 默认返回当前时间
            return base_time

    def validate_repeat_config(self, repeat_type: RepeatType, repeat_config: Dict[str, Any]) -> bool:
        """
        验证重复配置是否合法

        Args:
            repeat_type: 重复类型
            repeat_config: 重复配置

        Returns:
            是否合法
        """
        if repeat_type == RepeatType.IMMEDIATE:
            return True

        elif repeat_type == RepeatType.INTERVAL:
            interval_hours = repeat_config.get("interval_hours")
            if interval_hours is None:
                return False
            return 1 <= interval_hours <= 8760

        elif repeat_type == RepeatType.DAILY:
            execute_time = repeat_config.get("execute_time")
            if not execute_time:
                return False
            import re
            return bool(re.match(r'^\d{2}:\d{2}$', execute_time))

        elif repeat_type == RepeatType.WEEKLY:
            week_days = repeat_config.get("week_days")
            execute_time = repeat_config.get("execute_time")
            if not week_days or not execute_time:
                return False
            if not all(1 <= day <= 7 for day in week_days):
                return False
            import re
            return bool(re.match(r'^\d{2}:\d{2}$', execute_time))

        elif repeat_type == RepeatType.CUSTOM:
            cron_expression = repeat_config.get("cron_expression")
            if not cron_expression:
                return False
            if croniter:
                try:
                    croniter(cron_expression)
                    return True
                except Exception:
                    return False
            return True

        return False


class ScheduledTaskDomainService:
    """定时任务领域服务"""

    def __init__(self, task_repository, log_repository, schedule_service: TaskScheduleService):
        self.task_repository = task_repository
        self.log_repository = log_repository
        self.schedule_service = schedule_service
        self.logger = logging.getLogger(self.__class__.__name__)

    def create_task(self, task: ScheduledTask) -> ScheduledTask:
        """创建定时任务"""
        # 验证重复配置
        if not self.schedule_service.validate_repeat_config(task.repeat_type, task.repeat_config):
            raise ValueError("Invalid repeat configuration")

        # 计算下次执行时间
        task.next_execute_time = self.schedule_service.calculate_next_execute_time(task)
        task.status = ScheduleTaskStatus.PENDING

        return self.task_repository.create(task)

    def update_task(self, task_id: str, updates: Dict[str, Any], user_id: str) -> Optional[ScheduledTask]:
        """更新定时任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        # 更新字段
        if "content" in updates:
            task.content = updates["content"]
        if "repeat_type" in updates:
            task.repeat_type = updates["repeat_type"]
        if "repeat_config" in updates:
            task.repeat_config = updates["repeat_config"]
            # 验证新的重复配置
            if not self.schedule_service.validate_repeat_config(task.repeat_type, task.repeat_config):
                raise ValueError("Invalid repeat configuration")
            # 重新计算下次执行时间
            task.next_execute_time = self.schedule_service.calculate_next_execute_time(task)
        if "max_retry_count" in updates:
            task.max_retry_count = updates["max_retry_count"]
        if "timeout_minutes" in updates:
            task.timeout_minutes = updates["timeout_minutes"]
        if "notify_on_failure" in updates:
            task.notify_on_failure = updates["notify_on_failure"]
        if "docker_image" in updates:
            task.docker_image = updates["docker_image"]
        if "resource_quota" in updates:
            task.resource_quota = updates["resource_quota"]

        return self.task_repository.update(task)

    def delete_task(self, task_id: str, user_id: str) -> bool:
        """删除定时任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        return self.task_repository.delete(task_id)

    def get_task(self, task_id: str, user_id: str) -> Optional[ScheduledTask]:
        """获取任务详情"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            return None
        if task.user_id != user_id:
            raise ValueError("Permission denied")
        return task

    def list_tasks(self, user_id: str, page: int = 1, page_size: int = 10, status: Optional[ScheduleTaskStatus] = None) -> Dict[str, Any]:
        """获取任务列表"""
        return self.task_repository.get_by_user_id(user_id, page, page_size, status)

    def pause_task(self, task_id: str, user_id: str) -> bool:
        """暂停任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        if task.status != ScheduleTaskStatus.PENDING:
            raise ValueError(f"Cannot pause task with status {task.status}")

        task.status = ScheduleTaskStatus.PAUSED
        self.task_repository.update(task)
        return True

    def resume_task(self, task_id: str, user_id: str) -> bool:
        """恢复任务"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        if task.status != ScheduleTaskStatus.PAUSED:
            raise ValueError(f"Cannot resume task with status {task.status}")

        task.status = ScheduleTaskStatus.PENDING
        # 重新计算下次执行时间
        task.next_execute_time = self.schedule_service.calculate_next_execute_time(task)
        self.task_repository.update(task)
        return True

    def record_execution(self, task_id: str, status: str, result: Optional[str] = None,
                        error_message: Optional[str] = None, duration: Optional[int] = None,
                        container_id: Optional[str] = None) -> TaskExecutionLog:
        """记录任务执行日志"""
        log = TaskExecutionLog(
            task_id=task_id,
            execute_time=datetime.utcnow(),
            status=status,
            result=result,
            error_message=error_message,
            duration=duration,
            container_id=container_id
        )
        return self.log_repository.create(log)

    def get_execution_logs(self, task_id: str, user_id: str, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """获取任务执行日志"""
        task = self.task_repository.get_by_id(task_id)
        if not task:
            raise ValueError("Task not found")
        if task.user_id != user_id:
            raise ValueError("Permission denied")

        return self.log_repository.get_by_task_id(task_id, page, page_size)
