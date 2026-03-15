# 高可用 (High Availability) - 设计文档

## 架构设计

### 整体架构

高可用模块采用**独立 FastAPI 微服务 + nginx upstream**的部署形态，提供故障切换、负载均衡和健康检查能力。系统包含三层架构:

**基础设施层**:
- **高可用网关服务**:独立部署的 FastAPI 应用，负责实例选择、健康检查和故障转移
- **nginx 反向代理**:使用 nginx upstream 模块实现请求路由和负载均衡
- **Redis 集群**:存储健康状态、分布式锁和缓存
- **RabbitMQ**:事件广播和异步通知

**领域服务层**:
- **HighAvailabilityDomainService**:核心业务逻辑决策，包括健康评估、故障判断和降级策略
- **CircuitBreakerService**:熔断器管理，实现熔断模式
- **WeightAdjustmentService**:动态权重调整，基于响应时间和错误率

**应用层**:
- **HAConfigService**:高可用配置管理，支持热加载
- **AlertService**:告警服务，多渠道通知
- **ManualControlService**:手动干预接口，供管理员使用

### 核心组件

**HighAvailabilityGateway**(高可用网关):
- 作为独立 FastAPI 服务部署，端口 8080
- 提供 REST API: `/select`, `/report`, `/health`
- 集成本地降级逻辑，当网关不可用时自动降级
- 使用 httpx 异步客户端调用 LLM 模型

**HighAvailabilityDomainService**(领域服务):
- 封装高可用业务逻辑，不依赖具体基础设施
- 与网关服务通信，同步模型配置
- 实现降级链逻辑，支持循环检测和手动干预
- 监听领域事件，触发配置同步

**CircuitBreakerService**(熔断器服务):
- 状态机实现：CLOSED → OPEN → HALF_OPEN → CLOSED
- 错误率计算：1 分钟滑动窗口，统计错误率和平均响应时间
- 熔断触发：错误率>50% 或连续失败>10 次
- 半开探测：放行 3 个请求，全部成功后恢复
- 配置参数可动态调整

**HealthCheckScheduler**(健康检查调度器):
- 使用 APScheduler 定时调度，默认 30 秒间隔
- 并发控制：信号量限制最大并发 100 个探测
- 多种探测方式：HTTP Probe(5s 超时)、推理探针 (10s 超时)、TCP 探测
- 失败重试：最多 2 次，间隔 3 秒
- 紧急停止：遇到大规模故障时暂停探测

**AlertService**(告警服务):
- 支持 P0-P3 四个告警级别
- 多渠道集成：邮件、短信、Slack、钉钉、企业微信、Webhook
- 告警收敛：相同告警 5 分钟内合并，1 小时最多发送 10 条
- 告警规则模板：Prometheus Rule 格式，便于集成监控系统

## 设计模式

**网关模式**:
通过 HighAvailabilityGateway 封装跨领域的复杂交互，提供统一的 REST API 接口。主应用通过调用网关 API 实现模型选择，屏蔽底层多实例管理和健康检查细节。网关不可用时自动降级到本地逻辑。

**监听器模式**:
HighAvailabilityEventListener 监听模型生命周期事件（ModelCreatedEvent、ModelDeletedEvent 等），事件触发后异步执行同步操作，将模型配置同步到网关。解耦模型管理和高可用逻辑，提高系统可扩展性。

**降级模式**:
在网关不可用、选择超时或无健康实例时，降级到本地默认逻辑。优先使用高可用网关选择实例，网关不可用时降级到配置的默认模型。降级过程记录详细日志并触发告警。

**熔断模式**:
CircuitBreakerService 实现熔断器模式，防止雪崩效应。每个模型实例独立维护熔断状态，基于错误率和响应时间自动触发熔断。半开状态下谨慎探测，确认恢复后重新加入可用池。

**分布式锁模式**:
使用 Redis RedLock 算法实现分布式锁，防止多实例同时执行故障切换。锁超时时间 30 秒，支持自动过期避免死锁。故障切换前必须先获取锁，确保操作的原子性。

## 技术实现

### 1. 高可用网关服务实现

**网关启动流程**:
```python
# main.py
from fastapi import FastAPI
from app.gateway import HighAvailabilityGateway
from app.scheduler import HealthCheckScheduler

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # 初始化网关
    gateway = HighAvailabilityGateway()
    await gateway.initialize()
    
    # 启动健康检查调度器
    scheduler = HealthCheckScheduler()
    scheduler.start()
    
    # 从数据库加载模型配置
    await gateway.load_models_from_db()

@app.on_event("shutdown")
async def shutdown_event():
    # 优雅关闭
    await gateway.close()
    scheduler.stop()
```

**模型同步到网关**:
```python
# 创建 ApiInstance 并注册到网关
async def sync_model_to_gateway(model: ModelAggregate):
    request = ApiInstanceCreateRequest(
        instance_id=model.id,
        provider=model.provider.name,
        model=model.model_endpoint,
        api_key=decrypt(model.provider.config.api_key),
        base_url=model.provider.config.base_url,
        weight=model.weight,
        status=model.status
    )
    
    # 异步调用网关 API，不阻塞主流程
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://ha-gateway:8080/api/v1/instances",
            json=request.dict()
        )
```

**最佳实例选择**:
```python
# 构建选择请求并调用网关
async def select_best_instance(user_id: str, model_type: str) -> ApiInstanceDTO:
    request = SelectInstanceRequest(
        user_id=user_id,
        model_type=model_type,
        session_id=session_id  # 用于会话亲和性
    )
    
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            response = await client.post(
                "http://ha-gateway:8080/api/v1/select",
                json=request.dict()
            )
            return ApiInstanceDTO.parse_obj(response.json())
    except Exception as e:
        # 降级到本地逻辑
        logger.warning(f"网关选择失败，降级：{e}")
        return await fallback_select_local(model_type)
```

### 2. 熔断器实现

**状态机设计**:
```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open" # 半开状态

class CircuitBreaker:
    def __init__(self, failure_threshold=0.5, consecutive_failures=10,
                 recovery_timeout=60, half_open_requests=3):
        self.state = CircuitState.CLOSED
        self.failure_threshold = failure_threshold
        self.consecutive_failures = consecutive_failures
        self.recovery_timeout = recovery_timeout  # 秒
        self.half_open_requests = half_open_requests
        
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.half_open_successes = 0
    
    def record_success(self):
        """记录成功调用"""
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_successes += 1
            if self.half_open_successes >= self.half_open_requests:
                self._transition_to_closed()
        else:
            self.failure_count = 0
    
    def record_failure(self):
        """记录失败调用"""
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
        """判断是否允许请求"""
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
        """计算 1 分钟滑动窗口的错误率"""
        # 实现滑动窗口统计
        pass
    
    def _should_attempt_reset(self) -> bool:
        """判断是否应该尝试重置熔断"""
        if not self.last_failure_time:
            return False
        return datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout)
    
    def _transition_to_closed(self):
        """转换到关闭状态"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.half_open_successes = 0
```

### 3. 降级链实现

**降级配置模型**:
```python
class FallbackChain(BaseModel):
    primary_model: ModelReference
    fallback_chain: List[FallbackModel]
    trigger_conditions: FallbackTriggerConditions
    recovery: RecoveryConfig

class FallbackModel(BaseModel):
    provider: str
    model: str
    weight: float = 1.0  # 权重 0.0-1.0

class FallbackTriggerConditions(BaseModel):
    consecutive_failures: int = 3
    error_rate_threshold: float = 0.5
    timeout_threshold_ms: int = 30000

class RecoveryConfig(BaseModel):
    auto_recovery: bool = True
    recovery_delay_seconds: int = 300  # 5 分钟
    health_check_interval_seconds: int = 30
```

**降级执行逻辑**:
```python
async def execute_with_fallback(
    request: LLMRequest,
    fallback_chain: FallbackChain
) -> LLMResponse:
    """带降级链的执行逻辑"""
    current_index = 0
    max_retries = len(fallback_chain.fallback_chain)
    
    while current_index <= max_retries:
        try:
            # 获取当前模型
            if current_index == 0:
                model_ref = fallback_chain.primary_model
            else:
                model_ref = fallback_chain.fallback_chain[current_index - 1]
            
            # 调用模型
            response = await call_llm(model_ref, request)
            
            # 成功则返回
            if current_index > 0:
                logger.info(f"降级到第{current_index}个备用模型成功")
            return response
            
        except Exception as e:
            logger.warning(f"模型调用失败：{model_ref}, error={e}")
            
            # 记录失败指标
            await metrics.record_failure(model_ref)
            
            # 检查是否达到触发条件
            if await should_trigger_fallback(model_ref, fallback_chain.trigger_conditions):
                current_index += 1
                
                if current_index > max_retries:
                    # 所有模型都失败
                    raise MaxRetriesExceededError("所有模型调用失败")
            else:
                # 未达到触发条件，继续重试
                continue
    
    raise MaxRetriesExceededError("超出最大重试次数")
```

**循环检测机制**:
```python
async def recovery_checker():
    """定期检测主模型是否恢复"""
    while True:
        await asyncio.sleep(300)  # 每 5 分钟检查一次
        
        # 获取所有降级的模型链
        degraded_chains = await get_degraded_chains()
        
        for chain in degraded_chains:
            if chain.recovery.auto_recovery:
                # 健康检查主模型
                health_status = await check_model_health(chain.primary_model)
                
                if health_status.is_healthy:
                    # 主模型恢复，切回
                    logger.info(f"主模型恢复：{chain.primary_model}")
                    await switch_to_primary(chain)
                    await alert_service.send_recovery_alert(chain.primary_model)
```

### 4. 健康检查实现

**多种探测方式**:
```python
class HealthChecker:
    async def http_probe(self, instance: ModelInstance) -> HealthStatus:
        """HTTP 探测：发送轻量 GET 请求到健康端点"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{instance.base_url}/health")
                if response.status_code == 200:
                    return HealthStatus.HEALTHY
                return HealthStatus.DEGRADED
        except Exception as e:
            logger.debug(f"HTTP Probe 失败：{e}")
            return HealthStatus.UNHEALTHY
    
    async def inference_probe(self, instance: ModelInstance) -> HealthStatus:
        """推理探针：发送最小化推理请求验证实际能力"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                test_request = {
                    "model": instance.model,
                    "messages": [{"role": "user", "content": "Hi"}],
                    "max_tokens": 1
                }
                response = await client.post(
                    f"{instance.base_url}/chat/completions",
                    headers={"Authorization": f"Bearer {instance.api_key}"},
                    json=test_request
                )
                if response.status_code == 200:
                    return HealthStatus.HEALTHY
                return HealthStatus.DEGRADED
        except Exception as e:
            logger.debug(f"推理探针失败：{e}")
            return HealthStatus.UNHEALTHY
    
    async def tcp_probe(self, instance: ModelInstance) -> HealthStatus:
        """TCP 探测：仅检测端口连通性"""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(instance.host, instance.port),
                timeout=3.0
            )
            writer.close()
            await writer.wait_closed()
            return HealthStatus.HEALTHY
        except Exception:
            return HealthStatus.UNHEALTHY
```

**并发控制**:
```python
class HealthCheckScheduler:
    def __init__(self, max_concurrent=100):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.scheduler = AsyncIOScheduler()
    
    async def check_all_instances(self):
        """并发检查所有实例，受信号量控制"""
        instances = await self.get_all_instances()
        
        tasks = []
        for instance in instances:
            task = self._check_with_semaphore(instance)
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _check_with_semaphore(self, instance: ModelInstance):
        """使用信号量控制并发"""
        async with self.semaphore:
            await self.check_single_instance(instance)
    
    def start(self):
        """启动定时任务"""
        self.scheduler.add_job(
            self.check_all_instances,
            'interval',
            seconds=30,
            id='health_check'
        )
        self.scheduler.start()
```

## 高可用网关设计

### 网关服务架构

**独立 FastAPI 服务**:
- 端口：8080
- 协议：HTTP/1.1, 支持 HTTP/2
- 认证：API Key + mTLS(可选)
- 部署：Docker 容器，Kubernetes 集群

**核心组件**:
1. **实例注册管理器**:管理模型实例的注册、更新和注销
2. **健康检查调度器**:APScheduler 定时调度，异步并发探测
3. **负载均衡选择器**:支持多种策略，动态权重调整
4. **熔断器管理器**:独立维护每个实例的熔断状态
5. **降级链执行器**:执行降级逻辑，循环检测恢复

**数据存储**:
- **Redis**:存储健康状态 (TTL 5 分钟)、分布式锁、实例选择缓存
- **PostgreSQL**:持久化配置、事件日志、审计记录
- **RabbitMQ**:事件广播、告警通知

### 健康检查策略

**主动检查**:
定期发送探测请求到所有实例，检查响应时间和可用性。
- HTTP Probe:5 秒超时，发送 GET /health
- 推理探针:10 秒超时，发送单 token 测试请求
- TCP 探测:3 秒超时，仅检测端口连通性

优先级：HTTP Probe > 推理探针 > TCP 探测

**被动检查**:
根据实际调用结果更新实例状态。
- 每次 LLM 调用后上报结果（成功/失败、延迟）
- 实时更新实例健康评分
- 触发熔断判断

**混合模式**:
主动检查发现异常时，增加被动检查权重；被动检查连续失败时，触发主动深度探测。

### 负载均衡算法

**轮询算法 (Round Robin)**:
```python
class RoundRobinStrategy(LoadBalanceStrategy):
    def __init__(self):
        self.index = 0
    
    def select_instance(self, instances: List[ModelInstance]) -> Optional[ModelInstance]:
        if not instances:
            return None
        
        healthy_instances = [i for i in instances if i.is_healthy]
        if not healthy_instances:
            return None
        
        self.index = (self.index + 1) % len(healthy_instances)
        return healthy_instances[self.index]
```

**响应时间算法 (Response Time)**:
```python
class ResponseTimeStrategy(LoadBalanceStrategy):
    def __init__(self, window_seconds=300):
        self.window_seconds = window_seconds
        self.response_times = {}  # instance_id -> deque of response times
    
    def select_instance(self, instances: List[ModelInstance]) -> Optional[ModelInstance]:
        healthy_instances = [i for i in instances if i.is_healthy]
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
```

**加权轮询算法 (Weighted Round Robin)**:
```python
class WeightedRoundRobinStrategy(LoadBalanceStrategy):
    def select_instance(self, instances: List[ModelInstance]) -> Optional[ModelInstance]:
        healthy_instances = [i for i in instances if i.is_healthy]
        if not healthy_instances:
            return None
        
        # 按权重排序，选择权重最高的实例
        best_instance = max(healthy_instances, key=lambda i: i.weight)
        return best_instance
```

### 配置设计

**高可用配置**:
```yaml
high_availability:
  gateway:
    host: "ha-gateway.internal"
    port: 8080
    protocol: "https"
    timeout_ms: 500
    retry_count: 2
  
  health_check:
    interval_seconds: 30
    timeout_http_ms: 5000
    timeout_inference_ms: 10000
    timeout_tcp_ms: 3000
    max_concurrent_probes: 100
    retry_count: 2
    retry_interval_ms: 3000
  
  circuit_breaker:
    failure_threshold: 0.5  # 错误率阈值 50%
    consecutive_failures: 10  # 连续失败次数
    recovery_timeout_seconds: 60  # 半开时间
    half_open_requests: 3  # 半开探测请求数
  
  affinity:
    type: "SESSION"  # SESSION, USER, NONE
    ttl_seconds: 3600
  
  load_balance:
    strategy: "RESPONSE_TIME"  # ROUND_ROBIN, RANDOM, LEAST_CONNECTIONS, RESPONSE_TIME
    dynamic_weight_adjustment: true
    weight_min: 0.1
    weight_max: 1.0
  
  fallback:
    enabled: true
    default_provider: "openai"
    default_model: "gpt-3.5-turbo"
  
  alert:
    enabled: true
    channels:
      - email
      - slack
      - webhook
    convergence_window_minutes: 5
    max_alerts_per_hour: 10
```

**降级链配置示例**:
```yaml
fallback_chains:
  - name: "gpt-4-fallback"
    primary:
      provider: "openai"
      model: "gpt-4"
    fallbacks:
      - provider: "openai"
        model: "gpt-3.5-turbo"
        weight: 1.0
      - provider: "anthropic"
        model: "claude-3-sonnet"
        weight: 0.9
      - provider: "moonshot"
        model: "moonshot-v1-8k"
        weight: 0.8
    trigger_conditions:
      consecutive_failures: 3
      error_rate_threshold: 0.5
      timeout_threshold_ms: 30000
    recovery:
      auto_recovery: true
      recovery_delay_seconds: 300
      health_check_interval_seconds: 30
```

## 负载均衡算法

轮询算法按顺序依次选择实例，响应时间算法选择平均响应时间最短的实例。选择算法可配置，支持按实际需求扩展。

## 配置设计

高可用配置包括网关连接参数、健康检查策略、亲和性类型和负载均衡策略。网关连接参数包括主机地址、端口、协议类型和超时时间。健康检查策略包括检查间隔、检查超时、失败阈值和成功阈值。亲和性类型支持 SESSION、USER 和 NONE 三种模式。负载均衡策略支持 ROUND_ROBIN、RANDOM、LEAST_CONNECTIONS 和 RESPONSE_TIME 四种算法。

## 关键流程

### 模型选择流程

1. **接收 LLM 调用请求**
   - 用户发起对话请求，包含 model_type 和 session_id

2. **检查高可用是否启用**
   - 未启用则直接使用默认模型

3. **构建 SelectInstanceRequest**
   ```python
   request = SelectInstanceRequest(
       user_id=user_id,
       model_type=model_type,
       session_id=session_id
   )
   ```

4. **调用网关 selectBestInstance**
   - 设置超时 500ms
   - 失败重试 2 次

5. **网关根据策略选择最佳实例**
   - 检查会话亲和性（绑定 session_id 的实例）
   - 过滤不健康实例
   - 应用负载均衡策略
   - 考虑动态权重

6. **返回 ApiInstanceDTO**
   - 包含 provider、model、base_url、api_key

7. **解析 Provider 和 Model**
   - 解密 api_key
   - 准备调用参数

8. **使用选中的实例进行调用**
   - 执行 LLM 推理

9. **调用结束上报结果到网关**
   - 上报成功/失败
   - 上报响应时间
   - 更新实例健康评分

### 故障切换流程

1. **网关健康检查发现实例异常**
   - HTTP Probe 连续失败 3 次
   - 或推理探针返回错误

2. **标记实例为不健康**
   - 更新 Redis 健康状态
   - 从可用实例池移除

3. **触发熔断器**
   - 错误率达到阈值
   - 熔断器状态：CLOSED → OPEN

4. **后续请求选择其他健康实例**
   - 负载均衡器跳过不健康实例
   - 选择下一个最佳实例

5. **发送告警通知**
   - 根据告警级别选择渠道
   - 告警收敛处理

6. **定期重新检查故障实例**
   - 健康检查调度器继续探测
   - 熔断器进入半开状态（60 秒后）

7. **实例恢复后重新加入可用池**
   - 半开状态下 3 次探测成功
   - 熔断器状态：OPEN → HALF_OPEN → CLOSED
   - 更新健康状态为 HEALTHY
   - 发送恢复告警

### 手动故障转移流程

1. **管理员调用手动切换 API**
   ```bash
   POST /api/v1/ha/manual/failover
   {
     "service_id": "svc_123",
     "target_instance_id": "inst_456",
     "reason": "计划内维护",
     "duration_minutes": 30
   }
   ```

2. **权限验证**
   - 校验管理员权限
   - 二次确认（防止误操作）

3. **获取分布式锁**
   - 防止并发操作

4. **执行切换**
   - 标记源实例为 UNHEALTHY
   - 激活目标实例

5. **记录审计日志**
   - 操作人、时间、原因

6. **发送告警通知**
   - P1 级别告警

7. **定时任务自动恢复**
   - duration 分钟后自动恢复源实例

## 错误处理

### 异常类型

**网关连接失败**:
- **场景**: 无法连接到高可用网关服务
- **处理**: 立即降级到本地默认逻辑，记录警告日志
- **告警**: P2 级别

**选择超时**:
- **场景**: 网关 500ms 内未响应
- **处理**: 使用默认实例，重试 2 次
- **告警**: P2 级别

**无健康实例**:
- **场景**: 所有实例都不健康
- **处理**: 返回错误或使用降级链最后一个备用模型
- **告警**: P0 级别（系统完全不可用）

**同步失败**:
- **场景**: 模型同步到网关失败
- **处理**: 记录错误日志，不影响主流程，下次定时同步重试
- **告警**: P3 级别

**熔断器打开**:
- **场景**: 实例触发熔断
- **处理**: 停止向该实例分发流量，等待自动恢复
- **告警**: P1 级别

**分布式锁获取失败**:
- **场景**: 多实例竞争锁失败
- **处理**: 放弃本次操作，记录日志
- **告警**: 无（正常并发控制）

### 降级策略

**一级降级**: 网关不可用，降级到本地逻辑
**二级降级**: 主模型不可用，降级到备用模型
**三级降级**: 所有模型不可用，返回友好错误提示

### 补偿机制

**调用失败补偿**: 记录失败请求，支持手动重试
**状态不一致补偿**: 定时对账任务，修复 Redis 和 DB 状态不一致
**事件丢失补偿**: 事件持久化 + 确认机制，确保可靠投递

## 性能优化

### 异步处理

**模型同步异步执行**:
- 使用 asyncio.create_task 异步同步，不阻塞主流程
- 失败自动重试（指数退避）

**结果上报异步处理**:
- 调用完成后异步上报结果
- 批量上报（积累 100 条或 10 秒后）

**健康检查异步调度**:
- APScheduler 异步调度器
- 协程池控制并发度

### 连接池

**HTTP 连接池**:
```python
# 使用 httpx 连接池，复用连接
client = httpx.AsyncClient(
    max_connections=1000,
    max_keepalive_connections=100,
    keepalive_expiry=300
)
```

**Redis 连接池**:
```python
# redis-py 连接池配置
redis_pool = redis.ConnectionPool(
    host='redis.internal',
    port=6379,
    max_connections=100,
    decode_responses=True
)
```

### 缓存策略

**实例选择缓存**:
- 缓存键：`select:{user_id}:{model_type}`
- TTL: 60 秒
- 状态变更时主动失效

**健康状态缓存**:
- 存储于 Redis，TTL 5 分钟
- 健康检查后更新
- 查询时优先读缓存

**配置缓存**:
- 降级链配置本地内存缓存
- 配置中心变更时推送更新

### 批处理

**批量上报**:
```python
class ResultReporter:
    def __init__(self, batch_size=100, flush_interval=10):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.buffer = []
    
    async def report(self, result: CallResult):
        self.buffer.append(result)
        if len(self.buffer) >= self.batch_size:
            await self.flush()
    
    async def flush(self):
        if not self.buffer:
            return
        
        # 批量发送到网关
        await gateway.report_batch(self.buffer)
        self.buffer.clear()
```

### 索引优化

**数据库索引**:
- `idx_service_health_status`: 加速健康状态查询
- `idx_ha_events_time`: 加速事件日志查询
- `idx_instance_user`: 加速用户实例过滤

## 监控指标

### 关键监控指标

**可用性指标**:
- 网关可用性 (%): 网关正常运行时间占比
- 实例健康率 (%): 健康实例数 / 总实例数
- 服务可用性 (%): 成功调用次数 / 总调用次数

**性能指标**:
- 平均响应时间 (ms): P50, P95, P99
- 模型选择延迟 (ms): 从请求到选中实例的时间
- 健康检查耗时 (ms): 单次探测耗时
- 故障切换时间 (ms): 检测到故障到切换完成

**容量指标**:
- QPS: 每秒请求数
- 并发连接数: 当前活跃连接数
- 实例数量: 注册的实例总数

**质量指标**:
- 调用成功率 (%): 成功调用占比
- 错误率 (%): 失败调用占比
- 降级触发次数: 降级发生的频率
- 熔断次数: 熔断器触发次数

### 告警规则

**P0 级别（严重）**:
- 网关不可用超过 1 分钟
- 所有实例不健康
- 降级频率 > 10 次/分钟

**P1 级别（高）**:
- 主实例不健康，已切换到备用
- 健康实例 < 2 个
- 熔断器打开

**P2 级别（中）**:
- 单个实例不健康
- 健康检查失败率 > 20%
- 网关响应时间 > 1 秒

**P3 级别（低）**:
- 配置同步失败
- 告警发送失败
- 非关键组件异常

### Prometheus 指标示例

```python
from prometheus_client import Gauge, Counter, Histogram

# Gauge 指标
instance_health_status = Gauge(
    'ha_instance_health_status',
    'Instance health status (1=healthy, 0=unhealthy)',
    ['instance_id', 'provider', 'model']
)

circuit_breaker_state = Gauge(
    'ha_circuit_breaker_state',
    'Circuit breaker state (0=closed, 1=open, 2=half_open)',
    ['instance_id']
)

# Counter 指标
failover_total = Counter(
    'ha_failover_total',
    'Total number of failovers',
    ['from_instance', 'to_instance']
)

fallback_triggered_total = Counter(
    'ha_fallback_triggered_total',
    'Total number of fallback triggers',
    ['chain_name', 'level']
)

# Histogram 指标
selection_latency_seconds = Histogram(
    'ha_selection_latency_seconds',
    'Instance selection latency',
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)

health_check_duration_seconds = Histogram(
    'ha_health_check_duration_seconds',
    'Health check duration',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```

### 日志记录

**结构化日志**:
```python
import structlog

logger = structlog.get_logger()

# 模型同步日志
logger.info(
    "model_synced_to_gateway",
    model_id=model.id,
    provider=model.provider.name,
    success=True,
    duration_ms=duration
)

# 故障切换日志
logger.warning(
    "failover_triggered",
    from_instance=old_instance.id,
    to_instance=new_instance.id,
    reason="health_check_failed",
    consecutive_failures=3
)

# 降级日志
logger.info(
    "fallback_triggered",
    chain_name="gpt-4-fallback",
    from_model="gpt-4",
    to_model="gpt-3.5-turbo",
    trigger_reason="consecutive_failures"
)

# 熔断日志
logger.warning(
    "circuit_breaker_opened",
    instance_id=instance.id,
    failure_rate=0.6,
    consecutive_failures=12
)
```

**日志级别**:
- DEBUG: 详细调试信息（实例选择过程）
- INFO: 正常操作流程（同步成功、切换成功）
- WARNING: 异常情况（健康检查失败、降级触发）
- ERROR: 错误和失败（调用失败、同步失败）
- CRITICAL: 严重错误（系统不可用）

## 安全考虑

### 认证与授权

**API Key 认证**:
- 网关层校验 API Key，支持按用户隔离资源
- API Key 加密存储（AES-256-GCM）
- 支持密钥轮换，周期建议 90 天
- Key 格式：`ak_xxxxxxxxxxxxxx`

**RBAC 权限模型**:
```python
class Role(Enum):
    ADMIN = "admin"          # 管理员：所有权限
    OPERATOR = "operator"    # 操作员：运维权限
    USER = "user"           # 普通用户：只读权限
    AUDITOR = "auditor"     # 审计员：审计日志权限

class Permission(Enum):
    HA_CONFIG_READ = "ha:config:read"
    HA_CONFIG_WRITE = "ha:config:write"
    HA_FAILOVER = "ha:failover"
    HA_MANUAL_CONTROL = "ha:manual_control"
    HA_ALERT_READ = "ha:alert:read"
```

**细粒度鉴权**:
- 不同用户可见不同的模型链
- 官方模型对所有用户可见
- 自定义模型仅创建者可见
- 手动故障转移仅限管理员

### 数据加密

**传输加密**:
- 强制 HTTPS/TLS 1.3
- 不支持 TLS 1.2 以下版本
- HSTS 头强制浏览器使用 HTTPS
- mTLS 双向认证（服务间通信）

**数据加密**:
- 敏感配置（API Key、密码）使用 AES-256-GCM 加密
- 密钥由 KMS（密钥管理服务）统一管理
- 支持密钥版本管理和历史追溯
- 加密字段：`provider.config.api_key`, `provider.config.base_url`

### 配额与限流

**配额管理**:
- 与计费模块联动，检查用户 Quota 余额
- Quota 不足时拒绝调用或降级到免费模型
- 实时扣减 Quota，防止超额使用

**API 限流**:
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/v1/select")
@limiter.limit("100/minute")  # 每分钟最多 100 次选择
async def select_instance(request: Request):
    ...
```

**防滥用策略**:
- 单用户 QPS 限制（默认 10 QPS）
- 单用户日调用次数限制
- 异常调用模式检测（高频调用、大额消耗）
- 自动触发风控告警

### 审计日志

**记录内容**:
- 所有配置变更操作（创建、更新、删除）
- 手动故障切换操作
- 权重调整操作
- 异常访问尝试

**保存期限**:
- 至少 180 天
- 支持按时间范围查询
- 支持导出审计报表

### 资源防滥用

**配置限制**:
- 降级链最大长度：5 个备用模型
- 健康检查间隔最小值：5 秒
- 并发探测数最大值：100
- 权重范围：0.1-1.0

**熔断保护**:
- 防止频繁熔断（冷却时间 5 分钟）
- 防止熔断抖动（连续成功 3 次才恢复）

**分布式锁保护**:
- 防止并发故障切换
- 锁超时自动释放
- 锁持有者标识追踪

## 与相关模块的集成

### 与 LLM 管理模块 (004) 集成

**模型配置同步**:
- LLM 管理模块创建/更新/删除模型时，发布领域事件
- 高可用模块监听事件，同步模型到网关
- 保持两个模块的模型配置一致

**联合查询**:
- 高可用模块提供实例健康状态
- LLM 管理模块查询时附加健康信息
- 前端展示模型列表时标记健康状态

**降级链配置**:
- LLM 管理模块提供降级链配置界面
- 高可用模块执行降级逻辑
- 配置存储于 LLM 模块，执行在高可用模块

### 与执行追踪模块 (016) 集成

**调用结果上报**:
- 每次 LLM 调用后，执行追踪模块记录详细信息
- 高可用模块订阅调用事件，更新实例健康评分
- 共享指标数据：响应时间、成功率、Token 使用量

**降级监控**:
- 执行追踪模块记录降级事件（isFallbackUsed, fallbackReason）
- 高可用模块提供降级链执行情况
- 联合分析降级原因和频率

**故障分析**:
- 执行追踪模块提供详细的执行链路
- 高可用模块提供实例健康状态变化历史
- 结合两者定位故障根因

### 与监控模块集成

**指标暴露**:
- 高可用模块提供 Prometheus 指标
- 监控模块统一采集和展示
- Grafana 仪表盘集成

**告警联动**:
- 高可用模块触发告警事件
- 监控模块统一发送告警通知
- 共享告警渠道（邮件、Slack 等）

### 与计费模块集成

**Quota 检查**:
- 高可用模块调用前检查用户 Quota 余额
- Quota 不足时降级到免费模型或拒绝调用
- 实时扣减 Quota，防止超额使用

**成本优化**:
- 基于计费数据，优先选择成本低的模型
- 权重配置考虑价格因素
- 提供成本分析报告

## 部署架构

### 独立服务部署

**Docker 容器化**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

**Kubernetes 部署**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ha-gateway
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ha-gateway
  template:
    metadata:
      labels:
        app: ha-gateway
    spec:
      containers:
      - name: ha-gateway
        image: agentx/ha-gateway:latest
        ports:
        - containerPort: 8080
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: ha-gateway-service
spec:
  selector:
    app: ha-gateway
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8080
  type: ClusterIP
```

### Nginx 配置

**Upstream 配置**:
```nginx
upstream ha_gateway {
    least_conn;
    server ha-gateway-1:8080 weight=1 max_fails=3 fail_timeout=30s;
    server ha-gateway-2:8080 weight=1 max_fails=3 fail_timeout=30s;
    server ha-gateway-3:8080 weight=1 max_fails=3 fail_timeout=30s;
    
    keepalive 100;
}

server {
    listen 443 ssl;
    server_name ha.internal;
    
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.3;
    
    location / {
        proxy_pass http://ha_gateway;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
}
```

### 高可用保障

**多副本部署**:
- 至少 3 个网关节点，防止单点故障
- Kubernetes 自动扩缩容（HPA）
- 节点故障自动迁移

**数据持久化**:
- Redis 集群模式，3 主 3 从
- PostgreSQL 主从复制，自动故障转移
- RabbitMQ 镜像队列

**灾备方案**:
- 跨区域部署（可选）
- 数据异地备份
- 灾难恢复预案（DRP）
