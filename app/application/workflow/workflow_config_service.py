from typing import Dict, Any, Optional


class RetryConfig:
    """重试配置"""
    def __init__(self, max_attempts: int = 5, backoff: float = 1.0):
        self.max_attempts = max_attempts
        self.backoff = backoff


class WorkflowConfigService:
    """工作流配置服务"""
    
    def __init__(self):
        # 默认配置
        self._config = {
            "workflow": {
                "enabled": True,
                "state": {
                    "persistence": True
                },
                "timeout": 300,  # 5分钟
                "task": {
                    "max_count": 100,
                    "parallel_threshold": 16
                }
            },
            "task": {
                "retry": {
                    "max_attempts": 5,
                    "backoff": 1.0
                },
                "timeout": 30
            },
            "summary": {
                "token_threshold": 4000,
                "turn_threshold": 10,
                "strategy": "token"
            },
            "eventbus": {
                "async": True,
                "queue_size": 10000,
                "thread_count": 4
            }
        }
    
    def is_workflow_enabled(self) -> bool:
        """是否启用工作流"""
        return self._config.get("workflow", {}).get("enabled", True)
    
    def get_max_tasks_per_workflow(self) -> int:
        """获取每个工作流的最大任务数"""
        return self._config.get("workflow", {}).get("task", {}).get("max_count", 100)
    
    def get_parallel_threshold(self) -> int:
        """获取并行阈值"""
        return self._config.get("workflow", {}).get("task", {}).get("parallel_threshold", 16)
    
    def get_task_retry_config(self) -> RetryConfig:
        """获取任务重试配置"""
        retry_config = self._config.get("task", {}).get("retry", {})
        return RetryConfig(
            max_attempts=retry_config.get("max_attempts", 5),
            backoff=retry_config.get("backoff", 1.0)
        )
    
    def get_task_timeout(self) -> int:
        """获取任务超时时间"""
        return self._config.get("task", {}).get("timeout", 30)
    
    def get_summary_token_threshold(self) -> int:
        """获取摘要Token阈值"""
        return self._config.get("summary", {}).get("token_threshold", 4000)
    
    def get_summary_turn_threshold(self) -> int:
        """获取摘要轮次阈值"""
        return self._config.get("summary", {}).get("turn_threshold", 10)
    
    def is_state_persistence_enabled(self) -> bool:
        """是否启用状态持久化"""
        return self._config.get("workflow", {}).get("state", {}).get("persistence", True)
    
    def get_workflow_timeout(self) -> int:
        """获取工作流超时时间"""
        return self._config.get("workflow", {}).get("timeout", 300)
    
    def update_config(self, config: Dict[str, Any]):
        """更新配置"""
        self._config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config
