# LLM 管理能力模块 - 技术设计文档

## 技术架构

### 整体架构

LLM 管理模块采用分层架构设计，遵循 DDD（领域驱动设计）原则，分为 API 层、应用层、领域层和基础设施层。

- **应用层**：LLMAppService（用户侧）、AdminLLMAppService（管理侧）
- **领域层**：LLMDomainService、ProviderAggregate、ModelEntity、领域事件
- **基础设施层**：MyBatis Repository、高可用网关、协议适配器、配置加密

### 分层职责

#### 应用层
协调领域服务，处理业务用例，提供 API 响应。服务商和模型的 CRUD 操作、状态切换、查询过滤。

#### 领域层
封装核心领域逻辑，定义聚合根、领域实体、领域服务、领域事件、值对象。

#### 基础设施层
提供高可用网关、协议适配器统一接口、持久化、配置加密解密、事件发布。

### 技术栈

- 语言：Java 17+
- 框架：Spring Boot
- ORM：MyBatis Plus
- 数据库：PostgreSQL
- 事件驱动：Spring Events
- 加密：AES-256
- 网关：自定义网关

## 关键设计

### 1. 聚合根模式

**设计目标**：确保服务商和模型之间的一致性，简化批量操作和状态管理。

**聚合根结构**：包含 ProviderEntity（服务商实体）和 List<ModelEntity>（模型列表）。

**优势**：一致性保证、批量加载、封装性（配置加密/解密透明）、业务逻辑封装。

### 2. 协议适配器

**设计目标**：统一不同 LLM 服务商的接口差异，支持灵活扩展新协议。

**协议类型**：OPENAI、MOONSHOT、AZURE_OPENAI、CUSTOM。

**适配器架构**：LLM Domain Service → Protocol Interface → 各协议适配器（统一的 sendChatRequest、sendEmbeddingRequest、validateConfig 接口）。

**适配器实现**：接口统一、配置转换、响应标准化、错误处理统一。

### 3. 高可用网关

**设计目标**：提供智能路由、负载均衡、故障转移能力，确保 LLM 服务的高可用性。

**核心组件**：
- HighAvailabilityDomainService：同步模型到网关、选择最佳服务商和模型、支持降级链、上报调用结果
- HighAvailabilityResult：包含选择的服务商、模型实例、实例ID、是否发生模型切换

**智能路由策略**：
1. **会话亲和性**：基于 sessionId 缓存选择的模型实例，同一会话使用相同模型
2. **负载均衡**：轮询、健康度加权、动态调整
3. **故障转移**：定期检测健康状态、自动切换备用实例
4. **降级机制**：支持多级降级配置、连续失败 N 次触发、管理员手动控制

**性能监控**：调用成功率、平均延迟、错误率、P99 延迟、健康度评分（加权算法）。

### 4. 配置加密与安全

**设计目标**：保护敏感配置信息（如 API Key）的安全，防止泄露。

**加密流程**：明文 API Key → ProviderConfig 对象 → AES-256 加密 → 密文存储到数据库。

**解密流程**：数据库查询 → 密文数据 → AES-256 解密 → ProviderConfig 对象（明文）→ 聚合根返回。

**前端掩码显示**：返回 API Key 使用掩码替换（`******`），更新时如果传入掩码保留原密钥。

### 5. 领域事件驱动

**设计目标**：通过领域事件解耦各模块，实现松耦合的架构。

**事件类型**：
- ModelCreatedEvent：创建→同步到网关
- ModelUpdatedEvent：更新→更新网关配置
- ModelDeletedEvent：删除→从网关删除
- ModelStatusChangedEvent：状态变更→更新网关状态
- ModelsBatchDeletedEvent：批量删除→批量删除网关模型

**发布订阅机制**：异步处理、重试机制、死信队列。

### 6. 权限控制

**设计目标**：实现用户级别的资源隔离和操作权限控制。

**资源级别**：官方资源（isOfficial=true，对所有用户可见）、用户资源（isOfficial=false，仅创建者可见）。

**权限校验**：只能删除自己的服务商或官方资源（需管理员权限）、管理员可删除任何资源。

**数据隔离查询**：查询条件为（用户自己的 或 官方的）。

### 7. Repository 模式

**设计目标**：抽象数据访问层，隔离领域模型与持久化实现。

提供基础 CRUD 接口、基于 MyBatis Plus 实现、自定义复杂查询方法、分页查询支持、条件构造器简化查询。

### 8. DTO 转换器

**设计目标**：隔离领域模型与外部数据传输对象，控制数据暴露范围。

**ProviderAssembler**：将聚合根转换为 DTO（包含名称、协议、描述、是否官方、状态、配置掩码）。

### 9. 状态管理

**服务商状态**：启用=可用可调用、禁用=不可用，不参与路由。

**模型状态**：启用=可用可调用、禁用=不可用，不参与路由。

**状态级联**：服务商禁用时，其下所有模型自动不可用；模型独立启用/禁用。

## 核心流程

### 1. 创建服务商流程

用户输入 → LLMAppService.createProvider() → ProviderAssembler.toEntity() → ProviderConfig 加密 → LLMDomainService.createProvider()（验证类型）→ Repository.insert() → 返回 DTO（配置掩码）。

### 2. 创建模型流程

用户输入 → LLMAppService.createModel() → 检查服务商存在 → ModelAssembler.toEntity() → LLMDomainService.createModel() → Repository.insert() → 发布 ModelCreatedEvent → HighAvailabilityEventListener → 同步模型到网关 → 返回 DTO。

### 3. 高可用路由流程

对话请求 → ConversationService → HighAvailabilityDomainService.selectBestProvider() → 检查会话缓存 → 查询可用模型列表 → 过滤禁用和不健康模型 → 应用负载均衡策略 → 返回 Result（服务商、模型、实例 ID）→ 调用模型服务 → reportCallResult()（上报成功/失败、延迟、更新健康度）。

### 4. 模型降级流程

调用失败 → 检查是否启用降级链 → 获取降级链中的下一个模型 → selectBestProvider with fallbackChain → 选择备用模型 → 重新调用 → 成功/失败 → 失败继续下一个 → 所有降级模型都失败返回错误。

## 数据模型

### ProviderEntity（服务商实体）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | String | 服务商 ID | 主键，UUID |
| userId | String | 用户 ID | 非空 |
| protocol | ProviderProtocol | 协议类型 | 非空 |
| name | String | 服务商名称 | 非空 |
| description | String | 描述 | 可空 |
| config | ProviderConfig | 配置（加密） | 非空，JSON |
| isOfficial | Boolean | 是否官方 | 非空，默认 false |
| status | Boolean | 状态 | 非空，默认 true |
| createdAt | LocalDateTime | 创建时间 | 自动填充 |
| updatedAt | LocalDateTime | 更新时间 | 自动填充 |
| deletedAt | LocalDateTime | 删除时间 | 逻辑删除 |

### ModelEntity（模型实体）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | String | 模型 ID | 主键，UUID |
| userId | String | 用户 ID | 非空 |
| providerId | String | 服务商 ID | 非空，外键 |
| modelId | String | 模型标识 | 非空 |
| name | String | 模型名称 | 非空 |
| description | String | 描述 | 可空 |
| modelEndpoint | String | 模型部署名称 | 可空 |
| type | ModelType | 模型类型 | 非空，CHAT/EMBEDDING |
| isOfficial | Boolean | 是否官方 | 非空，默认 false |
| status | Boolean | 状态 | 非空，默认 true |
| createdAt | LocalDateTime | 创建时间 | 自动填充 |
| updatedAt | LocalDateTime | 更新时间 | 自动填充 |
| deletedAt | LocalDateTime | 删除时间 | 逻辑删除 |

### ProviderConfig（服务商配置）

| 字段 | 类型 | 说明 |
|------|------|------|
| apiKey | String | API 密钥（加密存储）|
| baseUrl | String | 自定义 Endpoint URL |

## 接口定义

### 应用层接口

#### LLMAppService
- 服务商管理：createProvider、updateProvider、deleteProvider、getAllProviders、updateProviderStatus
- 模型管理：createModel、updateModel、deleteModel、updateModelStatus、getActiveModelsByType

#### AdminLLMAppService
- 官方服务商管理：createProvider、updateProvider、deleteProvider
- 官方模型管理：createModel、updateModel、deleteModel

### 领域层接口

#### LLMDomainService
- 服务商管理：createProvider、updateProvider、deleteProvider、getProvider、getAllProviders、updateProviderStatus
- 模型管理：createModel、updateModel、deleteModel、updateModelStatus、getActiveModelList
- 工具方法：checkProviderExists、getProviderAggregate、getProviderProtocols

#### HighAvailabilityDomainService
- 模型同步：syncModelToGateway、removeModelFromGateway、updateModelInGateway、batchRemoveModelsFromGateway、syncAllModelsToGateway、initializeProject
- 智能路由：selectBestProvider（单选/带会话/带降级链）
- 结果上报：reportCallResult

## 扩展性设计

### 1. 新增协议支持

1. 在 ProviderProtocol 枚举中添加新协议类型
2. 实现对应的协议适配器（统一接口）
3. 在配置转换器中添加新协议的配置映射

### 2. 新增高可用策略

1. 实现新的路由策略类
2. 在 HighAvailabilityDomainService 中集成新策略
3. 提供策略配置选项

### 3. 新增模型类型

1. 在 ModelType 枚举中添加新类型
2. 更新模型验证逻辑
3. 在高可用网关中添加对新类型的支持

## 性能优化

### 查询优化
- 批量加载：使用聚合根模式一次性加载服务商和模型
- 索引优化：对 userId、providerId、status 等常用查询字段建立索引
- 缓存机制：对热点数据（如官方模型列表）使用缓存

### 并发控制
- 乐观锁：更新操作使用版本号或时间戳
- 事务隔离：合理配置事务隔离级别
- 异步处理：高可用同步、事件发布等操作异步执行

## 安全考虑

### 配置安全
- 加密存储：AES-256
- 传输加密：HTTPS
- 密钥轮换：支持定期更换

### 访问控制
- 用户隔离：严格权限校验
- 操作审计：记录关键操作日志

### 防护措施
- 限流控制：API 调用限流
- 输入验证：严格验证所有输入
- 异常处理：统一异常处理，不暴露敏感信息
