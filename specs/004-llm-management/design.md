# LLM 管理能力模块 - 技术设计文档

## 技术架构

### 整体架构

LLM 管理模块采用分层架构设计，遵循 DDD（领域驱动设计）原则，分为 API 层、应用层、领域层和基础设施层。

- **API 层**：FastAPI 路由（`app/api/v1/llm/`, `app/api/v1/admin/llm/`）
- **应用层**：LLMAppService（用户侧）、AdminLLMAppService（管理侧）
- **领域层**：LLMDomainService、ProviderAggregate、ModelEntity、领域事件
- **基础设施层**：SQLAlchemy Repository、高可用网关、协议适配器、配置加密

### 分层职责

#### API 层
处理 HTTP 请求/响应、参数验证、权限校验、异常处理。

#### 领域层
封装核心领域逻辑，定义聚合根、领域实体、领域服务、领域事件、值对象。

#### 基础设施层
提供高可用网关、协议适配器统一接口、持久化、配置加密解密、事件发布。

### 技术栈

- **语言**：Python 3.9+
- **Web 框架**：FastAPI 0.104+
- **ORM**：SQLAlchemy 2.0+ (AsyncSession)
- **数据验证**：Pydantic 2.0+
- **异步支持**：AsyncIO
- **数据库**：PostgreSQL 14+
- **缓存**：Redis 7.0+
- **消息队列**：RabbitMQ 3.10+（可选，用于事件驱动）
- **加密**：cryptography (Fernet/AES-256-GCM)
- **监控**：Prometheus + prometheus_client
- **日志**：structlog（结构化日志）
- **协议适配**：llama-index 或自定义 httpx 客户端

## 关键设计

### 1. 聚合根模式

**设计目标**：确保服务商和模型之间的一致性，简化批量操作和状态管理。

**聚合根结构**：
```python
class ProviderAggregate:
    def __init__(self, provider: ProviderEntity, models: List[ModelEntity]):
        self.provider = provider
        self.models = models
    
    def get_decrypted_config(self) -> ProviderConfig:
        """解密后的配置访问"""
        return decrypt_provider_config(self.provider.config)
    
    def to_dto(self, mask_api_key: bool = True) -> ProviderDTO:
        """转换为 DTO，可选择掩码 API Key"""
        return ProviderAssembler.to_dto(self, mask_api_key=mask_api_key)
```

**优势**：一致性保证、批量加载、封装性（配置加密/解密透明）、业务逻辑封装。

### 2. 协议适配器

**设计目标**：统一不同 LLM 服务商的接口差异，支持灵活扩展新协议。

**协议类型**：OPENAI、MOONSHOT、AZURE_OPENAI、CUSTOM。

**适配器架构**：
```python
# 抽象基类
class ProtocolAdapter(ABC):
    @abstractmethod
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        pass
    
    @abstractmethod
    async def send_embedding_request(self, config: ProviderConfig, request: EmbeddingRequest) -> EmbeddingResponse:
        pass
    
    @abstractmethod
    def validate_config(self, config: ProviderConfig) -> bool:
        pass

# OpenAI 协议适配器实现
class OpenAIProtocolAdapter(ProtocolAdapter):
    async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
        # 使用 llama-index 或直接 httpx 实现
        pass
```

**适配器实现**：接口统一、配置转换、响应标准化、错误处理统一。

### 3. 高可用网关

**设计目标**：提供智能路由、负载均衡、故障转移能力，确保 LLM 服务的高可用性。

**核心组件**：
```python
class HighAvailabilityDomainService:
    async def sync_model_to_gateway(self, model: ModelEntity) -> None:
        """同步模型到网关"""
        pass
    
    async def select_best_provider(
        self,
        model_type: ModelType,
        session_id: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None
    ) -> HighAvailabilityResult:
        """选择最佳服务商和模型"""
        pass
    
    async def report_call_result(
        self,
        model_id: str,
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None
    ) -> None:
        """上报调用结果（异步非阻塞）"""
        pass
```

**HighAvailabilityResult**：包含选择的服务商、模型实例、实例 ID、是否发生模型切换。

**智能路由策略**：
1. **会话亲和性**：基于 session_id 缓存选择的模型实例，同一会话使用相同模型（Redis 缓存，TTL 30 分钟）
2. **负载均衡**：轮询、健康度加权、动态调整
3. **故障转移**：定期检测健康状态、自动切换备用实例（超时 < 1s）
4. **降级机制**：支持多级降级配置、连续失败 N 次触发、管理员手动控制

**性能监控**：调用成功率、平均延迟、错误率、P99 延迟、健康度评分（加权算法）。

**性能要求**：
- 模型选择延迟：< 50ms（P95）
- 故障转移时间：< 1s
- 缓存命中率：> 80%

### 4. 配置加密与安全

**设计目标**：保护敏感配置信息（如 API Key）的安全，防止泄露。

**加密流程**：明文 API Key → ProviderConfig 对象 → Fernet(AES-256-GCM) 加密 → 密文存储到数据库。

**解密流程**：数据库查询 → 密文数据 → Fernet 解密 → ProviderConfig 对象（明文）→ 聚合根返回。

**密钥管理**：
- **加密密钥**：使用环境变量 `ENCRYPTION_KEY` 存储
- **密钥轮换**：支持定期轮换（建议周期 90 天）
- **密钥存储**：生产环境使用专用密钥管理服务（如 AWS KMS、HashiCorp Vault）

**前端掩码显示**：返回 API Key 使用掩码替换（`******`），更新时如果传入掩码保留原密钥。

**防护措施**：
- 传输加密：强制 HTTPS/TLS 1.3
- 访问日志：记录所有 API Key 使用记录
- 配额限制：官方模型设置调用配额，防止滥用
- 异常检测：检测异常调用模式（如高频调用、大额消耗）

### 5. 领域事件驱动

**设计目标**：通过领域事件解耦各模块，实现松耦合的架构。

**事件类型**：
- ModelCreatedEvent：创建→同步到网关
- ModelUpdatedEvent：更新→更新网关配置
- ModelDeletedEvent：删除→从网关删除
- ModelStatusChangedEvent：状态变更→更新网关状态
- ModelsBatchDeletedEvent：批量删除→批量删除网关模型

**发布订阅机制**：
```python
from fastapi import BackgroundTasks

# 使用 FastAPI BackgroundTasks 异步处理事件
async def publish_event(event: BaseEvent, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_event, event)

# 或使用 Celery 进行分布式处理
@celery.task
def process_event_task(event_data: dict):
    # 处理事件
    pass
```

**重试机制**：失败事件进入重试队列，最多重试 3 次。
**死信队列**：超过重试次数的事件进入死信队列，人工介入处理。

### 6. 权限控制

**设计目标**：实现用户级别的资源隔离和操作权限控制。

**资源级别**：官方资源（isOfficial=true，对所有用户可见）、用户资源（isOfficial=false，仅创建者可见）。

**权限校验**：只能删除自己的服务商或官方资源（需管理员权限）、管理员可删除任何资源。

**数据隔离查询**：查询条件为（用户自己的 或 官方的）。

### 7. Repository 模式

**设计目标**：抽象数据访问层，隔离领域模型与持久化实现。

**ProviderRepository 接口**：
```python
class ProviderRepository(ABC):
    @abstractmethod
    async def create(self, provider: ProviderEntity) -> ProviderEntity:
        pass
    
    @abstractmethod
    async def update(self, provider: ProviderEntity) -> ProviderEntity:
        pass
    
    @abstractmethod
    async def delete(self, provider_id: str) -> None:
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> List[ProviderEntity]:
        pass
    
    @abstractmethod
    async def find_official_providers(self) -> List[ProviderEntity]:
        pass
```

**SQLAlchemy 实现**：基于 AsyncSession 实现异步 CRUD，使用自定义复杂查询方法，分页查询支持，条件构造器简化查询。

### 8. DTO 转换器

**设计目标**：隔离领域模型与外部数据传输对象，控制数据暴露范围。

**ProviderAssembler**：
```python
class ProviderAssembler:
    @staticmethod
    def to_dto(aggregate: ProviderAggregate, mask_api_key: bool = True) -> ProviderDTO:
        config = aggregate.get_decrypted_config()
        if mask_api_key:
            config.api_key = "******"
        
        return ProviderDTO(
            id=aggregate.provider.id,
            name=aggregate.provider.name,
            protocol=aggregate.provider.protocol,
            description=aggregate.provider.description,
            is_official=aggregate.provider.is_official,
            status=aggregate.provider.status,
            config=config,
            models=[ModelAssembler.to_dto(m) for m in aggregate.models]
        )
```

**掩码处理**：通过 mask_api_key 参数控制是否掩码 API Key。

### 9. 状态管理

**服务商状态**：启用=可用可调用、禁用=不可用，不参与路由。

**模型状态**：启用=可用可调用、禁用=不可用，不参与路由。

**状态级联**：
- 服务商禁用时，其下所有模型自动不可用
- 模型独立启用/禁用，但受服务商状态约束

**状态查询优化**：
- 使用 Redis 缓存激活模型列表
- 状态变更时主动失效缓存

## 核心流程

### 1. 创建服务商流程

用户输入 → API 层参数验证 → LLMAppService.create_provider()（异步） → ProviderAssembler.to_entity() → ProviderConfig 加密 → LLMDomainService.create_provider()（验证类型） → Repository.insert() → 返回 DTO（配置掩码）。

### 2. 创建模型流程

用户输入 → API 层参数验证 → LLMAppService.create_model()（异步） → 检查服务商存在 → ModelAssembler.to_entity() → LLMDomainService.create_model() → Repository.insert() → 发布 ModelCreatedEvent（BackgroundTasks 异步处理） → HighAvailabilityEventListener → 同步模型到网关 → 返回 DTO。

### 3. 高可用路由流程

对话请求 → ConversationService → HighAvailabilityDomainService.select_best_provider()（异步） → 检查 Redis 会话缓存 → 查询可用模型列表（带索引优化） → 过滤禁用和不健康模型 → 应用负载均衡策略 → 返回 Result（服务商、模型、实例 ID） → 调用模型服务 → report_call_result()（异步非阻塞上报成功/失败、延迟、更新健康度）。

**性能优化**：
- Redis 缓存命中：~5ms
- 数据库查询：< 20ms
- 路由计算：< 25ms
- **总计**：< 50ms（P95）

### 4. 模型降级流程

调用失败 → 检查是否启用降级链 → 获取降级链中的下一个模型 → select_best_provider with fallback_chain → 选择备用模型 → 重新调用 → 成功/失败 → 失败继续下一个 → 所有降级模型都失败返回错误。

**降级链配置示例**：
```json
{
  "primary_model": "gpt-4",
  "fallback_chain": ["gpt-3.5-turbo", "claude-3-sonnet", "moonshot-v1-8k"],
  "trigger_conditions": {
    "consecutive_failures": 3,
    "error_rate_threshold": 0.5
  }
}
```

## 数据模型

### ProviderEntity（服务商实体）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | str | 服务商 ID | 主键，UUID |
| user_id | str | 用户 ID | 非空，索引 |
| protocol | ProviderProtocol | 协议类型 | 非空，枚举 |
| name | str | 服务商名称 | 非空 |
| description | str | 描述 | 可空 |
| config | str | 配置（加密） | 非空，JSON 格式 |
| is_official | bool | 是否官方 | 非空，默认 false |
| status | bool | 状态 | 非空，默认 true |
| created_at | datetime | 创建时间 | 自动填充 |
| updated_at | datetime | 更新时间 | 自动填充 |
| deleted_at | datetime | 删除时间 | 逻辑删除 |

### ModelEntity（模型实体）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | str | 模型 ID | 主键，UUID |
| user_id | str | 用户 ID | 非空 |
| provider_id | str | 服务商 ID | 非空，外键，索引 |
| model_id | str | 模型标识 | 非空 |
| name | str | 模型名称 | 非空 |
| description | str | 描述 | 可空 |
| model_endpoint | str | 模型部署名称 | 可空 |
| type | ModelType | 模型类型 | 非空，CHAT/EMBEDDING |
| is_official | bool | 是否官方 | 非空，默认 false |
| status | bool | 状态 | 非空，默认 true |
| created_at | datetime | 创建时间 | 自动填充 |
| updated_at | datetime | 更新时间 | 自动填充 |
| deleted_at | datetime | 删除时间 | 逻辑删除 |

### ProviderConfig（服务商配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| api_key | str | API 密钥（Fernet 加密存储） |
| base_url | str | 自定义 Endpoint URL |

## 接口定义

### 应用层接口

#### LLMAppService
```python
class LLMAppService:
    # 服务商管理
    async def create_provider(self, dto: ProviderCreateDTO, user_id: str) -> ProviderDTO:
        pass
    
    async def update_provider(self, provider_id: str, dto: ProviderUpdateDTO, user_id: str) -> ProviderDTO:
        pass
    
    async def delete_provider(self, provider_id: str, user_id: str) -> None:
        pass
    
    async def get_all_providers(self, user_id: str, provider_type: ProviderType) -> List[ProviderDTO]:
        pass
    
    async def update_provider_status(self, provider_id: str, status: bool, user_id: str) -> None:
        pass
    
    # 模型管理
    async def create_model(self, dto: ModelCreateDTO, user_id: str) -> ModelDTO:
        pass
    
    async def update_model(self, model_id: str, dto: ModelUpdateDTO, user_id: str) -> ModelDTO:
        pass
    
    async def delete_model(self, model_id: str, user_id: str) -> None:
        pass
    
    async def update_model_status(self, model_id: str, status: bool, user_id: str) -> None:
        pass
    
    async def get_active_models_by_type(self, provider_type: ProviderType, model_type: ModelType) -> List[ModelDTO]:
        pass
```

#### AdminLLMAppService
```python
class AdminLLMAppService:
    # 官方服务商管理
    async def create_provider(self, dto: ProviderCreateDTO) -> ProviderDTO:
        pass
    
    async def update_provider(self, provider_id: str, dto: ProviderUpdateDTO) -> ProviderDTO:
        pass
    
    async def delete_provider(self, provider_id: str) -> None:
        pass
    
    # 官方模型管理
    async def create_model(self, dto: ModelCreateDTO) -> ModelDTO:
        pass
    
    async def update_model(self, model_id: str, dto: ModelUpdateDTO) -> ModelDTO:
        pass
    
    async def delete_model(self, model_id: str) -> None:
        pass
```

### 领域层接口

#### LLMDomainService
```python
class LLMDomainService:
    # 服务商管理
    async def create_provider(self, entity: ProviderEntity) -> ProviderEntity:
        pass
    
    async def update_provider(self, entity: ProviderEntity) -> ProviderEntity:
        pass
    
    async def delete_provider(self, provider_id: str) -> None:
        pass
    
    async def get_provider(self, provider_id: str) -> ProviderAggregate:
        pass
    
    async def get_all_providers(self, user_id: str, provider_type: ProviderType) -> List[ProviderAggregate]:
        pass
    
    async def update_provider_status(self, provider_id: str, status: bool) -> None:
        pass
    
    # 模型管理
    async def create_model(self, entity: ModelEntity) -> ModelEntity:
        pass
    
    async def update_model(self, entity: ModelEntity) -> ModelEntity:
        pass
    
    async def delete_model(self, model_id: str) -> None:
        pass
    
    async def update_model_status(self, model_id: str, status: bool) -> None:
        pass
    
    async def get_active_model_list(self, provider_type: ProviderType, model_type: ModelType) -> List[ModelEntity]:
        pass
    
    # 工具方法
    async def check_provider_exists(self, provider_id: str) -> bool:
        pass
    
    async def get_provider_aggregate(self, provider_id: str) -> ProviderAggregate:
        pass
    
    def get_provider_protocols(self) -> List[ProviderProtocol]:
        pass
```

#### HighAvailabilityDomainService
```python
class HighAvailabilityDomainService:
    # 模型同步
    async def sync_model_to_gateway(self, model: ModelEntity) -> None:
        pass
    
    async def remove_model_from_gateway(self, model_id: str) -> None:
        pass
    
    async def update_model_in_gateway(self, model: ModelEntity) -> None:
        pass
    
    async def batch_remove_models_from_gateway(self, model_ids: List[str]) -> None:
        pass
    
    async def sync_all_models_to_gateway(self) -> None:
        pass
    
    async def initialize_project(self) -> None:
        pass
    
    # 智能路由
    async def select_best_provider(
        self,
        model_type: ModelType,
        session_id: Optional[str] = None,
        fallback_chain: Optional[List[str]] = None
    ) -> HighAvailabilityResult:
        pass
    
    # 结果上报
    async def report_call_result(
        self,
        model_id: str,
        success: bool,
        latency_ms: float,
        error_message: Optional[str] = None
    ) -> None:
        pass
```

## 扩展性设计

### 1. 新增协议支持

**步骤**：
1. 在 `app/domain/llm/enums.py` 的 ProviderProtocol 枚举中添加新协议类型
2. 实现对应的协议适配器（继承 ProtocolAdapter 抽象基类）
   ```python
   class NewProtocolAdapter(ProtocolAdapter):
       async def send_chat_request(self, config: ProviderConfig, request: ChatRequest) -> ChatResponse:
           # 实现新协议的聊天请求
           pass
   ```
3. 在配置转换器中添加新协议的配置映射
4. 注册适配器到适配器工厂

**示例**：
```python
# 适配器工厂注册
class ProtocolAdapterFactory:
    _adapters = {
        ProviderProtocol.OPENAI: OpenAIProtocolAdapter(),
        ProviderProtocol.MOONSHOT: MoonshotProtocolAdapter(),
        # 新增协议
        ProviderProtocol.NEW_PROTOCOL: NewProtocolAdapter(),
    }
```

### 2. 新增高可用策略

**步骤**：
1. 实现新的路由策略类
   ```python
   class CustomRoutingStrategy(RoutingStrategy):
       async def select(self, models: List[ModelEntity]) -> ModelEntity:
           # 自定义路由逻辑
           pass
   ```
2. 在 HighAvailabilityDomainService 中集成新策略
3. 提供策略配置选项（通过配置文件或环境变量）

### 3. 新增模型类型

**步骤**：
1. 在 `app/domain/llm/enums.py` 的 ModelType 枚举中添加新类型
   ```python
   class ModelType(str, Enum):
       CHAT = "CHAT"
       EMBEDDING = "EMBEDDING"
       IMAGE_GENERATION = "IMAGE_GENERATION"  # 新增
   ```
2. 更新模型验证逻辑
3. 在高可用网关中添加对新类型的支持

## 性能优化

### 查询优化
- **批量加载**：使用聚合根模式一次性加载服务商和模型（减少 N+1 查询）
- **索引优化**：对 user_id、provider_id、status 等常用查询字段建立索引
- **缓存机制**：对热点数据（如官方模型列表）使用 Redis 缓存
  - 官方模型列表：TTL 5 分钟
  - 激活模型列表：TTL 2 分钟
  - 会话选择的模型实例：TTL 30 分钟

### 并发控制
- **乐观锁**：更新操作使用时间戳版本控制
- **事务隔离**：使用 READ COMMITTED 隔离级别
- **异步处理**：高可用同步、事件发布等操作使用 BackgroundTasks 异步执行
- **连接池**：SQLAlchemy AsyncSession 连接池配置（pool_size=20, max_overflow=40）

### 性能基准
- **模型选择延迟**：< 50ms（P95）
- **API 响应时间**：< 200ms（P95，不含 LLM 调用时间）
- **故障转移时间**：< 1s
- **缓存命中率**：> 80%
- **并发连接数**：支持 1000+ 并发连接
- **QPS**：单实例支持 500+ QPS

## 安全考虑

### 配置安全
- **加密存储**：Fernet(AES-256-GCM) 加密
- **传输加密**：强制 HTTPS/TLS 1.3
- **密钥轮换**：支持定期轮换（建议周期 90 天）
- **密钥管理**：生产环境使用专用密钥管理服务（如 AWS KMS、HashiCorp Vault）

### 访问控制
- **用户隔离**：严格权限校验，防止越权访问
- **操作审计**：记录关键操作日志（创建、更新、删除）
- **权限分级**：用户级（仅操作自己的资源）、管理员级（操作所有资源）

### 防护措施
- **限流控制**：API 调用限流（如 100 次/分钟/IP）
- **输入验证**：严格验证所有输入参数（Pydantic 验证）
- **异常处理**：统一异常处理，不暴露敏感信息
- **配额限制**：官方模型设置调用配额，防止滥用
- **异常检测**：检测异常调用模式（如高频调用、大额消耗）
- **告警机制**：异常情况实时告警（对接钉钉、企业微信等）

### MCP 集成安全
- **MCP Server 认证**：只有认证的 LLM 服务商才能注册为 MCP Server
- **Tool Call 鉴权**：所有 MCP Tool Call 需要验证调用权限
- **配额管理**：MCP 调用计入总配额，防止绕过限制

## 监控与运维

### 监控指标
- **业务指标**：
  - `llm_request_total`：LLM 请求总数
  - `llm_request_duration`：LLM 请求延迟（P50, P95, P99）
  - `llm_request_errors`：LLM 请求错误数
  - `llm_fallback_total`：降级次数
  - `llm_cache_hit_rate`：缓存命中率

- **系统指标**：
  - API 响应时间
  - 数据库连接池使用率
  - Redis 缓存使用情况
  - CPU/内存使用率

### 日志记录
- **结构化日志**：使用 structlog，JSON 格式输出
- **日志级别**：DEBUG, INFO, WARNING, ERROR, CRITICAL
- **审计日志**：记录所有敏感操作
- **链路追踪**：集成 OpenTelemetry，支持分布式追踪

### 告警规则
- **错误率告警**：错误率 > 5% 触发告警
- **延迟告警**：P95 延迟 > 500ms 触发告警
- **可用性告警**：服务不可用立即触发告警
- **配额告警**：官方模型配额使用 > 80% 触发告警

### 运维手册
- **部署流程**：Docker 容器化部署
- **扩容流程**：水平扩容增加实例
- **备份恢复**：数据库定时备份，支持快速恢复
- **故障排查**：常见问题排查手册
