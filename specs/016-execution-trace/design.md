# 执行链路追踪技术设计

## 概述

执行链路追踪模块采用分层架构设计，遵循领域驱动设计原则，记录和分析 Agent 执行过程中的模型调用、工具调用等关键信息，支持执行历史查询、统计分析、失败排查和成本分析。

**核心设计原则**：
- **非侵入式**：追踪不应影响主流程性能
- **异步处理**：使用事件驱动和异步队列解耦
- **可扩展性**：支持 OpenTelemetry 标准集成
- **安全优先**：内置脱敏、权限控制和审计

## 技术架构

### 分层架构

系统采用四层架构：

**接口层（API Layer）**：
- FastAPI 路由控制器
- DTO 对象定义和参数校验
- 用户认证和权限过滤

**应用层（Application Layer）**：
- AgentExecutionTraceAppService：负责业务流程编排
- TraceEventListener：事件监听和数据处理
- 发布领域事件收集追踪数据

**领域层（Domain Layer）**：
- TraceCollector：追踪数据收集器（AOP 装饰器）
- AgentExecutionSummary/Detail 实体模型
- TraceContext 上下文管理
- 领域服务封装核心业务逻辑

**基础设施层（Infrastructure Layer）**：
- SQLAlchemy Repository：数据持久化
- PostgreSQL：主存储数据库
- Redis：热点数据缓存
- asyncio.Queue：异步事件队列
- gzip：数据压缩

### 核心组件

**AgentExecutionTraceAppService**：
- 负责执行追踪相关的业务流程编排
- 提供获取完整的执行链路信息
- 分页查询用户的执行历史
- 查询会话的执行历史
- 查询用户的失败执行记录
- 获取执行统计信息

**TraceCollector（AOP 装饰器）**：
- **埋点方式**：使用 Python 装饰器实现 AOP
- **LLM 调用埋点**：装饰 `model_chat()` 方法，记录输入输出、Token、耗时
- **工具调用埋点**：装饰 `tool_executor.execute()` 方法，记录参数、响应、耗时
- **Agent 执行埋点**：在 conversation_manager 中植入开始/结束埋点
- **功能**：
  - 获取或开始会话级别的执行追踪
  - 记录模型调用详情
  - 记录工具调用详情
  - 完成执行追踪
- **采样逻辑**：根据 Trace ID 哈希计算是否采集

**TraceEventListener（异步事件监听器）**：
- **监听机制**：asyncio.Queue 消费者
- **处理方式**：异步批量处理（每 100 条或 5 秒）
- **事件类型**：
  - ExecutionStartEvent：执行开始
  - ExecutionEndEvent：执行完成
  - ModelCallEvent：模型调用
  - ToolCallEvent：工具调用
- **数据脱敏**：在持久化前自动脱敏敏感字段

**EventPublisher（事件发布器）**：
- 基于 asyncio.Queue 实现
- 容量：10000 条消息
- 支持背压控制（队列满时降级）

## 追踪上下文管理

### TraceContext

在一次执行过程中保持追踪状态，包含追踪 ID、用户 ID、会话 ID、Agent ID、是否启用追踪、当前用户消息 ID、用户消息内容、用户消息类型等核心字段。支持禁用状态，当追踪系统异常时返回禁用上下文，不影响主流程。

### 追踪启动流程

用户发起 Agent 对话请求，TraceCollector 获取或创建 TraceContext，如果是首次追踪则创建 AgentExecutionSummaryEntity，记录用户消息到 AgentExecutionDetailEntity，将消息 ID 保存到 TraceContext。

## 事件驱动架构

### 事件机制

采用事件驱动机制实现追踪数据的异步收集和持久化，确保追踪过程不影响主流程。使用 Spring 的 ApplicationEventPublisher 发布事件，使用 @EventListener 和 @Async 异步处理事件，事件处理失败不影响主流程。

### 事件类型

执行开始事件在 Agent 执行开始时触发，携带 TraceContext 和用户消息，处理逻辑为创建执行汇总记录。执行完成事件在 Agent 执行完成时触发，携带 TraceContext 和执行结果，处理逻辑为更新执行汇总记录。模型调用事件在每次模型调用时触发，携带 TraceContext、AI 响应和 ModelCallInfo，处理逻辑为记录模型调用详情。工具执行事件在每次工具调用时触发，携带 TraceContext 和 ToolCallInfo，处理逻辑为记录工具调用详情。

## 数据收集机制

### 模型调用数据收集

在模型调用完成后收集模型部署名称、提供商名称、输入 Token 数、输出 Token 数、总 Token 数、模型调用耗时和 AI 响应内容等数据。

### 工具调用数据收集

在工具调用完成后收集工具名称、工具调用入参、工具调用出参、工具执行耗时、工具执行是否成功、是否触发了降级、降级原因、降级前的模型和降级后的模型等数据。

## 数据存储设计

### 存储方案选型

**短期方案（PostgreSQL + Redis）**：
- **PostgreSQL**：主存储数据库
  - agent_execution_summary：执行汇总表（宽表设计）
  - agent_execution_details：执行详细表（JSONB 支持灵活查询）
  - 使用 GIN 索引优化 JSONB 字段查询
- **Redis**：热点数据缓存
  - 缓存最近 24 小时的活跃会话追踪
  - TTL：5 分钟（热点） / 1 小时（统计）

**长期方案（ClickHouse + OpenTelemetry）**：
- **ClickHouse**：海量数据分析
  - SummingMergeTree：预聚合统计数据
  - ReplicatedMergeTree：高可用副本
  - 适用于 PB 级追踪数据
- **Jaeger/Zipkin**：分布式追踪标准
  - 兼容 OpenTelemetry API
  - 支持跨服务追踪

### 表结构设计

agent_execution_summary（执行汇总表）存储每次执行的汇总数据，包含用户 ID、会话 ID、Agent ID、执行开始时间、执行结束时间、总执行时间、总输入 Token 数、总输出 Token 数、总 Token 数、工具调用次数、总工具执行时间、执行是否成功、错误阶段、错误消息等字段。建立索引以支持用户维度、会话维度、Agent 维度和时间范围的查询。

agent_execution_details（执行详细记录表）存储每个步骤的详细数据，包含会话 ID、消息内容、消息类型、模型部署名称、提供商名称、消息 Token 数、模型调用时间、工具名称、工具请求参数、工具响应数据、工具执行时间、工具执行是否成功、是否使用降级、降级原因、降级前模型和降级后模型等字段。建立索引以支持会话维度、消息类型和时间范围的查询。

### 汇总与详细分离

汇总信息用于快速查询和统计，详细信息用于深度分析和问题排查。分离存储以提高查询性能，列表查询只需要汇总数据，详细数据按需加载，便于数据生命周期管理。

### 批量写入

支持批量写入执行详细记录，减少数据库操作次数，提高写入性能。

## 关键设计决策

### 事件驱动的异步处理

追踪数据处理不应阻塞主流程，追踪系统异常不应影响 Agent 正常执行，提高系统吞吐量和响应速度。

**实现方式**：
- 使用 asyncio.Queue 作为事件总线
- TraceCollector 发布事件到队列（非阻塞）
- TraceEventListener 异步消费事件
- 批量持久化（每 100 条或 5 秒）

### 追踪失败保护机制

追踪是辅助功能，不应影响核心业务，追踪系统异常时自动禁用。

**实现方式**：
- TraceCollector 的所有方法都包裹在 try-catch 中
- 追踪失败时返回禁用的 TraceContext
- Queue 满时自动降级（丢弃低优先级事件）
- 配置开关可临时关闭追踪

### 无侵入式追踪设计

业务代码不需要关心追踪细节，通过事件机制自动收集数据。

**实现方式**：
- 使用 Python 装饰器实现 AOP
- 业务代码调用被装饰的方法
- 装饰器自动记录输入输出和耗时
- 发布领域事件
- TraceEventListener 监听并持久化

### 智能采样机制

**采样策略**：
- **开发环境**：100% 全量采集
- **生产环境**：
  - 默认采样率：10%
  - 按 Trace ID 哈希计算：`hash(trace_id) % 100 < sampling_rate`
  - 保证同一会话完整性（sessionId 一致）
- **强制全量**：
  - 错误/失败请求：100%
  - VIP 用户：100%
  - 白名单用户/Agent：100%

**采样实现**：
```python
def should_sample(trace_id: str, user_id: str, sampling_rate: float) -> bool:
    # 错误请求强制全量
    if is_error_request():
        return True
    # VIP 用户强制全量
    if is_vip_user(user_id):
        return True
    # 白名单强制全量
    if in_whitelist(trace_id):
        return True
    # 哈希采样
    trace_hash = int(hashlib.md5(trace_id.encode()).hexdigest(), 16)
    return (trace_hash % 100) < (sampling_rate * 100)
```

### OpenTelemetry 兼容性设计

**当前阶段**：
- 定义内部 Span/Trace 数据结构
- 保持与 OpenTelemetry 概念对齐（TraceId, SpanId, ParentSpanId）
- 预留 Exporter 接口

**未来迁移路径**：
1. 集成 OpenTelemetry SDK
2. 替换 EventPublisher 为 OTel Span Processor
3. 导出到 Jaeger/Zipkin
4. 保留现有查询 API（适配层）

**数据结构对齐**：
```python
# 当前设计
class TraceContext:
    trace_id: str          # 对应 OTel Trace ID
    span_id: str          # 对应 OTel Span ID
    parent_span_id: str   # 对应 OTel Parent Span ID
    session_id: str
    user_id: str
    
# OpenTelemetry 标准
class Span(OTel):
    context.trace_id
    context.span_id
    parent.span_id
```

## 性能优化

### 异步处理

事件监听器使用 asyncio 异步处理，避免阻塞主流程，提高系统并发能力。

**实现细节**：
- `asyncio.create_task()` 创建后台任务
- `asyncio.Queue` 作为缓冲
- 消费者协程持续处理

### 分层缓存策略

**L1 缓存（内存）**：
- 最近 100 条活跃会话
- TTL：5 分钟
- 使用 functools.lru_cache

**L2 缓存（Redis）**：
- 最近 24 小时数据
- TTL：1 小时
- Redis Hash 结构存储

**L3 存储（PostgreSQL）**：
- 全量数据持久化
- 按需查询

### 批量写入优化

**批量策略**：
- 每 100 条批量写入一次
- 或每 5 秒强制写入一次
- 使用 SQLAlchemy `bulk_insert_mappings`

**失败重试**：
- 指数退避：1s, 2s, 4s
- 最多重试 3 次
- 失败后进入死信队列

### 索引优化

为常用查询字段建立索引，支持高效的时间范围查询和维度查询（用户、会话、Agent）。

**索引设计**：
```sql
-- 用户维度查询
CREATE INDEX idx_summary_user_id ON agent_execution_summary(user_id);

-- 会话维度查询
CREATE INDEX idx_summary_session_id ON agent_execution_summary(session_id);

-- Agent 维度查询
CREATE INDEX idx_summary_agent_id ON agent_execution_summary(agent_id);

-- 时间范围查询
CREATE INDEX idx_summary_exec_time ON agent_execution_summary(execution_start_time DESC);

-- JSONB 字段查询（Gin 索引）
CREATE INDEX idx_details_metadata ON agent_execution_details USING GIN (metadata);
```

### 数据压缩

**压缩策略**：
- 工具调用参数和响应：gzip 压缩
- 长文本输出（>1KB）：gzip 压缩
- 压缩率目标：60%-80%

**透明解压**：
- 查询时自动解压
- 应用层无感知

### 数据生命周期管理

执行详细数据保留期可配置（如 90 天），执行汇总数据保留期可配置（如 1 年），定期清理过期数据，控制存储成本。

**清理任务**：
- 每天凌晨 2 点执行
- 分批删除（每次 1000 条）
- 记录删除日志

## 扩展性设计

### 可扩展的追踪维度

通过事件机制支持新增追踪类型，新增步骤类型只需添加新的事件类型和处理新事件类型的监听器。

### 可扩展的数据处理链

支持多个事件监听器处理同一事件，每个监听器可以处理不同的数据（如存储、统计、监控），便于集成第三方系统。

### 可扩展的存储适配

支持不同的存储实现（MySQL、Elasticsearch、时序数据库），通过 Repository 接口隔离存储细节，便于根据业务需求选择合适的存储方案。

## 监控与运维

### 追踪系统监控

监控追踪成功率、追踪延迟、存储异常率和事件处理积压等指标。

### 性能监控

追踪数据写入耗时、追踪数据查询耗时和异步事件处理队列长度。

### 告警机制

追踪失败率超过阈值时告警、追踪延迟超过阈值时告警、存储异常时告警和事件处理积压时告警。

## 安全设计

### 数据权限隔离

**用户级隔离**：
- 普通用户：仅能查询自己的执行数据
- 通过数据库行级安全策略强制过滤（RLS）
- API 查询时自动注入 `user_id = current_user_id` 条件

**管理员权限**：
- 平台管理员：可以查看所有用户的执行数据
- 需要审计日志记录查询行为
- 支持批量分析（跨用户统计）

**实现方式**：
```python
# Repository 层强制过滤
def get_by_user_id(self, user_id: str, current_user: User):
    if not current_user.is_admin:
        # 非管理员只能查自己
        query = query.filter(AgentExecutionSummary.user_id == current_user.id)
    else:
        # 管理员可以查指定用户
        query = query.filter(AgentExecutionSummary.user_id == user_id)
```

### 敏感数据脱敏

**脱敏规则引擎**：
- PII 自动识别和掩码（手机号、邮箱、身份证）
- 认证信息完全移除（Token、API Key、密码）
- 自定义正则匹配脱敏字段

**脱敏实现**：
```python
class DataMasker:
    MASK_PATTERNS = {
        'phone': (r'1[3-9]\d{9}', lambda m: m.group()[:3] + '****' + m.group()[-4:]),
        'email': (r'[\w.-]+@[\w.-]+', lambda m: m.group().split('@')[0][:3] + '***@' + m.group().split('@')[1]),
        'token': (r'\b(token|apikey|secret)\b.*', lambda m: '***'),
    }
    
    def mask(self, data: str) -> str:
        for pattern, replacer in self.MASK_PATTERNS.values():
            data = re.sub(pattern, replacer, data, flags=re.IGNORECASE)
        return data
```

### 访问控制列表（ACL）

**角色定义**：
- `USER`：普通用户，仅查看自己的数据
- `ADMIN`：管理员，查看和管理所有数据
- `AUDITOR`：审计员，只读查看所有数据

**权限矩阵**：
| 操作 | USER | ADMIN | AUDITOR |
|------|------|-------|---------|
| 查看自己的追踪 | ✓ | ✓ | ✓ |
| 查看他人的追踪 | ✗ | ✓ | ✓ |
| 删除追踪 | ✗ | ✓ | ✗ |
| 导出追踪 | ✓ | ✓ | ✓ |
| 查看统计 | 仅自己 | 全部 | 全部 |

### 数据加密存储

**传输加密**：
- 所有 API 使用 HTTPS
- PostgreSQL 连接使用 SSL

**存储加密**：
- 数据库启用 TDE（透明数据加密）
- 敏感字段应用层加密（Fernet 对称加密）
- Redis 缓存加密（可选）

**密钥管理**：
- 使用环境变量存储密钥
- 定期轮换密钥
- 密钥版本化管理

### 审计日志

**操作审计**：
- 记录所有查询操作：谁、何时、查了谁、什么条件、多少结果
- 审计日志独立存储（与追踪数据分离）
- 审计日志保留期：2 年

**异常检测**：
- 检测频繁跨用户查询行为
- 检测大批量数据导出行为
- 触发告警通知安全管理员

## 与其他模块的集成

### 与会话管理的集成

在会话开始时初始化追踪上下文，通过 sessionId 关联追踪数据与会话，支持按会话 ID 查询执行历史。

### 与 Agent 管理的集成

追踪数据与 Agent 绑定，支持按 Agent 维度的性能分析，统计每个 Agent 的执行指标。

### 与模型管理的集成

记录模型调用的详细信息，支持模型维度的成本分析，追踪模型降级情况。

### 与工具管理的集成

记录工具调用的详细信息，统计工具的使用频率和成功率，分析工具的性能表现。

### 与高可用能力的集成

记录降级事件，分析降级频率和原因，为高可用策略优化提供数据支持。

### 与计费能力的集成

Token 使用统计数据用于计费，支持按 Agent 维度的成本分析，提供成本相关的统计 API。

## 数据一致性

采用异步事件处理，数据是最终一致的，追踪数据可能存在短暂的延迟，对于实时性要求不高的场景可以接受。执行汇总和详细记录通过 sessionId 关联，执行完成后更新汇总信息，定期检查数据一致性。提供数据修复工具，支持重新计算汇总数据和补充缺失的详细数据。

## 技术栈

**核心框架**：
- FastAPI：Web 框架和 API 路由
- SQLAlchemy：ORM 和数据持久化
- Pydantic：数据验证和 DTO

**存储层**：
- PostgreSQL 14+：主存储数据库（支持 JSONB）
- Redis 6+：热点数据缓存
- ClickHouse（可选）：大规模分析

**异步处理**：
- asyncio：异步 IO 框架
- aiofiles：异步文件操作
- asyncpg：PostgreSQL 异步驱动

**监控和日志**：
- structlog：结构化日志
- Prometheus + Grafana：指标监控
- OpenTelemetry（未来）：分布式追踪

**工具库**：
- python-jose：JWT 认证
- passlib：密码加密
- gzip：数据压缩
- hashlib：哈希采样

## 未来演进方向

### 实时流式追踪

引入消息队列实现真正的流式追踪，支持实时展示执行过程，提升用户体验。

**实现方案**：
- 使用 Kafka/RabbitMQ 作为事件总线
- WebSocket 推送实时追踪数据
- 前端实时更新执行进度

### 分布式追踪（OpenTelemetry）

集成 OpenTelemetry 等分布式追踪标准，实现跨服务的追踪能力。

**迁移步骤**：
1. 定义 OTel Span 数据结构映射
2. 集成 OpenTelemetry SDK
3. 部署 Jaeger/Zipkin Collector
4. 逐步替换内部事件系统
5. 保留现有 API（适配层）

**收益**：
- 标准化追踪协议
- 与现有 APM 工具集成
- 跨语言追踪支持
- 丰富的可视化生态

### AI 驱动的智能分析

**异常检测**：
- 基于历史数据自动识别异常模式
- 预测性告警（提前发现潜在问题）

**根因分析**：
- 自动关联失败原因
- 推荐优化建议

**成本优化**：
- 智能识别高成本调用
- 推荐更经济的模型选择

### 增强的可视化能力

**链路图谱**：
- 交互式执行链路图
- 依赖关系可视化
- 性能瓶颈热力图

**自定义仪表板**：
- 用户可配置的统计视图
- 多维度数据对比
- 导出定制化报表