from typing import Optional, List, Dict, Deque
from pydantic import BaseModel
from app.domain.llm.entities import ModelEntity
from app.domain.llm.enums import ModelType
from datetime import datetime, timedelta
import time
import asyncio
import random
from collections import deque


class HealthStatus(str):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HighAvailabilityResult(BaseModel):
    """高可用结果"""
    provider_id: str
    model_id: str
    model_instance: ModelEntity
    instance_id: str
    is_fallback: bool = False


class FallbackModel(BaseModel):
    """备用模型"""
    provider: str
    model: str
    weight: float = 1.0


class FallbackChain(BaseModel):
    """降级链"""
    primary_model: Dict[str, str]
    fallback_chain: List[FallbackModel]
    trigger_conditions: Dict[str, int]
    recovery: Dict[str, any]


class LoadBalanceStrategy:
    """负载均衡策略抽象基类"""
    
    async def select_instance(self, instances: List[ModelEntity]) -> Optional[ModelEntity]:
        """选择实例"""
        if not instances:
            return None
        healthy_instances = [i for i in instances if i.status]
        if not healthy_instances:
            return None
        return healthy_instances[0]
    
    def update_weights(self, weights: Dict[str, float]):
        """动态调整权重"""
        pass


class RoundRobinStrategy(LoadBalanceStrategy):
    """轮询策略"""
    def __init__(self):
        self.index = 0
    
    async def select_instance(self, instances: List[ModelEntity]) -> Optional[ModelEntity]:
        healthy_instances = [i for i in instances if i.status]
        if not healthy_instances:
            return None
        
        self.index = (self.index + 1) % len(healthy_instances)
        return healthy_instances[self.index]


class RandomStrategy(LoadBalanceStrategy):
    """随机策略"""
    async def select_instance(self, instances: List[ModelEntity]) -> Optional[ModelEntity]:
        healthy_instances = [i for i in instances if i.status]
        if not healthy_instances:
            return None
        return random.choice(healthy_instances)


class ResponseTimeStrategy(LoadBalanceStrategy):
    """响应时间策略"""
    def __init__(self, window_seconds=300):
        self.window_seconds = window_seconds
        self.response_times: Dict[str, Deque[float]] = {}
    
    async def select_instance(self, instances: List[ModelEntity]) -> Optional[ModelEntity]:
        healthy_instances = [i for i in instances if i.status]
        if not healthy_instances:
            return None
        
        # 选择平均响应时间最短的实例
        best_instance = min(
            healthy_instances,
            key=lambda i: self._get_avg_response_time(i.id)
        )
        return best_instance
    
    def record_response_time(self, instance_id: str, response_time_ms: float):
        """记录响应时间"""
        if instance_id not in self.response_times:
            self.response_times[instance_id] = deque(maxlen=100)
        self.response_times[instance_id].append(response_time_ms)
    
    def _get_avg_response_time(self, instance_id: str) -> float:
        """获取平均响应时间"""
        if instance_id not in self.response_times or not self.response_times[instance_id]:
            return float('inf')
        return sum(self.response_times[instance_id]) / len(self.response_times[instance_id])


class WeightedRoundRobinStrategy(LoadBalanceStrategy):
    """加权轮询策略"""
    def __init__(self):
        self.weights: Dict[str, float] = {}
    
    async def select_instance(self, instances: List[ModelEntity]) -> Optional[ModelEntity]:
        healthy_instances = [i for i in instances if i.status]
        if not healthy_instances:
            return None
        
        # 按权重排序，选择权重最高的实例
        best_instance = max(healthy_instances, key=lambda i: self.weights.get(i.id, 1.0))
        return best_instance
    
    def update_weights(self, weights: Dict[str, float]):
        """动态调整权重"""
        self.weights.update(weights)


class HighAvailabilityDomainService:
    """高可用领域服务"""
    
    def __init__(self):
        self.load_balance_strategy = RoundRobinStrategy()
        self.model_health: Dict[str, Dict] = {}
        self.session_affinity: Dict[str, str] = {}  # session_id -> model_id
        self.fallback_chains: Dict[str, FallbackChain] = {}
        self.response_time_strategy = ResponseTimeStrategy()
    
    async def sync_model_to_gateway(self, model: ModelEntity) -> None:
        """同步模型到网关"""
        # 模拟同步操作
        await asyncio.sleep(0.01)
        print(f"Synced model {model.model_id} to gateway")
    
    async def remove_model_from_gateway(self, model_id: str) -> None:
        """从网关移除模型"""
        # 模拟移除操作
        await asyncio.sleep(0.01)
        print(f"Removed model {model_id} from gateway")
    
    async def update_model_in_gateway(self, model: ModelEntity) -> None:
        """更新网关中的模型"""
        # 模拟更新操作
        await asyncio.sleep(0.01)
        print(f"Updated model {model.model_id} in gateway")
    
    async def batch_remove_models_from_gateway(self, model_ids: List[str]) -> None:
        """批量从网关移除模型"""
        # 模拟批量移除操作
        await asyncio.sleep(0.01)
        print(f"Batch removed models {model_ids} from gateway")
    
    async def sync_all_models_to_gateway(self) -> None:
        """同步所有模型到网关"""
        # 模拟同步操作
        await asyncio.sleep(0.01)
        print("Synced all models to gateway")
    
    async def initialize_project(self) -> None:
        """初始化项目"""
        # 模拟初始化操作
        await asyncio.sleep(0.01)
        print("Initialized project")
    
    async def select_best_provider(
        self,
        model_type: ModelType,
        session_id: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None
    ) -> HighAvailabilityResult:
        """选择最佳服务商和模型"""
        # 1. 检查会话亲和性
        if session_id and session_id in self.session_affinity:
            model_id = self.session_affinity[session_id]
            # 尝试获取该模型
            model = await self._get_model_by_id(model_id)
            if model and model.status:
                return HighAvailabilityResult(
                    provider_id=model.provider_id,
                    model_id=model.model_id,
                    model_instance=model,
                    instance_id=f"instance-{int(time.time())}",
                    is_fallback=False
                )
        
        # 2. 从数据库获取可用模型
        available_models = await self._get_available_models(model_type)
        
        # 3. 应用负载均衡策略选择模型
        selected_model = await self.load_balance_strategy.select_instance(available_models)
        
        if not selected_model:
            # 4. 尝试降级链
            if fallback_chain:
                selected_model = await self._select_from_fallback_chain(fallback_chain, model_type)
                if selected_model:
                    return HighAvailabilityResult(
                        provider_id=selected_model.provider_id,
                        model_id=selected_model.model_id,
                        model_instance=selected_model,
                        instance_id=f"instance-{int(time.time())}",
                        is_fallback=True
                    )
            # 5. 无可用模型，返回默认模型
            selected_model = await self._get_default_model(model_type)
        
        # 6. 记录会话亲和性
        if session_id:
            self.session_affinity[session_id] = selected_model.id
            # 设置过期时间（1小时）
            asyncio.create_task(self._expire_session_affinity(session_id, 3600))
        
        return HighAvailabilityResult(
            provider_id=selected_model.provider_id,
            model_id=selected_model.model_id,
            model_instance=selected_model,
            instance_id=f"instance-{int(time.time())}",
            is_fallback=False
        )
    
    async def report_call_result(
        self,
        model_id: str,
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None
    ) -> None:
        """上报调用结果"""
        # 记录响应时间
        self.response_time_strategy.record_response_time(model_id, latency_ms)
        
        # 更新健康状态
        self.model_health[model_id] = {
            "last_call": time.time(),
            "success": success,
            "latency": latency_ms,
            "error": error_message,
            "health_status": HealthStatus.HEALTHY if success else HealthStatus.DEGRADED
        }
        
        print(f"Reported call result for model {model_id}: success={success}, latency={latency_ms}ms")
    
    async def _get_model_by_id(self, model_id: str) -> Optional[ModelEntity]:
        """根据ID获取模型"""
        # 模拟从数据库获取模型
        await asyncio.sleep(0.01)
        # 这里应该从数据库查询，现在返回模拟数据
        return ModelEntity(
            id=model_id,
            user_id="system",
            provider_id="mock-provider-1",
            model_id="gpt-4",
            name="GPT-4",
            type=ModelType.CHAT,
            status=True
        )
    
    async def _get_available_models(self, model_type: ModelType) -> List[ModelEntity]:
        """获取可用模型"""
        # 模拟从数据库获取可用模型
        await asyncio.sleep(0.01)
        # 这里应该从数据库查询，现在返回模拟数据
        return [
            ModelEntity(
                id="model-1",
                user_id="system",
                provider_id="openai",
                model_id="gpt-4",
                name="GPT-4",
                type=model_type,
                status=True
            ),
            ModelEntity(
                id="model-2",
                user_id="system",
                provider_id="openai",
                model_id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                type=model_type,
                status=True
            ),
            ModelEntity(
                id="model-3",
                user_id="system",
                provider_id="anthropic",
                model_id="claude-3-sonnet",
                name="Claude 3 Sonnet",
                type=model_type,
                status=True
            )
        ]
    
    async def _select_from_fallback_chain(self, fallback_chain: List[str], model_type: ModelType) -> Optional[ModelEntity]:
        """从降级链选择模型"""
        for model_id in fallback_chain:
            model = await self._get_model_by_id(model_id)
            if model and model.status:
                return model
        return None
    
    async def _get_default_model(self, model_type: ModelType) -> ModelEntity:
        """获取默认模型"""
        # 模拟默认模型
        return ModelEntity(
            id="default-model",
            user_id="system",
            provider_id="openai",
            model_id="gpt-3.5-turbo",
            name="GPT-3.5 Turbo (Default)",
            type=model_type,
            status=True
        )
    
    async def _expire_session_affinity(self, session_id: str, seconds: int):
        """过期会话亲和性"""
        await asyncio.sleep(seconds)
        if session_id in self.session_affinity:
            del self.session_affinity[session_id]
    
    def set_load_balance_strategy(self, strategy: LoadBalanceStrategy):
        """设置负载均衡策略"""
        self.load_balance_strategy = strategy
    
    def add_fallback_chain(self, chain_name: str, fallback_chain: FallbackChain):
        """添加降级链"""
        self.fallback_chains[chain_name] = fallback_chain
    
    async def check_model_health(self, model_id: str) -> HealthStatus:
        """检查模型健康状态"""
        if model_id not in self.model_health:
            return HealthStatus.HEALTHY
        
        health_data = self.model_health[model_id]
        return health_data.get("health_status", HealthStatus.HEALTHY)
