from abc import ABC, abstractmethod
from typing import List, Optional, Dict
import asyncio
import httpx
import time
from datetime import datetime

from app.domain.llm.entities import ModelEntity
from app.domain.llm.high_availability import HealthStatus


class HealthChecker(ABC):
    """健康检查器抽象基类"""
    
    @abstractmethod
    async def check(self, instance: ModelEntity) -> HealthStatus:
        """执行健康检查
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        pass
    
    @abstractmethod
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔
        """
        pass


class HTTPHealthChecker(HealthChecker):
    """HTTP 健康检查器"""
    
    def __init__(self, timeout_ms: int = 5000):
        """初始化 HTTP 健康检查器
        
        Args:
            timeout_ms: 超时时间（毫秒）
        """
        self.timeout_ms = timeout_ms
    
    async def check(self, instance: ModelEntity) -> HealthStatus:
        """执行 HTTP 健康检查
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        try:
            # 构建健康检查 URL
            base_url = getattr(instance, 'base_url', '') or 'http://localhost:8000'
            health_url = f"{base_url}/health"
            
            async with httpx.AsyncClient(timeout=self.timeout_ms / 1000) as client:
                response = await client.get(health_url)
                if response.status_code == 200:
                    return HealthStatus.HEALTHY
                return HealthStatus.DEGRADED
        except Exception as e:
            print(f"HTTP Probe failed for model {instance.model_id}: {e}")
            return HealthStatus.UNHEALTHY
    
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔
        """
        return 30


class InferenceHealthChecker(HealthChecker):
    """推理健康检查器"""
    
    def __init__(self, timeout_ms: int = 10000):
        """初始化推理健康检查器
        
        Args:
            timeout_ms: 超时时间（毫秒）
        """
        self.timeout_ms = timeout_ms
    
    async def check(self, instance: ModelEntity) -> HealthStatus:
        """执行推理健康检查
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        try:
            # 构建推理 URL
            base_url = getattr(instance, 'base_url', '') or 'http://localhost:8000'
            inference_url = f"{base_url}/chat/completions"
            
            # 准备测试请求
            test_request = {
                "model": instance.model_id,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 1
            }
            
            # 准备 headers
            headers = {}
            if hasattr(instance, 'api_key') and instance.api_key:
                headers["Authorization"] = f"Bearer {instance.api_key}"
            
            async with httpx.AsyncClient(timeout=self.timeout_ms / 1000) as client:
                response = await client.post(inference_url, json=test_request, headers=headers)
                if response.status_code == 200:
                    return HealthStatus.HEALTHY
                return HealthStatus.DEGRADED
        except Exception as e:
            print(f"Inference Probe failed for model {instance.model_id}: {e}")
            return HealthStatus.UNHEALTHY
    
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔
        """
        return 60


class TCPHealthChecker(HealthChecker):
    """TCP 健康检查器"""
    
    def __init__(self, timeout_ms: int = 3000):
        """初始化 TCP 健康检查器
        
        Args:
            timeout_ms: 超时时间（毫秒）
        """
        self.timeout_ms = timeout_ms
    
    async def check(self, instance: ModelEntity) -> HealthStatus:
        """执行 TCP 健康检查
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        try:
            # 从 base_url 提取 host 和 port
            base_url = getattr(instance, 'base_url', '') or 'http://localhost:8000'
            # 简单解析，实际应该使用 urlparse
            if base_url.startswith('http://'):
                host_port = base_url[7:]
            elif base_url.startswith('https://'):
                host_port = base_url[8:]
            else:
                host_port = base_url
            
            # 提取 host 和 port
            if ':' in host_port:
                host, port_str = host_port.split(':', 1)
                port = int(port_str)
            else:
                host = host_port
                port = 80 if base_url.startswith('http://') else 443
            
            # 尝试建立 TCP 连接
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port),
                timeout=self.timeout_ms / 1000
            )
            writer.close()
            await writer.wait_closed()
            return HealthStatus.HEALTHY
        except Exception as e:
            print(f"TCP Probe failed for model {instance.model_id}: {e}")
            return HealthStatus.UNHEALTHY
    
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔
        """
        return 15


class CompositeHealthChecker(HealthChecker):
    """组合健康检查器"""
    
    def __init__(self):
        """初始化组合健康检查器"""
        self.checkers = [
            HTTPHealthChecker(),
            InferenceHealthChecker(),
            TCPHealthChecker()
        ]
    
    async def check(self, instance: ModelEntity) -> HealthStatus:
        """执行组合健康检查
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        # 按优先级执行检查
        for checker in self.checkers:
            status = await checker.check(instance)
            if status == HealthStatus.HEALTHY:
                return HealthStatus.HEALTHY
        # 所有检查都失败
        return HealthStatus.UNHEALTHY
    
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）
        
        Returns:
            int: 检查间隔
        """
        # 使用最短的检查间隔
        return min(checker.get_check_interval() for checker in self.checkers)


class HealthCheckScheduler:
    """健康检查调度器"""
    
    def __init__(self, max_concurrent: int = 100):
        """初始化健康检查调度器
        
        Args:
            max_concurrent: 最大并发数
        """
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.checker = CompositeHealthChecker()
        self.instance_health: Dict[str, Dict] = {}  # model_id -> health info
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动健康检查调度器"""
        if self.is_running:
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._schedule_checks())
        print("Health check scheduler started")
    
    async def stop(self):
        """停止健康检查调度器"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("Health check scheduler stopped")
    
    async def _schedule_checks(self):
        """调度健康检查"""
        interval = self.checker.get_check_interval()
        while self.is_running:
            try:
                # 获取所有实例
                instances = await self._get_all_instances()
                if instances:
                    # 并发执行健康检查
                    await self.check_all_instances(instances)
            except Exception as e:
                print(f"Error in health check scheduler: {e}")
            
            # 等待下一次检查
            await asyncio.sleep(interval)
    
    async def check_all_instances(self, instances: List[ModelEntity]):
        """并发检查所有实例
        
        Args:
            instances: 模型实例列表
        """
        tasks = []
        for instance in instances:
            task = self._check_with_semaphore(instance)
            tasks.append(task)
        
        # 等待所有检查完成
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理检查结果
        for instance, result in zip(instances, results):
            if isinstance(result, Exception):
                print(f"Health check failed for model {instance.model_id}: {result}")
                self._update_health_status(instance.id, HealthStatus.UNHEALTHY)
            else:
                self._update_health_status(instance.id, result)
    
    async def _check_with_semaphore(self, instance: ModelEntity) -> HealthStatus:
        """使用信号量控制并发
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        async with self.semaphore:
            return await self.check_single_instance(instance)
    
    async def check_single_instance(self, instance: ModelEntity) -> HealthStatus:
        """检查单个实例
        
        Args:
            instance: 模型实例
        
        Returns:
            HealthStatus: 健康状态
        """
        # 执行健康检查，支持重试
        max_retries = 2
        retry_interval = 3  # 秒
        
        for attempt in range(max_retries + 1):
            status = await self.checker.check(instance)
            if status == HealthStatus.HEALTHY:
                return status
            
            if attempt < max_retries:
                print(f"Health check failed for model {instance.model_id}, retrying in {retry_interval}s...")
                await asyncio.sleep(retry_interval)
        
        return status
    
    async def _get_all_instances(self) -> List[ModelEntity]:
        """获取所有实例
        
        Returns:
            List[ModelEntity]: 模型实例列表
        """
        # 模拟从数据库获取所有实例
        await asyncio.sleep(0.01)
        # 这里应该从数据库查询，现在返回模拟数据
        from app.domain.llm.enums import ModelType
        return [
            ModelEntity(
                id="model-1",
                user_id="system",
                provider_id="openai",
                model_id="gpt-4",
                name="GPT-4",
                type=ModelType.CHAT,
                status=True
            ),
            ModelEntity(
                id="model-2",
                user_id="system",
                provider_id="openai",
                model_id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                type=ModelType.CHAT,
                status=True
            ),
            ModelEntity(
                id="model-3",
                user_id="system",
                provider_id="anthropic",
                model_id="claude-3-sonnet",
                name="Claude 3 Sonnet",
                type=ModelType.CHAT,
                status=True
            )
        ]
    
    def _update_health_status(self, model_id: str, status: HealthStatus):
        """更新健康状态
        
        Args:
            model_id: 模型 ID
            status: 健康状态
        """
        self.instance_health[model_id] = {
            "status": status,
            "last_check": datetime.now().isoformat()
        }
        print(f"Updated health status for model {model_id}: {status}")
    
    def get_health_status(self, model_id: str) -> Optional[HealthStatus]:
        """获取健康状态
        
        Args:
            model_id: 模型 ID
        
        Returns:
            Optional[HealthStatus]: 健康状态
        """
        if model_id not in self.instance_health:
            return None
        return self.instance_health[model_id]["status"]
    
    def get_all_health_statuses(self) -> Dict[str, HealthStatus]:
        """获取所有实例的健康状态
        
        Returns:
            Dict[str, HealthStatus]: 模型 ID 到健康状态的映射
        """
        return {
            model_id: info["status"]
            for model_id, info in self.instance_health.items()
        }
    
    def pause(self):
        """暂停健康检查（紧急停止）"""
        self.is_running = False
        print("Health check scheduler paused")
    
    def resume(self):
        """恢复健康检查"""
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self._schedule_checks())
            print("Health check scheduler resumed")