## 实施清单

### 一、核心服务层（依赖 011-session-context）

**说明**: Session/Message/Context的实体模型、仓储和基础领域服务已在 011-session-context中实现，本模块直接复用。

- [ ] 1.1 引用 011 的 Session 领域服务
     【目标对象】`app/domain/conversation/services/session_domain_service.py`
     【修改目的】复用已实现的会话管理能力
     【相关依赖】011-session-context 已完成
     【修改内容】
        - 直接使用 011 中的 SessionDomainService
        - 无需重复实现 CRUD 操作

- [ ] 1.2 引用 011 的 Message 领域服务
     【目标对象】`app/domain/conversation/services/message_domain_service.py`
     【修改目的】复用已实现的消息管理能力
     【相关依赖】011-session-context 已完成
     【修改内容】
        - 直接使用 011 中的 MessageDomainService
        - 专注于消息处理逻辑而非存储

- [ ] 1.3 引用 011 的 Context 领域服务
     【目标对象】`app/domain/conversation/services/context_domain_service.py`
     【修改目的】复用已实现的上下文管理能力
     【相关依赖】011-session-context 已完成
     【修改内容】
        - 直接使用 011 中的 ContextDomainService
        - 使用其提供的 Token 计算和窗口管理接口

### 二、聊天模式处理器（013 核心）

- [ ] 2.1 实现 AbstractMessageHandler 基类
     【目标对象】`app/application/conversation/handlers/abstract_message_handler.py`
     【修改目的】定义消息处理器的统一接口和模板方法
     【修改方式】使用 Python ABC 抽象基类
     【修改内容】
        - 定义 handle 抽象方法（子类实现）
        - 实现公共方法：send_token、send_event、save_message
        - 实现流式响应辅助方法
        - 实现执行追踪集成方法

- [ ] 2.2 实现 ChatMessageHandler（标准对话）
     【目标对象】`app/application/conversation/handlers/chat_message_handler.py`
     【修改目的】处理标准对话模式
     【修改内容】
        - 继承 AbstractMessageHandler
        - 实现简单问答逻辑
        - 集成记忆提取和注入
        - 支持流式响应

- [ ] 2.3 实现 AgentMessageHandler（Agent 智能体）
     【目标对象】`app/application/conversation/handlers/agent_message_handler.py`
     【修改目的】处理 Agent 对话模式
     【修改内容】
        - 继承 AbstractMessageHandler
        - **集成工具调用链路**:
          - 解析 LLM 返回的工具调用请求
          - 调用 AgentToolManager 执行工具
          - 收集工具结果并返回给 LLM
        - **集成执行追踪**:
          - 记录每个工具调用的详细信息（名称、参数、耗时、结果）
          - 标记执行阶段（分析、执行、汇总）
          - 关联追踪 ID
        - **工作流集成**:
          - 调用 014-agent-workflow 的任务拆分能力
          - 订阅工作流事件并转换为对话消息
          - 向用户展示任务进度
        - 支持流式响应和中断

- [ ] 2.4 实现 RagMessageHandler（RAG 检索增强）
     【目标对象】`app/application/conversation/handlers/rag_message_handler.py`
     【修改目的】处理 RAG 对话模式
     【修改内容】
        - 继承 AbstractMessageHandler
        - **检索流程集成**:
          - 调用 RAGSearchAppService 进行文档检索
          - 支持多数据集和单文件检索
          - 应用相似度阈值过滤
        - **检索结果注入**:
          - 将检索结果格式化为系统消息
          - 插入到对话上下文中
          - 控制引用数量（top_k 配置）
        - **流式响应**:
          - 分阶段推送事件：retrieval_start → retrieval_progress → retrieval_end → thinking → answer
          - 展示检索到的文档片段

- [ ] 2.5 实现 PreviewMessageHandler（预览模式）
     【目标对象】`app/application/conversation/handlers/preview_message_handler.py`
     【修改目的】处理 Agent 预览测试
     【修改内容】
        - 继承 AgentMessageHandler
        - 实现临时会话创建（不持久化）
        - 快速验证智能体配置
        - 限制功能（如不计费、不保存历史）

- [ ] 2.6 实现 MessageHandlerFactory
     【目标对象】`app/application/conversation/handlers/message_handler_factory.py`
     【修改目的】根据请求自动选择处理器
     【修改内容】
        - **处理器注册表**:
          - 使用字典存储处理器：{chat_mode: handler_instance}
          - 支持动态注册新处理器
        - **优先级规则**:
          - preview (优先级 1) > rag (优先级 2) > agent (优先级 3) > standard (优先级 4)
          - 基于 agent_id 和 chat_mode 参数自动选择
        - **懒加载**: 首次使用时才实例化处理器
        - **单例模式**: 每个处理器类型只创建一次

### 三、流式响应与实时通信

- [ ] 3.1 实现 SSE 流式响应端点
     【目标对象】`app/api/v1/endpoints/sse_endpoints.py`
     【修改目的】提供 SSE 流式输出能力
     【修改方式】使用 sse-starlette 库
     【修改内容】
        - **SSE 端点**:
          - `POST /api/v1/sessions/{sessionId}/chat/stream` - 标准流式聊天
          - `POST /api/v1/agents/{agentId}/chat/stream` - Agent 流式聊天
          - `POST /api/v1/rag/{ragId}/chat/stream` - RAG 流式聊天
        - **EventSourceResponse 使用**:
          - 创建 EventSourceResponse 对象
          - 异步生成器推送 token
          - 设置合适的 headers（Content-Type: text/event-stream）
        - **chunk 大小策略**:
          - 每 20-50 tokens 推送一次（避免过频）
          - 完整句子优先（遇到标点符号推送）
        - **断线重连支持**:
          - 记录 last-event-id
          - 客户端重连时从中断点恢复
          - 最多重试 3 次
        - **背压控制**:
          - 使用 asyncio.Queue(maxsize=100) 缓冲事件
          - 防止内存溢出
        - **错误处理**:
          - 捕获异常并推送 error 事件
          - 清理 SSE 连接资源

- [ ] 3.2 实现 WebSocket 连接管理器
     【目标对象】`app/infrastructure/websocket/connection_manager.py`
     【修改目的】管理 WebSocket 连接（备选方案）
     【修改内容】
        - **连接池管理**:
          - 维护活跃连接字典：{session_id: websocket}
          - 支持广播和单播
        - **心跳检测**:
          - 每 30s 发送 ping 消息
          - 90s 无响应自动断开
        - **认证机制**:
          - 连接建立时验证 JWT Token
          - 未授权连接立即拒绝

- [ ] 3.3 实现 Agent WebSocket 路由
     【目标对象】`app/api/v1/websocket/agent_websocket.py`
     【修改目的】处理 Agent WebSocket 连接
     【修改内容】
        - 端点：`/ws/agents/{agentId}/sessions`
        - 使用 FastAPI WebSocket
        - 消息接收和转发
        - 认证和授权

- [ ] 3.4 实现 SSE/WebSocket 双协议兼容
     【修改目的】支持降级策略
     【修改内容】
        - 优先使用 SSE（浏览器兼容性好）
        - 检测到不支持 SSE 时降级为 WebSocket
        - 统一的 event 格式定义

### 四、安全与输入验证

- [ ] 4.1 实现敏感词过滤器
     【目标对象】`app/domain/conversation/security/sensitive_word_filter.py`
     【修改目的】过滤用户输入中的敏感词
     【修改内容】
        - 从配置文件加载敏感词库
        - 支持正则表达式匹配
        - 替换敏感词为 ***
        - 记录过滤日志

- [ ] 4.2 实现 Prompt 注入检测
     【目标对象】`app/domain/conversation/security/prompt_injection_detector.py`
     【修改目的】检测并阻止 Prompt 注入攻击
     【修改内容】
        - 检测模式：忽略指令、角色扮演攻击、越狱尝试
        - 使用正则 + 关键词匹配
        - 高风险输入直接拒绝并告警

- [ ] 4.3 实现用户输入长度验证
     【目标对象】`app/application/conversation/validators/message_validator.py`
     【修改目的】限制用户输入长度
     【修改内容】
        - Pydantic Validator 实现
        - 最大长度：4000 tokens
        - 超出限制返回清晰的错误提示

- [ ] 4.4 实现工具调用白名单校验
     【目标对象】`app/application/conversation/security/tool_call_validator.py`
     【修改目的】确保工具调用的安全性
     【修改内容】
        - 检查工具是否在已注册列表中
        - 验证用户是否有工具访问权限
        - 检查工具调用频率限制
        - 黑名单工具禁止调用

### 五、性能优化

- [ ] 5.1 实现异步批量消息提交
     【目标对象】`app/domain/conversation/services/message_batch_service.py`
     【修改目的】提高消息持久化效率
     【修改内容】
        - 使用 asyncio.gather 批量保存消息
        - 限制并发数：max_concurrency=10
        - 批处理大小：10 条消息一批
        - 超时控制：单次批量 < 100ms

- [ ] 5.2 实现会话缓存
     【目标对象】`app/infrastructure/cache/session_cache.py`
     【修改目的】加速会话访问
     【修改内容】
        - **缓存 Key 设计**: `session:{id}:context`
        - **失效策略**: 
          - TTL = 30 分钟（无活动自动过期）
          - LRU（内存不足时淘汰最少使用）
        - **缓存内容**: 会话上下文、最近 10 条消息
        - **Redis 集成**: 分布式缓存支持

- [ ] 5.3 实现 Token 预算控制
     【目标对象】`app/domain/conversation/services/token_budget_service.py`
     【修改目的】管理上下文 Token 分配
     【修改内容】
        - **滑动窗口算法**:
          - 历史消息占 70% Token 预算
          - 当前对话预留 30%
          - 动态调整窗口大小
        - **实时监控**:
          - 每次添加消息前检查 Token 余量
          - 超出预算时触发压缩或截断
        - **压缩策略优先级**:
          1. 摘要压缩（早期消息）
          2. 截断最早的消息
          3. 移除工具调用详情（保留结果）

- [ ] 5.4 实现限流中间件集成
     【目标对象】`app/infrastructure/ratelimit/rate_limiter.py`
     【修改目的】防止 API 滥用
     【修改方式】使用 slowapi 库
     【修改内容】
        - 单用户每秒 ≤ 5 个会话创建
        - 单用户每分钟 ≤ 60 次工具调用
        - 单 IP 每分钟 ≤ 100 次请求
        - 超限返回 429 Too Many Requests

### 六、执行追踪集成

- [ ] 6.1 实现对话追踪上下文
     【目标对象】`app/domain/conversation/tracing/chat_tracing_context.py`
     【修改目的】记录对话执行的完整链路
     【修改内容】
        - 创建追踪上下文（trace_id, span_id）
        - 记录会话 ID、Agent ID、开始时间
        - 关联用户 ID 和 tenant_id

- [ ] 6.2 集成模型调用追踪
     【目标对象】`app/domain/conversation/tracing/model_call_tracer.py`
     【修改目的】记录 LLM 调用详情
     【修改内容】
        - 记录服务商、模型名称
        - 记录 prompt tokens、completion tokens
        - 记录调用耗时
        - 记录温度、top_p 等参数

- [ ] 6.3 集成工具调用追踪
     【目标对象】`app/domain/conversation/tracing/tool_call_tracer.py`
     【修改目的】记录工具执行详情
     【修改内容】
        - 记录工具名称、输入参数
        - 记录执行结果
        - 记录执行耗时
        - 记录成功/失败状态

### 七、计费集成

- [ ] 7.1 实现 Token 用量统计
     【目标对象】`app/domain/conversation/billing/token_usage_calculator.py`
     【修改目的】精确统计 Token 使用量
     【修改内容】
        - 每次对话后计算总 Token 数
        - 区分 prompt tokens 和 completion tokens
        - 按用户和模型分类

- [ ] 7.2 实现余额检查
     【目标对象】`app/application/conversation/billing/balance_checker.py`
     【修改目的】防止欠费使用
     【修改内容】
        - 对话前查询用户账户余额
        - 预估本次对话费用
        - 余额不足抛出 InsufficientBalanceException
        - 提示用户充值

- [ ] 7.3 实现用量上报
     【目标对象】`app/domain/conversation/billing/usage_reporter.py`
     【修改目的】将用量记录同步到计费模块
     【修改方式】异步上报（不阻塞主流程）
     【修改内容】
        - 构建 UsageRecord 对象
        - 异步调用计费服务 API
        - 记录失败重试机制

### 八、API 路由层

- [ ] 8.1 创建会话管理端点
     【目标对象】`app/api/v1/endpoints/sessions.py`
     【修改目的】暴露会话管理的 HTTP API
     【修改内容】
        - `POST /api/v1/agents/{agentId}/sessions` - 创建会话
        - `GET /api/v1/agents/{agentId}/sessions` - 获取会话列表
        - `GET /api/v1/sessions/{sessionId}` - 获取会话详情
        - `PUT /api/v1/sessions/{sessionId}` - 更新会话
        - `DELETE /api/v1/sessions/{sessionId}` - 删除会话

- [ ] 8.2 创建消息管理端点
     【目标对象】`app/api/v1/endpoints/messages.py`
     【修改内容】
        - `POST /api/v1/sessions/{sessionId}/messages` - 发送消息
        - `GET /api/v1/sessions/{sessionId}/messages` - 获取消息历史（分页）
        - `GET /api/v1/sessions/{sessionId}/messages/{messageId}` - 获取单条消息
        - `DELETE /api/v1/sessions/{sessionId}/messages/{messageId}` - 删除消息

- [ ] 8.3 创建聊天端点
     【目标对象】`app/api/v1/endpoints/chat.py`
     【修改内容】
        - `POST /api/v1/sessions/{sessionId}/chat` - 聊天（同步）
        - `POST /api/v1/sessions/{sessionId}/chat/stream` - 聊天（流式 SSE）
        - `POST /api/v1/agents/{agentId}/preview` - Agent 预览对话
        - `POST /api/v1/rag/{ragId}/chat` - RAG 对话
        - `POST /api/v1/rag/{ragId}/chat/stream` - RAG 流式对话

### 九、DTO 和 Assembler

- [ ] 9.1 创建聊天 DTO
     【目标对象】`app/application/conversation/dto/chat_dto.py`
     【修改内容】
        - ChatRequestDTO - 聊天请求（content、stream、chat_mode）
        - ChatResponseDTO - 聊天响应（message_id、content、token_usage）
        - StreamChatRequestDTO - 流式请求
        - AgentChatResponseDTO - Agent 专用响应（包含工具调用信息）
        - RagChatRequestDTO - RAG 专用请求（包含检索参数）
        - RagRetrievalDocumentDTO - RAG 检索结果

- [ ] 9.2 实现 Assembler
     【目标对象】`app/application/conversation/assembler/`
     【修改内容】
        - MessageAssembler - Message 实体 ↔ DTO 转换
        - SessionAssembler - Session 实体 ↔ DTO 转换

### 十、单元测试

- [ ] 10.1 测试消息处理器
     【目标对象】`tests/unit/application/test_message_handlers.py`
     【修改目的】确保各处理器逻辑正确
     【修改内容】
        - 测试 ChatMessageHandler 的标准对话
        - 测试 AgentMessageHandler 的工具调用（Mock ToolManager）
        - 测试 RagMessageHandler 的检索注入（Mock RAGService）
        - 测试 PreviewMessageHandler 的临时会话

- [ ] 10.2 测试流式响应
     【目标对象】`tests/unit/infrastructure/test_sse_response.py`
     【修改内容】
        - 测试 SSE 事件生成器
        - 测试 chunk 大小策略
        - 测试背压控制（Queue 满时行为）
        - 测试断线重连逻辑

- [ ] 10.3 测试安全组件
     【目标对象】`tests/unit/domain/security/`
     【修改内容】
        - 测试敏感词过滤器
        - 测试 Prompt 注入检测（各种攻击模式）
        - 测试工具调用白名单校验
        - 测试输入长度验证

- [ ] 10.4 测试性能优化
     【目标对象】`tests/unit/domain/services/`
     【修改内容】
        - 测试异步批量提交（并发数限制）
        - 测试 Token 预算控制（滑动窗口）
        - 测试缓存失效策略

### 十一、集成测试

- [ ] 11.1 测试聊天 API 端到端
     【目标对象】`tests/integration/test_chat_api.py`
     【修改内容】
        - 测试同步聊天端点（正常流程、异常流程）
        - 测试流式聊天端点（SSE 事件流完整性）
        - 测试 Agent 预览端点
        - 测试 RAG 对话端点
        - 测试错误处理（400、401、403、429、500）

- [ ] 11.2 测试 WebSocket 连接
     【目标对象】`tests/integration/test_websocket.py`
     【修改内容】
        - 测试 Agent WebSocket 连接（使用 websockets.client）
        - 测试 Session WebSocket 连接
        - 测试消息收发
        - 测试心跳检测（90s 超时）
        - 测试连接断开处理

- [ ] 11.3 压力测试
     【目标对象】`tests/stress/test_concurrent_sessions.py`
     【修改内容】
        - **并发会话测试**: 同时创建 1000+ 会话并发送消息
        - **长连接稳定性测试**: 维持 100 个 SSE 连接 24 小时
        - **资源泄漏检测**: 监控内存和连接数增长
        - **限流测试**: 验证速率限制生效

- [ ] 11.4 安全测试
     【目标对象】`tests/security/`
     【修改内容】
        - **Prompt 注入攻击测试**: 尝试各种越狱模式
        - **工具调用越权测试**: 尝试调用未授权工具
        - **会话劫持测试**: 尝试访问他人会话
        - **SQL 注入测试**: 在输入中注入 SQL 语句

- [ ] 11.5 性能测试
     【目标对象】`tests/performance/`
     【修改内容】
        - **首 Token延迟测试**: 测量 P50/P90/P95延迟
        - **流式响应频率测试**: 验证 chunk间隔 100-200ms
        - **吞吐量测试**: 最大消息处理能力
        - **并发连接测试**: SSE 连接数上限

### 十二、数据库迁移

**说明**: 表结构已在 011-session-context 中创建，本模块无需重复迁移。

- [ ] 12.1 确认 sessions 表已存在
     【相关依赖】011-session-context 的迁移脚本

- [ ] 12.2 确认 messages 表已存在
     【相关依赖】011-session-context 的迁移脚本

- [ ] 12.3 确认 contexts 表已存在
     【相关依赖】011-session-context 的迁移脚本

### 十三、文档和配置

- [ ] 13.1 更新 OpenAPI 文档
     【目标对象】`app/api/v1/openapi.yaml`
     【修改内容】
        - 添加会话端点文档
        - 添加消息端点文档
        - 添加聊天端点文档
        - 添加 SSE 端点文档（EventSchema）
        - 添加 WebSocket 端点文档

- [ ] 13.2 更新配置文件
     【目标对象】`config/settings.py`
     【修改内容】
        - SSE 配置：chunk_size=30, heartbeat_interval=30
        - 会话缓存配置：cache_ttl=1800, cache_max_size=10000
        - 限流配置：rate_limit_per_second=5, rate_limit_per_minute=60
        - Token 预算配置：budget_history_ratio=0.7, budget_current_ratio=0.3
        - 安全配置：max_message_length=4000, sensitive_word_enabled=true

- [ ] 13.3 编写使用文档
     【目标对象】`docs/conversation/README.md`
     【修改内容】
        - 聊天模式使用说明
        - SSE 事件格式说明
        - 错误码说明
        - 最佳实践（如何选择合适的模式）
