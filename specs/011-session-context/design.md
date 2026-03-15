# 会话上下文技术设计

## 概述

会话上下文模块使用会话管理器（ChatSessionManager）作为核心组件，结合 SSE 实现实时通信，提供会话生命周期管理、Token 计算和溢出处理等功能。

## 技术架构

### 整体架构

系统采用分层架构设计，遵循领域驱动设计（DDD）原则。接口层提供 RESTful API 和 SSE 流式接口；应用层协调领域服务，包含会话管理、消息处理和上下文管理等服务；领域层封装核心业务逻辑，管理会话、消息和上下文等实体模型；基础设施层提供数据持久化、缓存和外部服务集成。

### 核心组件

#### ChatSessionManager

会话管理器负责管理正在进行的聊天会话，支持会话注册与注销、会话中断控制、SSE 连接管理、超时处理和自动清理。使用 Python Dict + asyncio.Lock 实现线程安全，提供会话生命周期管理能力。支持分布式场景下通过 Redis pub/sub 同步会话状态。

#### SessionEntity

会话实体是会话管理的核心领域模型，包含会话 ID、用户 ID、Agent ID、会话状态、创建时间、更新时间和关联的 Agent 信息等字段。

#### MessageEntity

消息实体记录会话中的消息内容，包含消息 ID、会话 ID、角色（user/assistant/system）、消息内容、创建时间、Token 数量和元数据等字段。

#### ContextEntity

上下文实体管理对话的上下文信息，包含上下文 ID、会话 ID、历史消息 ID 列表、总 Token 数、最大容量、摘要和版本号等字段。

### 设计模式

#### 会话管理器模式

集中管理所有活跃会话，提供统一的会话操作接口。ChatSessionManager 作为单例管理器，使用 Python Dict + asyncio.Lock 保证并发安全，提供会话生命周期管理能力。分布式场景下，通过 Redis 实现跨节点会话共享。

#### 观察者模式

SSE 连接的生命周期事件通知处理。通过 SseEmitter 的回调（onCompletion、onTimeout、onError）自动清理会话资源，实现资源的自动管理。

#### 策略模式

Token 计算和溢出处理使用策略模式。定义 TokenCalculator 接口，根据不同模型选择不同的计算策略（GPT-4、GPT-3.5-turbo、Claude-3 等）。定义 TruncationStrategy 枚举，支持多种截断策略（FROM_START、FROM_END、IMPORTANT_FIRST）。

## 技术实现

### SSE 连接管理

#### 连接建立

客户端发起 SSE 连接请求，验证 JWT Token 或 API Key，验证通过后建立 StreamingResponse 连接，注册到 ChatSessionManager，返回会话 ID 和连接信息。连接建立后发送第一个心跳包。

#### 心跳机制

每 30 秒发送一次心跳事件 (event: heartbeat)，客户端收到后更新本地连接状态。服务端检测超过 90 秒无活动的连接，自动断开并清理资源。心跳事件包含时间戳和连接 ID。

#### 重连机制

客户端断线后，尝试自动重连 (最多 3 次)。第一次重连等待 1 秒，第二次等待 2 秒，第三次等待 4 秒 (指数退避)。重连时携带 last-event-id，服务端从中断点恢复消息推送。重连需重新验证身份。

#### 连接池管理

单节点限制最大连接数 (默认 50000)，防止资源耗尽。使用连接池监控当前连接数，超过阈值时拒绝新连接并返回 503 错误。定期扫描僵尸连接 (超过 2 分钟无心跳) 并清理。

### 会话生命周期

#### 创建会话

创建会话信息并存储到活跃会话中，设置 SSE 完成回调和超时回调，自动清理会话资源。返回会话 ID 和 SSE URL 给客户端。

#### 会话中断

标记会话为中断状态，发送中断事件给客户端，完成 SSE 连接。从活跃会话中移除，持久化会话信息（可选），清理资源。

#### 会话清理

定期清理超时会话，释放内存资源。检查会话的最后活动时间，超过阈值的会话执行清理操作。

### SSE 消息推送

查找会话信息，检查会话状态，发送 SSE 事件。如果会话已中断则停止推送，发送失败时自动清理会话。支持发送文本消息、错误消息和会话结束消息。

### Token 管理

#### Token 计算

根据模型选择不同的计算策略：
- GPT-4 和 GPT-3.5-turbo：使用 tiktoken 库精确计算 (编码：cl100k_base)
- Claude-3：使用 Anthropic SDK 提供的 Token 计算方法
- 其他模型：基于长度估算（降级方案，1 中文字符≈1.5 tokens）
- 缓存优化：使用 LRU Cache 缓存已计算文本的 Token 数，缓存大小可配置 (默认 10000 条)

#### Token 溢出处理

Token 数量超过限制时，根据配置的策略处理：
- **截断策略**:FROM_START(从开头截断)、FROM_END(从尾部截断)、IMPORTANT_FIRST(按重要性截断 - 系统消息>用户消息>助手消息)
- **摘要策略**:对早期消息进行摘要 (可配置摘要比例，默认 50%)，保留摘要和重要消息，支持多轮递归压缩
- **滑动窗口策略**:保留最近 N 轮对话 (可配置，默认 20 轮),自动丢弃最早的消息
- **混合策略**:组合多种策略 - 先滚动窗口，再摘要，最后截断，可配置策略优先级和参数

#### 可配置点

- token.default_limit: 默认 Token 限制 (默认 8000)
- token.overflow.strategy: 溢出处理策略 (默认 hybrid)
- token.calculator.method: Token 计算方法 (默认 auto)
- token.cache.enabled: 是否启用 Token 缓存 (默认 true)
- token.cache.size: LRU 缓存大小 (默认 10000)

## 数据模型

### 数据库表结构

#### sessions 表（会话表）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | VARCHAR(64) | 主键 | PK |
| session_id | VARCHAR(64) | 会话标识 | UNIQUE |
| user_id | VARCHAR(64) | 用户 ID | NOT NULL, INDEX |
| agent_id | VARCHAR(64) | Agent ID | NOT NULL, INDEX |
| status | VARCHAR(32) | 会话状态 | NOT NULL, INDEX |
| created_at | DATETIME | 创建时间 | NOT NULL |
| updated_at | DATETIME | 更新时间 | NOT NULL |

#### messages 表（消息表）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | VARCHAR(64) | 主键 | PK |
| message_id | VARCHAR(64) | 消息标识 | UNIQUE |
| session_id | VARCHAR(64) | 会话 ID | NOT NULL, INDEX |
| role | VARCHAR(32) | 角色 | NOT NULL |
| content | TEXT | 消息内容 | NOT NULL |
| token_count | INT | Token 数量 | DEFAULT 0 |
| created_at | DATETIME | 创建时间 | NOT NULL, INDEX |

#### contexts 表（上下文表）

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| id | VARCHAR(64) | 主键 | PK |
| context_id | VARCHAR(64) | 上下文标识 | UNIQUE |
| session_id | VARCHAR(64) | 会话 ID | UNIQUE, INDEX |
| context_data | JSON | 上下文数据 | NOT NULL |
| version | INT | 版本号 | DEFAULT 1 |
| created_at | DATETIME | 创建时间 | NOT NULL |

## 关键流程

### 会话建立流程

1. 客户端发起对话请求
2. 生成会话 ID
3. ChatSessionManager 注册会话
4. 返回会话 ID 和 SSE URL
5. 客户端建立 SSE 连接
6. 会话进入活跃状态

### 消息推送流程

1. AI 生成回复
2. ChatSessionManager 发送消息
3. 客户端接收消息
4. 客户端显示消息
5. 用户继续对话或结束会话

### 会话中断流程

1. 用户点击停止按钮
2. 调用 /conversation/interrupt
3. ChatSessionManager 中断会话
4. 清理会话
5. 返回中断成功

## 配置设计

### 会话配置

系统支持灵活的会话配置：
- **enabled**：是否启用会话管理
- **timeout**：空闲超时时间、最大会话时长
- **sse**：重连配置、心跳配置
- **storage**：存储类型、过期时间
- **token**：默认限制、溢出策略、计算方法

### SSE 配置

- **timeout**：SSE 超时时间（秒）
- **heartbeat.interval**：心跳间隔（毫秒）
- **reconnect.max_retries**：最大重连次数
- **reconnect.backoff**：重连退避时间（毫秒）

### Token 配置

- **default_limit**：默认 Token 限制
- **overflow.strategy**：溢出处理策略
- **calculator.method**：Token 计算方法
- **cache.enabled**：是否启用 Token 缓存
- **cache.size**：LRU 缓存大小

## 错误处理

### 异常类型

系统定义完善的异常处理机制：
- **会话不存在**：返回 404 错误
- **向已中断的会话发送消息**：记录日志
- **客户端断开连接**：自动清理会话
- **Token 计算接口异常**：降级到基于长度的估算

### 错误处理策略

捕获会话不存在异常并返回 404 错误响应，捕获 Token 超限异常并返回 400 错误响应和建议，捕获 SSE 相关异常并记录日志、清理会话资源。

## 性能优化

### 内存管理

使用 Python Dict + asyncio.Lock 保证线程安全，定期清理超时会话 (每 5 分钟),限制最大活跃会话数 (默认 10000)。SSE 事件批量发送 (每 100ms 合并一次),压缩大消息 (>1KB 使用 gzip)。使用连接池管理 SSE 连接，限制单节点最大连接数 (默认 50000)。

### 缓存优化

缓存文本的 Token 计算结果，避免重复计算，使用 LRU 淘汰策略 (默认 10000 条)。缓存最近消息列表 (每个会话最近 50 条),减少数据库查询次数。使用 Redis 缓存活跃会话信息，TTL 设置为 30 分钟。

### 异步处理

消息保存异步化 (使用 asyncio.create_task),不阻塞主流程。会话清理异步执行，避免影响活跃会话。Token 计算使用线程池 (concurrent.futures.ThreadPoolExecutor) 避免阻塞事件循环。

### 数据库优化

messages 表按 session_id 分区，提升查询性能。创建复合索引 (session_id, created_at DESC) 优化最新消息查询。批量插入消息 (每 10 条或每 5 秒批量写入)。使用连接池管理数据库连接。

## 监控指标

### 关键指标

- **活跃会话数**：当前活跃的会话数量
- **会话创建速率**：单位时间内创建的会话数
- **平均会话时长**：会话的平均持续时间
- **消息推送延迟**：从生成到推送的时间
- **Token 使用量**：Token 消耗统计
- **会话中断率**：中断会话占总会话的比例

### 告警规则

- 活跃会话数超过阈值
- 会话创建速率异常
- 消息推送延迟过高
- Token 使用超标

## 安全设计

### 认证机制

SSE 连接建立时需验证 JWT Token 或 API Key，防止未授权访问。Token 包含用户 ID、过期时间和权限范围。每次重连需重新验证身份，支持 IP 白名单绑定 (可选配置)。

### 防 CSRF 攻击

使用同源策略 + Token 验证双重机制。检查 Origin 和 Referer 头，确保请求来源合法。Token 中包含随机 nonce，防止重放攻击。

### 防会话劫持

session_id 使用加密安全的随机字符串 (至少 32 位),使用 secrets.token_hex() 生成。定期刷新 session_id(每次会话创建时)。限制 session_id 的访问权限，只能被创建者访问。

### 敏感信息保护

用户凭证、密钥等敏感数据不存储在会话中。日志记录时自动脱敏 (如隐藏 Token 中间部分)。上下文中的敏感词过滤 (可配置敏感词表)。

### 速率限制

单用户每秒最多创建 5 个会话，防止恶意刷接口。使用 Redis INCR + EXPIRE 实现滑动窗口限流。超过限制返回 429 Too Many Requests。

### 审计日志

记录会话创建、中断、异常等关键事件，包含时间戳、用户 ID、IP 地址等信息。日志保留 90 天，支持查询和分析。

## 扩展性设计

### 自定义 Token 计算器

可以实现 TokenCalculator 接口，提供自定义 Token 计算方法。继承 TokenCalculator 基类，实现 calculate(text: str) -> int 方法，使用 @register_calculator 装饰器注册模型前缀。

### 自定义溢出策略

可以实现 OverflowStrategy 接口，提供自定义 Token 溢出处理逻辑。继承 BaseOverflowStrategy 基类，实现 apply(messages, max_tokens) 方法。

### 分布式会话存储

支持将会话存储切换到 Redis、Memcached 等外部存储。实现 SessionStorage 接口，提供 get/set/delete 方法。通过配置切换存储后端。

## 技术栈

### 核心框架

- Python 3.10+
- FastAPI (Web 框架)
- Starlette (SSE 支持)
- SQLAlchemy (ORM 框架)
- Pydantic (数据验证)

### 数据存储

- MySQL 8.0+ (关系型数据库)
- Redis 7.0+ (缓存和分布式锁)

### 通信协议

- HTTP/REST (API 接口)
- SSE (流式响应，使用 Server-Sent Events)

### Token 计算

- tiktoken (GPT 系列模型 Token 计算)
- anthropic (Claude 系列模型 Token 计算)

### 工具库

- loguru (日志记录)
- redis-py (Redis 客户端)
- aioredis (异步 Redis 支持)
- APScheduler (定时任务)
- prometheus-client (监控指标)

## 与其他模块的集成

### 与 Agent 管理的集成

会话与 Agent 绑定，支持 Agent 维度的会话管理。统计每个 Agent 的会话数量和活跃度。会话创建时验证 Agent 是否存在和可用。

### 与模型管理的集成

记录模型调用的 Token 使用情况，支持模型维度的成本分析。追踪模型降级情况，记录降级原因和时间。根据模型窗口动态调整 Token 限制。

### 与计费模块的集成

Token 使用量用于计费，构建计费上下文，调用计费服务记录使用数据。实时计算会话成本，显示给用户。支持预付费和后付费模式。

### 与执行追踪 (016) 的集成

创建追踪上下文，记录会话 ID、Agent ID 和开始时间。记录模型调用和工具调用的详细信息，关联到会话。支持按会话维度查询执行轨迹。

### 与高可用 (015) 的集成

通过 Redis 哨兵模式实现故障自动转移。多节点部署时，使用 Redis pub/sub 同步会话状态。支持会话的跨节点迁移 (当节点故障时)。

## 未来优化方向

### 分布式会话管理

支持集群环境下的会话管理，实现会话的跨节点迁移和负载均衡。使用一致性哈希分配会话到节点，减少迁移开销。支持会话的粘性路由 (同一用户的会话尽量路由到同一节点)。

### 智能上下文压缩

使用 AI 模型自动摘要对话内容，提升上下文压缩的质量和效率。训练专用的摘要模型，平衡压缩率和信息保留。支持可配置的压缩策略 (激进/保守)。

### 实时流式追踪

引入消息队列 (如 Kafka) 实现真正的流式追踪，支持实时展示会话过程，提升用户体验。支持会话回放功能，用于问题排查和用户行为分析。

### 会话模板

支持会话模板功能，用户可以基于模板快速创建会话，支持模板的参数化配置。模板包含预设的系统提示、Token 限制、溢出策略等。

### 多模态会话

支持图片、音频、视频等多模态内容的会话。优化大文件的传输和存储，使用 CDN 加速。支持多模态内容的 Token 计算。
