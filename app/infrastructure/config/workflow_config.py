import os
from typing import Dict, Any


class WorkflowConfig:
    """工作流配置"""
    
    def __init__(self):
        self._config = {
            "workflow": {
                "enabled": self._get_bool_env("WORKFLOW_ENABLED", True),
                "state": {
                    "persistence": self._get_bool_env("WORKFLOW_STATE_PERSISTENCE", True)
                },
                "timeout": self._get_int_env("WORKFLOW_TIMEOUT", 300),
                "task": {
                    "max_count": self._get_int_env("WORKFLOW_TASK_MAX_COUNT", 100),
                    "parallel_threshold": self._get_int_env("WORKFLOW_TASK_PARALLEL_THRESHOLD", 16)
                }
            },
            "task": {
                "retry": {
                    "max_attempts": self._get_int_env("TASK_RETRY_MAX_ATTEMPTS", 5),
                    "backoff": self._get_float_env("TASK_RETRY_BACKOFF", 1.0)
                },
                "timeout": self._get_int_env("TASK_TIMEOUT", 30)
            },
            "summary": {
                "token_threshold": self._get_int_env("SUMMARY_TOKEN_THRESHOLD", 4000),
                "turn_threshold": self._get_int_env("SUMMARY_TURN_THRESHOLD", 10),
                "strategy": os.getenv("SUMMARY_STRATEGY", "token")
            },
            "eventbus": {
                "async": self._get_bool_env("EVENTBUS_ASYNC", True),
                "queue_size": self._get_int_env("EVENTBUS_QUEUE_SIZE", 10000),
                "thread_count": self._get_int_env("EVENTBUS_THREAD_COUNT", 4)
            }
        }
    
    def _get_bool_env(self, key: str, default: bool) -> bool:
        """获取布尔类型的环境变量"""
        value = os.getenv(key)
        if value is None:
            return default
        return value.lower() in ["true", "1", "yes"]
    
    def _get_int_env(self, key: str, default: int) -> int:
        """获取整数类型的环境变量"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def _get_float_env(self, key: str, default: float) -> float:
        """获取浮点数类型的环境变量"""
        value = os.getenv(key)
        if value is None:
            return default
        try:
            return float(value)
        except ValueError:
            return default
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config


# 全局配置实例
workflow_config = WorkflowConfig()
