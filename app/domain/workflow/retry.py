import random
from typing import Optional, Type


class ExponentialBackoffRetry:
    """指数退避重试器"""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        """计算重试延迟"""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        return delay + random.uniform(0, delay * 0.1)  # 添加抖动避免雪崩
    
    def should_retry(self, error_type: Type[Exception]) -> bool:
        """判断是否应该重试"""
        # 可重试的错误类型
        retryable_errors = [
            ConnectionError,
            TimeoutError,
            OSError
        ]
        
        # 不可重试的错误类型
        non_retryable_errors = [
            PermissionError,
            ValueError,
            TypeError,
            KeyError
        ]
        
        for error in non_retryable_errors:
            if issubclass(error_type, error):
                return False
        
        for error in retryable_errors:
            if issubclass(error_type, error):
                return True
        
        return False
    
    def can_retry(self, attempt: int) -> bool:
        """判断是否还能重试"""
        return attempt < self.max_retries
