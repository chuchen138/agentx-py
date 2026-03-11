# 会话上下文技术设计

## 概述

会话上下文模块使用会话管理器（ChatSessionManager）作为核心组件，结合 SSE 实现实时通信，提供会话生命周期管理、Token 计算和溢出处理等功能。

## 技术架构

### 整体架构

系统采用分层架构设计，遵循领域驱动设计（DDD）原则。接口层提供 RESTful API 和 SSE 流式接口；应用层协调领域服务，包含会话管理、消息处理和上下文管理等服务；领域层封装核心业务逻辑，管理会话、消息和上下文等实体模型；基础设施层提供数据持久化、缓存和外部服务集成。

### 核心组件

#### ChatSessionManager

会话管理器负责管理正在进行的聊天会话，支持会话注册与注销、会话中断控制、SSE 连接管理、超时处理和自动清理。使用 ConcurrentHashMap 存储会话实现线程安全，提供会话生命周期管理能力。

#### SessionEntity

会话实体是会话管理的核心领域模型，包含会话 ID、用户 ID、Agent ID、会话状态、创建时间、更新时间和关联的 Agent 信息等字段。

#### MessageEntity

消息实体记录会话中的消息内容，包含消息 ID、会话 ID、角色（user/assistant/system）、消息内容、创建时间、Token 数量和元数据等字段。

#### ContextEntity

上下文实体管理对话的上下文信息，包含上下文 ID、会话 ID、历史消息 ID 列表、总 Token 数、最大容量、摘要和版本号等字段。

### 设计模式

#### 会话管理器模式

集中管理所有活跃会话，提供统一的会话操作接口。ChatSessionManager 作为单例管理器，使用 ConcurrentHashMap 存储会话实现线程安全，提供会话生命周期管理能力。

#### 观察者模式

SSE 连接的生命周期事件通知处理。通过 SseEmitter 的回调（onCompletion、onTimeout、onError）自动清理会话资源，实现资源的自动管理。

#### 策略模式

Token 计算和溢出处理使用策略模式。定义 TokenCalculator 接口，根据不同模型选择不同的计算策略（GPT-4、GPT-3.5-turbo、Claude-3 等）。定义 TruncationStrategy 枚举，支持多种截断策略（FROM_START、FROM_END、IMPORTANT_FIRST）。

## 技术实现

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
- GPT-4 和 GPT-3.5-turbo：使用 tiktoken 库精确计算
- Claude-3：使用特定计算方法
- 其他模型：基于长度估算（降级方案）

#### Token 溢出处理

Token 数量超过限制时，根据配置的策略处理：
- **截断策略**：FROM_START（从开头截断）、FROM_END（从尾部截断）、IMPORTANT_FIRST（按重要性截断）
- **摘要策略**：对更早的消息进行摘要，保留摘要和重要消息

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

使用 ConcurrentHashMap 保证线程安全，定期清理超时会话，限制最大活跃会话数。SSE 事件批量发送，压缩大消息，使用连接池管理 SSE 连接。

### 缓存优化

缓存文本的 Token 计算结果，避免重复计算，使用 LRU 淘汰策略。缓存最近消息列表，减少数据库查询次数。

### 异步处理

消息保存异步化，不阻塞主流程。会话清理异步执行，避免影响活跃会话。

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

## 安全考虑

### 数据隔离

基于 user_id 的用户数据隔离，基于 session_id 的会话隔离。权限控制确保只能访问自己的会话和消息。

### 敏感信息保护

系统提示中的敏感信息过滤，用户上传文件的路径保护，Token 计算结果脱敏显示。

## 扩展性设计

### 自定义处理器

可以继承 AbstractMessageHandler 实现自定义处理逻辑，使用 @Component 注解标记为 Spring Bean。

### 自定义消息类型

可以扩展 MessageType 枚举，添加自定义消息类型。

### 自定义 Token 计算器

可以实现 TokenCalculator 接口，提供自定义 Token 计算方法，使用 @Component 注解标记为 Spring Bean。

## 技术栈

### 核心框架

Spring Boot 3.x、Spring Web MVC、MyBatis-Plus、LangChain4j（LLM 集成）

### 数据存储

MySQL 8.0（关系型数据库）、Redis（缓存，可选）

### 通信协议

HTTP/REST（API 接口）、SSE（流式响应）

### 工具库

Hutool（Java 工具库）、Lombok（注解简化代码）、Jackson（JSON 处理）、tiktoken（Token 计算）

## 与其他模块的集成

### 与 Agent 管理的集成

会话与 Agent 绑定，支持 Agent 维度的会话管理。统计每个 Agent 的会话数量和活跃度。

### 与模型管理的集成

记录模型调用的 Token 使用情况，支持模型维度的成本分析。追踪模型降级情况。

### 与计费的集成

Token 使用量用于计费，构建计费上下文，调用计费服务记录使用数据。

### 与执行追踪的集成

创建追踪上下文，记录会话 ID、Agent ID 和开始时间，记录模型调用和工具调用的详细信息。

## 未来优化方向

### 实时流式追踪

引入消息队列实现真正的流式追踪，支持实时展示会话过程，提升用户体验。

### 分布式会话管理

支持集群环境下的会话管理，实现会话的跨节点迁移和负载均衡。

### 智能上下文压缩

使用 AI 模型自动摘要对话内容，提升上下文压缩的质量和效率。

### 会话模板

支持会话模板功能，用户可以基于模板快速创建会话，支持模板的参数化配置。
