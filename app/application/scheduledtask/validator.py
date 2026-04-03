import re
import logging
from typing import List, Tuple

from app.domain.scheduledtask.constant import RepeatType

logger = logging.getLogger(__name__)


class TaskValidator:
    """任务内容校验器"""

    CONTENT_MAX_LENGTH = 10000
    CONTENT_MIN_LENGTH = 1

    # 禁止的可执行代码模式
    SENSITIVE_PATTERNS = [
        r'\bimport\s+os\b',
        r'\bimport\s+subprocess\b',
        r'\bimport\s+sys\b',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
        r'\bcompile\s*\(',
        r'\bopen\s*\(',
        r'\bfile\s*\(',
        r'\bos\.system\s*\(',
        r'\bos\.popen\s*\(',
        r'\bsubprocess\.call\s*\(',
        r'\bsubprocess\.Popen\s*\(',
        r'\binput\s*\(',
        r'\braw_input\s*\(',
    ]

    # 敏感词列表（需要脱敏）
    SENSITIVE_WORDS = [
        'password',
        'secret',
        'token',
        'apikey',
        'api_key',
        'private_key',
        'access_token',
        'refresh_token',
        'auth_token',
        'credentials',
        'passwd',
        'pwd',
    ]

    @classmethod
    def validate_content(cls, content: str) -> Tuple[bool, str]:
        """
        验证任务内容

        Args:
            content: 任务内容

        Returns:
            (是否通过, 错误信息)
        """
        if not content:
            return False, "Content is required"

        if len(content) < cls.CONTENT_MIN_LENGTH:
            return False, f"Content must be at least {cls.CONTENT_MIN_LENGTH} characters"

        if len(content) > cls.CONTENT_MAX_LENGTH:
            return False, f"Content exceeds maximum length of {cls.CONTENT_MAX_LENGTH} characters"

        # 检查可执行代码
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                logger.warning(f"Content contains prohibited executable code: {pattern}")
                return False, "Content contains prohibited executable code"

        return True, ""

    @classmethod
    def sanitize_content(cls, content: str) -> str:
        """
        对内容进行脱敏处理

        Args:
            content: 原始内容

        Returns:
            脱敏后的内容
        """
        sanitized = content

        for word in cls.SENSITIVE_WORDS:
            # 匹配 key=value 或 key: value 格式
            pattern = rf'\b{word}\s*[=:]\s*\S+'
            replacement = f'{word}=[REDACTED]'
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)

        return sanitized

    @classmethod
    def validate_repeat_config(cls, repeat_type: RepeatType, repeat_config: dict) -> Tuple[bool, str]:
        """
        验证重复配置

        Args:
            repeat_type: 重复类型
            repeat_config: 重复配置

        Returns:
            (是否通过, 错误信息)
        """
        if repeat_type == RepeatType.IMMEDIATE:
            return True, ""

        elif repeat_type == RepeatType.INTERVAL:
            interval_hours = repeat_config.get("interval_hours")
            if interval_hours is None:
                return False, "interval_hours is required for INTERVAL type"
            if not isinstance(interval_hours, int) or interval_hours < 1 or interval_hours > 8760:
                return False, "interval_hours must be an integer between 1 and 8760"

        elif repeat_type == RepeatType.DAILY:
            execute_time = repeat_config.get("execute_time")
            if not execute_time:
                return False, "execute_time is required for DAILY type"
            if not re.match(r'^\d{2}:\d{2}$', execute_time):
                return False, "execute_time must be in HH:mm format"
            try:
                hour, minute = map(int, execute_time.split(":"))
                if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                    return False, "execute_time must be a valid time"
            except ValueError:
                return False, "execute_time must be a valid time"

        elif repeat_type == RepeatType.WEEKLY:
            week_days = repeat_config.get("week_days")
            execute_time = repeat_config.get("execute_time")

            if not week_days:
                return False, "week_days is required for WEEKLY type"
            if not isinstance(week_days, list) or len(week_days) == 0:
                return False, "week_days must be a non-empty list"
            if not all(isinstance(d, int) and 1 <= d <= 7 for d in week_days):
                return False, "week_days must be integers between 1 and 7"

            if not execute_time:
                return False, "execute_time is required for WEEKLY type"
            if not re.match(r'^\d{2}:\d{2}$', execute_time):
                return False, "execute_time must be in HH:mm format"

        elif repeat_type == RepeatType.CUSTOM:
            cron_expression = repeat_config.get("cron_expression")
            if not cron_expression:
                return False, "cron_expression is required for CUSTOM type"
            try:
                from croniter import croniter
                croniter(cron_expression)
            except ImportError:
                logger.warning("croniter not installed, skipping cron validation")
            except Exception as e:
                return False, f"Invalid cron expression: {str(e)}"

        return True, ""

    @classmethod
    def validate_resource_quota(cls, resource_quota: dict) -> Tuple[bool, str]:
        """
        验证资源配额

        Args:
            resource_quota: 资源配额配置

        Returns:
            (是否通过, 错误信息)
        """
        if not resource_quota:
            return True, ""

        cpu_limit = resource_quota.get("cpu_limit")
        if cpu_limit is not None:
            if not isinstance(cpu_limit, (int, float)) or cpu_limit <= 0 or cpu_limit > 16:
                return False, "cpu_limit must be a positive number not exceeding 16"

        memory_limit = resource_quota.get("memory_limit")
        if memory_limit is not None:
            # 支持格式：512M, 1G, 1024
            if isinstance(memory_limit, (int, float)):
                if memory_limit <= 0 or memory_limit > 65536:
                    return False, "memory_limit must be a positive number not exceeding 65536"
            elif isinstance(memory_limit, str):
                if not re.match(r'^\d+[MGmg]?$', memory_limit):
                    return False, "memory_limit must be in format like '512M' or '1G'"
            else:
                return False, "memory_limit must be a number or string"

        return True, ""

    @classmethod
    def validate_docker_image(cls, docker_image: str) -> Tuple[bool, str]:
        """
        验证 Docker 镜像名称

        Args:
            docker_image: 镜像名称

        Returns:
            (是否通过, 错误信息)
        """
        if not docker_image:
            return False, "docker_image is required"

        # 基本的镜像名称格式验证
        # 支持格式：name, name:tag, registry/name:tag
        pattern = r'^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*(:[a-zA-Z0-9_.-]+)?$'
        if not re.match(pattern, docker_image):
            return False, "Invalid docker image format"

        return True, ""
