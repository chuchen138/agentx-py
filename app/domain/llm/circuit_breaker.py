from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Deque, Optional
from collections import deque


class CircuitState(Enum):
    """熔断器状态"""
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open" # 半开状态


class CircuitBreaker:
    """熔断器实现"""
    
    def __init__(self, 
                 failure_threshold: float = 0.5, 
                 consecutive_failures: int = 10,
                 recovery_timeout: int = 60, 
                 half_open_requests: int = 3,
                 min_requests: int = 10):
        """初始化熔断器
        
        Args:
            failure_threshold: 错误率阈值，默认 50%
            consecutive_failures: 连续失败次数，默认 10 次
            recovery_timeout: 恢复超时时间，默认 60 秒
            half_open_requests: 半开状态下的探测请求数，默认 3 个
            min_requests: 最小请求数，达到后才开始评估熔断，默认 10 次
        """
        self.state = CircuitState.CLOSED
        self.failure_threshold = failure_threshold
        self.consecutive_failures = consecutive_failures
        self.recovery_timeout = recovery_timeout  # 秒
        self.half_open_requests = half_open_requests
        self.min_requests = min_requests
        
        # 状态变量
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.half_open_successes = 0
        
        # 滑动窗口数据
        self.requests_window: Deque[bool] = deque(maxlen=100)  # 存储最近 100 次请求的成功状态
        self.response_times: Deque[float] = deque(maxlen=100)  # 存储最近 100 次请求的响应时间
    
    def record_success(self, response_time: float = 0.0):
        """记录成功调用
        
        Args:
            response_time: 响应时间（毫秒）
        """
        self.requests_window.append(True)
        self.response_times.append(response_time)
        
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self._transition_to_closed()
        else:
            self.failure_count = 0
            self.success_count += 1
    
    def record_failure(self, response_time: float = 0.0):
        """记录失败调用
        
        Args:
            response_time: 响应时间（毫秒）
        """
        self.requests_window.append(False)
        self.response_times.append(response_time)
        
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            # 半开状态下失败，立即重新熔断
            self.state = CircuitState.OPEN
        elif (self.failure_count >= self.consecutive_failures or
              self._calculate_failure_rate() > self.failure_threshold):
            # 达到熔断条件
            self.state = CircuitState.OPEN
    
    def allow_request(self) -> bool:
        """判断是否允许请求
        
        Returns:
            bool: 是否允许请求
        """
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_successes = 0
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def _calculate_failure_rate(self) -> float:
        """计算 1 分钟滑动窗口的错误率
        
        Returns:
            float: 错误率（0-1）
        """
        if len(self.requests_window) < self.min_requests:
            return 0.0
        
        failure_count = sum(1 for success in self.requests_window if not success)
        return failure_count / len(self.requests_window)
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置熔断
        
        Returns:
            bool: 是否应该尝试重置
        """
        if not self.last_failure_time:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _transition_to_closed(self):
        """转换到关闭状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_successes = 0
        # 清空窗口数据，开始新的评估周期
        self.requests_window.clear()
        self.response_times.clear()
    
    def get_state(self) -> CircuitState:
        """获取当前状态
        
        Returns:
            CircuitState: 当前状态
        """
        return self.state
    
    def get_failure_rate(self) -> float:
        """获取当前错误率
        
        Returns:
            float: 错误率
        """
        return self._calculate_failure_rate()
    
    def get_avg_response_time(self) -> float:
        """获取平均响应时间
        
        Returns:
            float: 平均响应时间（毫秒）
        """
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    def reset(self):
        """重置熔断器状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_successes = 0
        self.requests_window.clear()
        self.response_times.clear()


class CircuitBreakerService:
    """熔断器服务"""
    
    def __init__(self):
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}  # model_id -> CircuitBreaker
    
    def get_circuit_breaker(self, model_id: str) -> CircuitBreaker:
        """获取或创建熔断器
        
        Args:
            model_id: 模型 ID
        
        Returns:
            CircuitBreaker: 熔断器实例
        """
        if model_id not in self.circuit_breakers:
            self.circuit_breakers[model_id] = CircuitBreaker()
        return self.circuit_breakers[model_id]
    
    async def record_call_result(self, model_id: str, success: bool, response_time: float = 0.0):
        """记录调用结果
        
        Args:
            model_id: 模型 ID
            success: 是否成功
            response_time: 响应时间（毫秒）
        """
        circuit_breaker = self.get_circuit_breaker(model_id)
        if success:
            circuit_breaker.record_success(response_time)
        else:
            circuit_breaker.record_failure(response_time)
    
    async def should_allow_request(self, model_id: str) -> bool:
        """判断是否允许请求
        
        Args:
            model_id: 模型 ID
        
        Returns:
            bool: 是否允许请求
        """
        circuit_breaker = self.get_circuit_breaker(model_id)
        return circuit_breaker.allow_request()
    
    async def get_circuit_state(self, model_id: str) -> CircuitState:
        """获取熔断器状态
        
        Args:
            model_id: 模型 ID
        
        Returns:
            CircuitState: 熔断器状态
        """
        circuit_breaker = self.get_circuit_breaker(model_id)
        return circuit_breaker.get_state()
    
    async def get_failure_rate(self, model_id: str) -> float:
        """获取错误率
        
        Args:
            model_id: 模型 ID
        
        Returns:
            float: 错误率
        """
        circuit_breaker = self.get_circuit_breaker(model_id)
        return circuit_breaker.get_failure_rate()
    
    async def reset_circuit_breaker(self, model_id: str):
        """重置熔断器
        
        Args:
            model_id: 模型 ID
        """
        if model_id in self.circuit_breakers:
            self.circuit_breakers[model_id].reset()
    
    async def reset_all_circuit_breakers(self):
        """重置所有熔断器"""
        for model_id in self.circuit_breakers:
            self.circuit_breakers[model_id].reset()
    
    async def remove_circuit_breaker(self, model_id: str):
        """移除熔断器
        
        Args:
            model_id: 模型 ID
        """
        if model_id in self.circuit_breakers:
            del self.circuit_breakers[model_id]