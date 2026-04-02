from typing import List, Dict, Optional
from pydantic import BaseModel
import asyncio
import time

from app.domain.llm.entities import ModelEntity
from app.domain.llm.high_availability import HealthStatus


class FallbackModel(BaseModel):
    """备用模型"""
    provider: str
    model: str
    weight: float = 1.0


class FallbackTriggerConditions(BaseModel):
    """降级触发条件"""
    consecutive_failures: int = 3
    error_rate_threshold: float = 0.5
    timeout_threshold_ms: int = 30000


class RecoveryConfig(BaseModel):
    """恢复配置"""
    auto_recovery: bool = True
    recovery_delay_seconds: int = 300  # 5 分钟
    health_check_interval_seconds: int = 30


class FallbackChain(BaseModel):
    """降级链"""
    primary_model: Dict[str, str]
    fallback_chain: List[FallbackModel]
    trigger_conditions: FallbackTriggerConditions
    recovery: RecoveryConfig


class FallbackChainManager:
    """降级链管理器"""
    
    def __init__(self):
        """初始化降级链管理器"""
        self.fallback_chains: Dict[str, FallbackChain] = {}  # chain_name -> FallbackChain
        self.chain_status: Dict[str, Dict] = {}  # chain_name -> status
        self.recovery_tasks: Dict[str, asyncio.Task] = {}  # chain_name -> recovery task
    
    def add_fallback_chain(self, chain_name: str, fallback_chain: FallbackChain):
        """添加降级链
        
        Args:
            chain_name: 降级链名称
            fallback_chain: 降级链配置
        """
        self.fallback_chains[chain_name] = fallback_chain
        self.chain_status[chain_name] = {
            "current_index": 0,  # 0 表示使用主模型
            "failure_count": 0,
            "last_failure_time": None,
            "is_degraded": False
        }
    
    def remove_fallback_chain(self, chain_name: str):
        """移除降级链
        
        Args:
            chain_name: 降级链名称
        """
        if chain_name in self.fallback_chains:
            del self.fallback_chains[chain_name]
        if chain_name in self.chain_status:
            del self.chain_status[chain_name]
        if chain_name in self.recovery_tasks:
            self.recovery_tasks[chain_name].cancel()
            del self.recovery_tasks[chain_name]
    
    async def execute_with_fallback(
        self,
        chain_name: str,
        execute_func,
        *args,
        **kwargs
    ) -> any:
        """带降级链的执行逻辑
        
        Args:
            chain_name: 降级链名称
            execute_func: 执行函数
            *args: 函数参数
            **kwargs: 函数关键字参数
        
        Returns:
            any: 执行结果
        """
        if chain_name not in self.fallback_chains:
            raise ValueError(f"Fallback chain {chain_name} not found")
        
        fallback_chain = self.fallback_chains[chain_name]
        status = self.chain_status[chain_name]
        
        current_index = status["current_index"]
        max_retries = len(fallback_chain.fallback_chain)
        
        while current_index <= max_retries:
            try:
                # 获取当前模型配置
                if current_index == 0:
                    model_config = fallback_chain.primary_model
                    is_primary = True
                else:
                    model_config = fallback_chain.fallback_chain[current_index - 1]
                    is_primary = False
                
                # 执行函数
                result = await execute_func(model_config, *args, **kwargs)
                
                # 成功执行，重置失败计数
                status["failure_count"] = 0
                status["last_failure_time"] = None
                
                # 如果当前是降级状态，尝试切回主模型
                if status["is_degraded"] and is_primary:
                    status["is_degraded"] = False
                    status["current_index"] = 0
                    print(f"Switched back to primary model for chain {chain_name}")
                
                return result
                
            except Exception as e:
                print(f"Model execution failed: {e}")
                
                # 记录失败
                status["failure_count"] += 1
                status["last_failure_time"] = time.time()
                
                # 检查是否达到触发条件
                if self._should_trigger_fallback(status, fallback_chain.trigger_conditions):
                    current_index += 1
                    status["current_index"] = current_index
                    
                    if current_index > max_retries:
                        # 所有模型都失败
                        raise Exception("All models in fallback chain failed")
                    
                    # 进入降级状态
                    status["is_degraded"] = True
                    print(f"Falling back to model {current_index} for chain {chain_name}")
                    
                    # 启动恢复检测
                    self._start_recovery_check(chain_name)
                else:
                    # 未达到触发条件，继续重试当前模型
                    continue
    
    def _should_trigger_fallback(
        self,
        status: Dict,
        conditions: FallbackTriggerConditions
    ) -> bool:
        """判断是否应该触发降级
        
        Args:
            status: 降级链状态
            conditions: 触发条件
        
        Returns:
            bool: 是否应该触发降级
        """
        # 检查连续失败次数
        if status["failure_count"] >= conditions.consecutive_failures:
            return True
        
        # 其他触发条件可以在这里添加
        
        return False
    
    def _start_recovery_check(self, chain_name: str):
        """启动恢复检测
        
        Args:
            chain_name: 降级链名称
        """
        if chain_name in self.recovery_tasks and not self.recovery_tasks[chain_name].done():
            return
        
        self.recovery_tasks[chain_name] = asyncio.create_task(
            self._recovery_checker(chain_name)
        )
    
    async def _recovery_checker(self, chain_name: str):
        """恢复检测任务
        
        Args:
            chain_name: 降级链名称
        """
        if chain_name not in self.fallback_chains:
            return
        
        fallback_chain = self.fallback_chains[chain_name]
        interval = fallback_chain.recovery.health_check_interval_seconds
        
        while True:
            await asyncio.sleep(interval)
            
            if chain_name not in self.fallback_chains:
                break
            
            status = self.chain_status[chain_name]
            if not status["is_degraded"]:
                break
            
            # 检查主模型是否恢复
            primary_model = fallback_chain.primary_model
            try:
                # 这里应该调用健康检查函数
                # 模拟健康检查
                await asyncio.sleep(0.1)
                is_healthy = True  # 假设主模型已恢复
                
                if is_healthy:
                    # 切回主模型
                    status["is_degraded"] = False
                    status["current_index"] = 0
                    status["failure_count"] = 0
                    print(f"Primary model recovered for chain {chain_name}, switching back")
                    break
            except Exception as e:
                print(f"Recovery check failed: {e}")
                continue
    
    def get_chain_status(self, chain_name: str) -> Optional[Dict]:
        """获取降级链状态
        
        Args:
            chain_name: 降级链名称
        
        Returns:
            Optional[Dict]: 降级链状态
        """
        return self.chain_status.get(chain_name)
    
    def get_all_chain_statuses(self) -> Dict[str, Dict]:
        """获取所有降级链状态
        
        Returns:
            Dict[str, Dict]: 所有降级链状态
        """
        return self.chain_status
    
    def reset_chain(self, chain_name: str):
        """重置降级链
        
        Args:
            chain_name: 降级链名称
        """
        if chain_name in self.chain_status:
            self.chain_status[chain_name] = {
                "current_index": 0,
                "failure_count": 0,
                "last_failure_time": None,
                "is_degraded": False
            }
        if chain_name in self.recovery_tasks:
            self.recovery_tasks[chain_name].cancel()
            del self.recovery_tasks[chain_name]
    
    async def check_primary_health(self, chain_name: str) -> HealthStatus:
        """检查主模型健康状态
        
        Args:
            chain_name: 降级链名称
        
        Returns:
            HealthStatus: 健康状态
        """
        if chain_name not in self.fallback_chains:
            return HealthStatus.UNHEALTHY
        
        # 这里应该调用健康检查函数
        # 模拟健康检查
        await asyncio.sleep(0.1)
        return HealthStatus.HEALTHY