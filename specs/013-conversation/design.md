# 对话管理技术设计

## 概述

对话管理模块采用分层架构设计，符合领域驱动设计原则。基于 Python FastAPI 生态系统实现，支持多种聊天模式、流式响应（SSE 优先）、Agent 工作流集成、RAG 检索增强、记忆管理集成、高可用支持和计费集成等核心功能。

## 技术架构

### 分层架构

系统采用四层架构：

**接口层（Interfaces Layer）**:
- REST API - 使用 FastAPI Router 定义 HTTP 端点
- SSE Endpoints - 使用 sse-starlette 的 EventSourceResponse
- WebSocket - 使用 FastAPI WebSocket
- DTOs - Pydantic v2 模型定义请求/响应结构

**应用层（Application Layer）**:
- ConversationAppService - 对话业务编排（使用依赖注入）
- ChatSessionManager - 会话生命周期管理（基于内存 + Redis 缓存）
- MessageHandlerFactory - 处理器工厂（字典注册表 + 懒加载）
- 各种 MessageHandler - 标准、Agent、RAG、预览模式处理器

**领域层（Domain Layer）**:
- 领域服务 - SessionDomainService、MessageDomainService、ContextDomainService（复用 011）
- 实体模型 - SessionEntity、MessageEntity、ContextEntity（复用 011）
- 仓储接口 - Repository 模式（SQLAlchemy 异步实现）
- 安全组件 - 敏感词过滤、Prompt 注入检测、工具调用验证

**基础设施层（Infrastructure Layer）**:
- 持久化 - SQLAlchemy 2.0 异步 ORM + Alembic 迁移
- 缓存 - Redis（会话缓存、分布式锁）
- 外部服务 - LLM SDK、RAG Service、Tool Manager
- 消息队列 - asyncio.Queue（背压控制）
- 日志 - structlog 结构化日志

### 设计原则

**领域驱动设计 (DDD)**:
- 实体（Entity）：Session、Message、Context 有唯一标识和生命周期
- 值对象（Value Object）：TokenUsage、ChatMode 等不可变对象
- 聚合根（Aggregate Root）：Session 作为聚合根管理消息和上下文
- 仓储（Repository）：数据访问抽象，支持替换实现

**依赖倒置**:
- 高层模块不依赖低层模块，都依赖抽象（接口）
- 使用 Python ABC 模块定义抽象基类
- 通过依赖注入容器管理生命周期

**单一职责**:
- 每个类只负责一项职责
- Handler 只处理消息，Service 只编排业务，Repository 只访问数据

**开闭原则**:
- 对扩展开放（新增处理器无需修改现有代码）
- 对修改关闭（通过工厂模式和策略模式实现）

## 核心组件

### 应用层组件

**ConversationAppService** - 对话应用服务

职责：作为应用层统一入口，协调对话相关的业务用例。

依赖：
- SessionDomainService（复用 011）
- MessageDomainService（复用 011）
- ContextDomainService（复用 011）
- MessageHandlerFactory
- ChatSessionManager
- LLMDomainService
- TokenDomainService
- BalanceChecker（计费集成）

核心方法：
- `create_session(user_id, agent_id, metadata)` - 创建会话
- `delete_session(session_id)` - 删除会话
- `get_session_list(user_id, page, page_size)` - 获取会话列表
- `chat_sync(chat_request)` - 同步聊天（阻塞等待完整响应）
- `chat_stream(chat_request)` - 流式聊天（返回 EventSourceResponse）
- `preview_agent(agent_id, message)` - Agent 预览对话

**MessageHandlerFactory** - 消息处理器工厂

**实现文件**: `app/application/conversation/handlers/message_handler_factory.py`

职责：根据请求参数自动选择合适的消息处理器。

实现细节：
- **注册表设计**: 使用字典存储 `{chat_mode: handler_instance}`
- **优先级规则**: 
  ```
  preview (1) > rag (2) > agent (3) > standard (4)
  ```
- **选择逻辑**:
  1. 检查是否 preview=true → PreviewMessageHandler
  2. 检查是否包含 rag_id → RagMessageHandler
  3. 检查 chat_mode="agent" → AgentMessageHandler
  4. 默认 → ChatMessageHandler
- **懒加载**: 首次使用时才实例化处理器
- **单例模式**: 每个处理器类型全局唯一

**AbstractMessageHandler** - 抽象消息处理器基类

**实现文件**: `app/application/conversation/handlers/abstract_message_handler.py`

职责：定义消息处理的模板方法和公共逻辑。

实现细节：
- 使用 Python `abc.ABC` 定义抽象基类
- **模板方法**:
  ```python
  async def handle(self, chat_context: ChatContext) -> AsyncGenerator[Event, None]:
      # 1. 前置处理（验证、安全检查）
      await self.pre_process(chat_context)
      
      # 2. 执行处理（子类实现）
      async for event in self.do_handle(chat_context):
          yield event
      
      # 3. 后置处理（持久化、计费）
      await self.post_process(chat_context)
  ```
- **抽象方法**: `do_handle(chat_context)` - 子类实现具体处理逻辑
- **公共方法**:
  - `send_token(content)` - 推送 token
  - `send_event(event_type, data)` - 推送事件
  - `save_message(message)` - 保存消息（异步批量）
  - `record_usage(token_usage)` - 记录用量

**子类实现**:

1. **ChatMessageHandler** - 标准对话处理器
   
   **实现文件**: `app/application/conversation/handlers/chat_message_handler.py`
   
   - 实现简单问答逻辑
   - 调用 LLMDomainService 完成对话
   - 集成记忆提取和注入

2. **AgentMessageHandler** - Agent 智能体处理器
   
   **实现文件**: `app/application/conversation/handlers/agent_message_handler.py`
   
   - **工具调用链路**:
     - 解析 LLM 返回的 tool_calls
     - 调用 AgentToolManager 执行工具
     - 收集结果并返回给 LLM
   - **工作流集成**:
     - 调用 014-agent-workflow 进行任务拆分
     - 订阅工作流事件：TaskCreated、TaskCompleted、TaskFailed
     - 转换为对话消息推送给用户
   - **执行追踪**:
     - 记录每个工具的调用详情
     - 标记执行阶段（ANALYZING → SPLITTING → EXECUTING → SUMMARIZING）

3. **RagMessageHandler** - RAG 检索增强处理器
   
   **实现文件**: `app/application/conversation/handlers/rag_message_handler.py`
   
   - **检索流程**:
     - 调用 RAGSearchAppService 检索文档
     - 应用 top_k 和 similarity_threshold 参数
     - 重排序检索结果
   - **结果注入**:
     - 将检索结果格式化为系统消息
     - 插入到对话上下文开头
   - **分阶段推送**:
     - retrieval_start → retrieval_progress → retrieval_end
     - thinking_start → thinking_progress → thinking_end
     - answer_start → [token stream] → answer_end

4. **PreviewMessageHandler** - 预览模式处理器
   
   **实现文件**: `app/application/conversation/handlers/preview_message_handler.py`
   
   - 继承 AgentMessageHandler
   - 创建临时会话（不持久化）
   - 跳过计费和历史记录

**ChatSessionManager** - 会话管理器

职责：管理正在进行的聊天会话。

实现细节：
- **连接注册表**: `Dict[session_id, SSEConnection]`
- **内存缓存**: LRU Cache 存储活跃会话上下文
- **Redis 共享**: 分布式环境下跨节点同步会话状态
- **超时清理**: 
  - 30 分钟无活动自动断开
  - 后台任务定期扫描（每 5 分钟）
- **中断控制**:
  - 用户发送中断信号 → 停止 LLM 流式输出
  - 关闭 SSE 连接
  - 释放资源

### 领域层组件

**领域模型**（复用 011-session-context）:

- **SessionEntity**: 会话实体
  - 字段：id (UUID), title, user_id, agent_id, description, is_archived, metadata
  - 方法：add_message(), archive(), restore()
  
- **MessageEntity**: 消息实体
  - 字段：id (UUID), session_id, role, content, message_type, token_count, provider, model, file_urls, metadata
  - 枚举：Role (USER, ASSISTANT, SYSTEM), MessageType (TEXT, TOOL_CALL, TOOL_RESPONSE, TASK_EXEC, etc.)
  
- **ContextEntity**: 上下文实体
  - 字段：id (UUID), session_id, active_message_ids (JSON), summary, total_tokens, max_capacity
  - 方法：add_message(), remove_message(), compress()

**领域服务**（部分复用 011，013 新增安全组件）:

**Security Components** - 安全组件（013 新增）

1. **SensitiveWordFilter** - 敏感词过滤器
   
   **实现文件**: `app/domain/conversation/security/sensitive_word_filter.py`
   
   - 从配置加载敏感词库
   - Trie 树高效匹配
   - 替换策略：***
   
2. **PromptInjectionDetector** - Prompt 注入检测
   
   **实现文件**: `app/domain/conversation/security/prompt_injection_detector.py`
   
   - 正则模式匹配：忽略指令、角色扮演、越狱尝试
   - 风险评分：0-100
   - 高风险直接拒绝
   
3. **ToolCallValidator** - 工具调用验证器
   - 白名单检查
   - 权限验证
   - 频率限制检查

ChatContext 封装对话所需的所有信息，包括会话 ID、用户 ID、用户消息、智能体实体、模型实体、服务商实体、大模型配置、上下文实体、历史消息列表、MCP server 名称、多模态文件、高可用实例 ID、流式响应标志、追踪上下文、公开访问标志和公开访问 ID。

## 流式响应实现

### SSE（Server-Sent Events）优先方案

**技术选型**: sse-starlette 的 EventSourceResponse

**实现文件**: `app/api/v1/endpoints/sse_endpoints.py`

**API 端点**:
- `POST /api/v1/sessions/{sessionId}/chat/stream` - 标准流式聊天
- `POST /api/v1/agents/{agentId}/chat/stream` - Agent 流式聊天
- `POST /api/v1/rag/{ragId}/chat/stream` - RAG 流式聊天

实现细节：

1. **创建 EventSourceResponse**:
   ```python
   from sse_starlette.sse import EventSourceResponse
   
   async def chat_stream_endpoint(request: ChatRequest):
       async def event_generator():
           async for event in conversation_app_service.chat_stream(request):
               yield {
                   "event": event.type,
                   "data": json.dumps(event.data),
                   "id": event.id
               }
       
       return EventSourceResponse(
           event_generator(),
           headers={
               "Cache-Control": "no-cache",
               "Connection": "keep-alive",
               "X-Accel-Buffering": "no"  # Nginx 禁用缓冲
           }
       )
   ```

2. **chunk 大小策略**:
   - 每 20-50 tokens 推送一次（平衡延迟和流量）
   - 遇到标点符号优先推送（保证句子完整性）
   - 最大等待时间 200ms（避免长时间无输出）

3. **背压控制**:
   - 使用 `asyncio.Queue(maxsize=100)` 缓冲事件
   - 生产者（LLM 流式输出）速度 > 消费者（网络推送）时阻塞
   - 防止内存溢出

4. **断线重连支持**:
   - 客户端发送 `Last-Event-ID` header
   - 服务端从中断点恢复（需要缓存最近 100 个事件）
   - 最多重试 3 次，失败后返回错误

5. **心跳机制**:
   - 每 30s 发送注释行（`: heartbeat`）保持连接
   - 防止防火墙和代理断开空闲连接

### WebSocket 备选方案

**技术选型**: FastAPI WebSocket

**实现文件**: `app/api/v1/websocket/agent_websocket.py`

**API 端点**: `/ws/agents/{agentId}/sessions`

**使用场景**:
- 需要双向通信（如实时中断）
- 浏览器不支持 SSE（罕见）

**降级策略**:
- 前端优先尝试 SSE
- 检测到不支持时降级为 WebSocket
- 统一的 event 格式定义

### SSE 事件格式标准

**通用事件结构**:
```json
{
  "event": "token|thought|tool_call|tool_result|error|...",
  "data": {
    "session_id": "sess_xxx",
    "message_id": "msg_xxx",
    "content": "...",
    "timestamp": 1710403200000
  },
  "id": "evt_001"
}
```

**典型事件序列**（Agent 模式）:
```
event: start
data: {"session_id":"sess_001","message_id":"msg_001"}

event: thought
data: {"type":"analysis","content":"用户需要查询天气..."}

event: tool_call
data: {"tool_name":"weather_query","arguments":{"city":"北京"}}

event: tool_result
data: {"tool_name":"weather_query","result":"晴，25°C"}

event: token
data: {"content":"今"}
event: token
data: {"content":"天"}
// ... 更多 token
event: end
data: {"finish_reason":"stop","token_usage":{"total_tokens":200}}
```

### 错误处理

**SSE 连接异常**:
- 捕获 `asyncio.CancelledError`（用户中断）
- 捕获 `TimeoutError`（LLM 超时）
- 推送 error 事件：`{"event":"error","data":{"code":"...","message":"..."}}`
- 清理资源（关闭连接、释放缓存）

**断线恢复**:
- 后台任务监控连接状态
- 断线时自动清理会话注册
- 记录详细日志用于排查

## 记忆集成

### 记忆提取

从对话历史中自动提取关键信息，异步调用记忆抽取服务，将提取的记忆保存到领域服务。

### 记忆注入

将相关记忆注入到系统提示中，根据用户消息搜索相似记忆，构建记忆文本并追加到系统提示。

## Agent 工作流

### 事件驱动架构

使用事件总线协调工作流，应用服务发布事件，监听器订阅并处理事件，通过事件驱动状态转换。

### 工作流状态

AgentWorkflowState 定义工作流状态，包括 IDLE（空闲）、ANALYZING（分析中）、TASK_SPLIT（任务拆分）、TASK_EXECUTE（任务执行）、SUMMARIZING（汇总中）。

### 任务管理

TaskManager 管理运行中的任务，支持创建任务、更新任务状态和跟踪任务进度。

## 高可用支持

### 模型故障转移

调用高可用领域服务获取可用模型，如果模型切换，则更新对话上下文中的模型和服务商信息，记录切换日志。

## 计费集成

### 使用量记录

记录 Token 使用量，构建计费上下文，调用计费服务记录使用数据。

### 余额检查

查询用户账户余额，如果余额不足则抛出异常提示用户充值。

## 跟踪与监控

### 执行跟踪

创建追踪上下文，记录会话 ID、Agent ID 和开始时间，记录模型调用和工具调用的详细信息。

## 数据持久化

### SQLAlchemy 集成

使用 SQLAlchemy 2.0 异步 ORM 进行数据访问，支持创建会话、列表查询、批量操作等常用功能。

### 批量操作

支持批量插入消息、批量删除消息等操作，提高数据访问效率。

## 接口定义

ConversationAppService 提供创建会话、删除会话、获取会话列表、流式聊天（包括 Agent 聊天和 RAG 聊天）和预览对话等接口。ChatSessionManager 提供注册会话、移除会话、中断会话和检查会话是否中断等接口。ConversationDomainService 提供获取会话消息、批量插入消息、保存消息、删除会话消息和更新消息 token 数量等接口。ContextDomainService 提供获取上下文、插入或更新上下文等接口。ChatCompletionHandler 提供同步完成聊天和流式完成聊天等接口。

## 数据模型

数据库表结构包括 sessions 表（会话表）、messages 表（消息表）和 contexts 表（上下文表）。sessions 表包含会话 ID、标题、用户 ID、Agent ID、描述、归档标志、元数据等字段。messages 表包含消息 ID、会话 ID、角色、内容、消息类型、创建时间、token 数量、服务商、模型、元数据、文件 URL 等字段。contexts 表包含上下文 ID、会话 ID、历史消息 ID 列表、总 token 数、最大容量、摘要等字段。

## 技术栈总结

**核心框架**:
- FastAPI 0.100+ - 异步 Web 框架
- Starlette - SSE 支持（sse-starlette）
- SQLAlchemy 2.0 - 异步 ORM
- Pydantic v2 - 数据验证和序列化
- Alembic - 数据库迁移

**异步处理**:
- asyncio - 异步运行时
- async/await - 异步语法
- aiohttp - 异步 HTTP 客户端

**缓存与存储**:
- Redis - 分布式缓存、会话共享
- MySQL 8.0 - 关系型数据库（通过 SQLAlchemy）

**通信协议**:
- HTTP/REST - API 接口
- SSE (Server-Sent Events) - 流式响应优先方案
- WebSocket - 双向通信备选方案

**工具库**:
- structlog - 结构化日志
- slowapi - 速率限制中间件
- tiktoken - Token 计算
- watchdog - 文件监听（热加载）
- prometheus-client - 指标采集

**部署与运维**:
- Docker - 容器化
- Prometheus + Grafana - 监控告警
- Elasticsearch - 日志存储检索
- Jaeger/Zipkin - 分布式追踪

## 性能优化

### 异步批量消息提交

**问题**: 每条消息单独保存导致数据库压力大，延迟高。

**解决方案**:
- 使用 `asyncio.gather` 批量保存消息
- 限制并发数：`asyncio.Semaphore(10)`
- 批处理大小：10 条消息一批
- 超时控制：单次批量 < 100ms

**实现示例**:
```python
async def save_messages_batch(messages: List[MessageEntity]):
    # 分组（每 10 条一批）
    batches = [messages[i:i+10] for i in range(0, len(messages), 10)]
    
    async with asyncio.Semaphore(10):  # 最多 10 个并发
        tasks = []
        for batch in batches:
            task = asyncio.create_task(message_repository.save_all(batch))
            tasks.append(task)
        
        await asyncio.gather(*tasks, return_exceptions=True)
```

### 会话缓存策略

**缓存架构**:
- **L1 缓存**: 内存 LRU Cache（最快，容量有限）
- **L2 缓存**: Redis 分布式缓存（共享，容量大）

**Key 设计**:
- `session:{id}:context` - 会话上下文
- `session:{id}:recent_messages` - 最近 10 条消息
- `session:{id}:metadata` - 会话元数据

**失效策略**:
- **TTL**: 30 分钟无活动自动过期
- **LRU**: 内存不足时淘汰最少使用的会话
- **主动失效**: 会话删除/更新时主动清除缓存

### Token 预算控制

**滑动窗口算法**:
- 历史消息占 70% Token 预算
- 当前对话预留 30%
- 动态调整窗口大小

**实现逻辑**:
```python
async def manage_token_budget(context: ContextEntity, new_message: Message):
    max_tokens = context.max_capacity  # 如 8000
    current_tokens = await token_service.count(context.messages + [new_message])
    
    if current_tokens > max_tokens:
        # 压缩早期消息为摘要
        while current_tokens > max_tokens * 0.7:
            await context.compress_earliest_messages()
            current_tokens = await token_service.count(context.messages)
        
        # 仍超出则截断
        if current_tokens > max_tokens:
            context.messages = context.messages[-int(max_tokens * 0.3):]
```

### 连接池配置

**数据库连接池**:
- HikariCP（SQLAlchemy 默认）
- 连接数：`CPU 核数 * 2 + 1`
- 最大空闲时间：300s
- 健康检查：每 60s

**HTTP 客户端连接池**:
- aiohttp ClientSession
- 连接数限制：100
- SSL 验证：启用

### 限流与背压

**慢速 API 限流**:
- 使用 slowapi 中间件
- 单用户每秒 ≤ 5 个会话创建
- 单用户每分钟 ≤ 60 次工具调用

**背压控制**:
- SSE 推送使用 `asyncio.Queue(maxsize=100)`
- 队列满时阻塞生产者（LLM 输出）
- 防止内存溢出

## 安全设计

### 多租户数据隔离

**实现方式**: SQLAlchemy 查询过滤（行级隔离）

**查询拦截器**:
```python
from sqlalchemy import event

@event.listens_for(Session, "do_orm_execute")
def filter_by_tenant(stmt, state, binding, context):
    # 强制添加 user_id 和 tenant_id 过滤
    if hasattr(context.params, 'user_id'):
        stmt = stmt.filter(Message.user_id == context.params.user_id)
    if hasattr(context.params, 'tenant_id'):
        stmt = stmt.filter(Message.tenant_id == context.params.tenant_id)
```

**访问控制**:
- JWT Token 验证用户身份
- 每次查询自动注入过滤条件
- 防止越权访问

### 输入验证

**Pydantic Validator**:
```python
from pydantic import validator

class ChatRequest(BaseModel):
    content: str
    
    @validator('content')
    def validate_content(cls, v):
        # 长度限制
        token_count = tiktoken.count(v)
        if token_count > 4000:
            raise ValueError('消息长度不能超过 4000 tokens')
        
        # Prompt 注入检测
        if injection_detector.detect(v) > 80:
            raise ValueError('检测到恶意输入')
        
        # 敏感词过滤
        return sensitive_word_filter.replace(v)
```

### 工具调用沙箱

**安全措施**:
1. **白名单校验**: 仅允许调用已注册的工具
2. **权限验证**: 检查用户是否有工具访问权限
3. **参数验证**: Pydantic 模型校验工具参数
4. **沙箱执行**: 高风险工具在独立容器执行
5. **结果过滤**: 移除敏感信息（如 API Key、文件路径）

### 审计日志

**结构化日志** (使用 structlog):
```python
import structlog

logger = structlog.get_logger()

# 记录关键操作
logger.info(
    "session_created",
    session_id=session_id,
    user_id=user_id,
    agent_id=agent_id,
    timestamp=datetime.utcnow().isoformat()
)

# 敏感信息脱敏
logger.info(
    "tool_called",
    tool_name="weather_query",
    arguments={"city": "***"},  # 脱敏处理
    result_length=len(result)
)
```

**日志保留**: 90 天

### 会话安全

**防 CSRF**:
- 同源策略验证
- CSRF Token 双重验证

**防会话劫持**:
- session_id 使用加密 UUID（32 位以上随机字符）
- 定期刷新 session_id
- IP 绑定检测（可选）

**连接鉴权**:
- SSE/WebSocket 连接建立时验证 JWT Token
- 未授权连接立即拒绝

## 扩展设计

### 自定义处理器扩展

**方式**: 继承 AbstractMessageHandler 抽象基类

**步骤**:
1. 创建新类继承 AbstractMessageHandler
2. 实现 `do_handle(chat_context)` 抽象方法
3. 在工厂注册表中注册新处理器

**示例**:
```python
class CustomMessageHandler(AbstractMessageHandler):
    async def do_handle(self, chat_context: ChatContext) -> AsyncGenerator[Event, None]:
        # 自定义处理逻辑
        yield Event("custom", {"message": "Custom handling..."})

# 注册到工厂
MessageHandlerFactory.register("custom", CustomMessageHandler)
```

**热加载机制**:
- 监听 `plugins/` 目录变化
- 使用 `watchdog` 库检测新文件
- 动态导入并注册处理器
- 无需重启服务

### 自定义消息类型

**方式**: 扩展 MessageType 枚举

```python
class MessageType(str, Enum):
    TEXT = "text"
    TOOL_CALL = "tool_call"
    # ... 现有类型
    CUSTOM_TYPE = "custom_type"  # 新增
```

**处理器绑定**:
- 为新消息类型创建专用处理器
- 在 MessageHandler 中添加分支逻辑

### 自定义工具扩展

**方式**: 实现 Tool 基类

```python
class CustomTool(Tool):
    name = "my_custom_tool"
    description = "自定义工具描述"
    
    async def call(self, **kwargs) -> str:
        # 实现工具逻辑
        return "result"

# 注册到工具管理器
AgentToolManager.register_tool(CustomTool())
```

**插件发现机制**:
- 基于 Python entry_points
- 在 setup.py 中声明工具插件
- 启动时自动扫描并注册

## 监控与日志

### 日志级别

- **DEBUG**: 调试信息（仅开发环境启用）
- **INFO**: 正常操作日志（会话创建、消息发送、工具调用等）
- **WARNING**: 警告日志（Token 接近上限、重试等）
- **ERROR**: 错误日志（异常、失败等）

### 监控指标

**实时指标** (通过 Prometheus 采集):
- 会话创建速率（sessions/minute）
- 消息处理速率（messages/second）
- 平均响应时间（P50/P90/P95）
- Token 消耗统计（tokens/minute）
- 错误率（errors/total_requests）
- SSE 连接数（active_connections）
- 队列长度（asyncio.Queue size）

**告警规则**:
- 首 Token延迟 > 1s 持续 5 分钟 → 告警
- 错误率 > 1% 持续 1 分钟 → 告警
- SSE 连接数 < 100（预期 1000+）→ 告警
- 内存使用 > 80% → 告警

### 审计日志

**记录内容**:
- 用户操作审计：会话创建、删除、更新
- 模型调用审计：服务商、模型、token 用量
- 工具使用审计：工具名称、参数、执行结果
- 计费记录：Token 消耗、费用计算

**存储策略**:
- 结构化日志 JSON 格式
- 存储到 Elasticsearch（便于检索）
- 保留 90 天

### 分布式追踪

**集成 016-execution-trace**:
- 每个请求生成 trace_id
- 跨服务传递 trace context
- 记录 span 信息（开始时间、结束时间、标签）
- 可视化调用链路（使用 Jaeger/Zipkin）

### 健康检查

**端点**: `/health`

**检查项**:
- 数据库连接状态
- Redis 连接状态
- LLM 服务可用性
- 内存使用情况
- 磁盘空间

**返回格式**:
```json
{
  "status": "healthy",
  "checks": {
    "database": "up",
    "redis": "up",
    "llm": "up",
    "memory_usage": 0.65,
    "disk_usage": 0.45
  }
}
```

## 代码文件清单

### 处理器层
- `app/application/conversation/handlers/abstract_message_handler.py` - 抽象消息处理器基类
- `app/application/conversation/handlers/chat_message_handler.py` - 标准对话处理器
- `app/application/conversation/handlers/agent_message_handler.py` - Agent 智能体处理器
- `app/application/conversation/handlers/rag_message_handler.py` - RAG 检索增强处理器
- `app/application/conversation/handlers/preview_message_handler.py` - 预览模式处理器
- `app/application/conversation/handlers/message_handler_factory.py` - 消息处理器工厂

### API 层
- `app/api/v1/endpoints/sse_endpoints.py` - SSE 流式响应端点
- `app/api/v1/websocket/agent_websocket.py` - Agent WebSocket 路由

### 安全层
- `app/domain/conversation/security/sensitive_word_filter.py` - 敏感词过滤器
- `app/domain/conversation/security/prompt_injection_detector.py` - Prompt 注入检测器

### 基础设施层
- `app/infrastructure/websocket/connection_manager.py` - WebSocket 连接管理器

### 测试层
- `app/tests/unit/application/test_message_handlers.py` - 消息处理器单元测试