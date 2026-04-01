# 对话管理能力规范

## 概述

对话管理模块（Conversation Management）是 AgentX 平台的核心能力，负责管理和处理用户与智能体之间的所有交互。该模块提供了多种聊天模式、灵活的会话管理机制、强大的消息处理能力，支持从简单的问答到复杂的工具调用工作流等多种对话场景。

### 模块职责边界

- **013-conversation**: 对话流程控制、聊天模式路由、消息接收/响应
- **014-agent-workflow**: 复杂任务编排引擎（任务拆分、依赖管理、并行调度）
- **018-task-management**: 任务/工作流持久化、状态存储、执行追踪

**注意**：当用户请求识别为复杂任务时，本模块将委托给 014-agent-workflow 模块进行编排处理。

## 核心能力

### 1. 多种聊天模式

#### 1.1 标准对话模式
- 基于大语言模型的基础问答能力
- 支持单轮和多轮对话
- 自动维护会话上下文
- 内置记忆提取和注入机制

**实现文件**: `app/application/conversation/handlers/chat_message_handler.py`

#### 1.2 Agent 智能体模式
- 支持工具调用的复杂任务处理
- **简单任务**：直接在本模块内处理（单步工具调用）
- **复杂任务**：委托给 014-agent-workflow 模块（多步骤、有依赖关系）
- 内置工具和外部工具集成
- 事件驱动的状态转换
- 用户可用工具管理

**实现文件**: `app/application/conversation/handlers/agent_message_handler.py`

**与 014 的协作**：
- 013 负责接收用户消息并判断是否为复杂任务
- 复杂任务委托给 014 进行编排（任务拆分、并行执行）
- 014 通过事件总线通知 013 任务进展
- 最终结果由 013 返回给用户

#### 1.3 RAG 检索增强模式
- 基于知识库的问答
- 智能文档检索与重排序
- 多阶段处理流程（检索、思考、回答）
- 支持多数据集和单文件检索
- 可配置的检索参数（最大结果数、相似度阈值）

**实现文件**: `app/application/conversation/handlers/rag_message_handler.py`

#### 1.4 预览模式
- 支持智能体预览测试
- 快速验证智能体配置
- 流式响应展示效果
- 临时会话（不持久化）
- 跳过计费和历史记录

**实现文件**: `app/application/conversation/handlers/preview_message_handler.py`

### 2. 会话管理

#### 2.1 会话生命周期
- 会话创建与初始化
- 会话消息持久化存储
- 会话归档与删除
- 会话元数据管理

#### 2.2 上下文管理
- 自动维护对话历史
- Token 消耗追踪
- 消息摘要生成
- 上下文溢出处理

#### 2.3 会话控制
- 实时会话中断
- 超时自动清理
- 并发会话支持

### 3. 消息处理

#### 3.1 消息类型
- 文本消息（TEXT）
- 工具调用消息（TOOL_CALL）
- 任务执行消息（TASK_EXEC）
- 任务状态消息（进行中、完成、拆分结束）
- RAG 处理消息（检索开始/进行中/结束、思考开始/进行中/结束、回答开始/进行中/结束）

#### 3.2 消息角色
- 用户（USER）
- 系统（SYSTEM）
- 助手/智能体（ASSISTANT）
- 摘要（SUMMARY）- 仅存在于历史消息表中

#### 3.3 消息元数据
- Token 统计（总数、正文数）
- 服务提供商和模型信息
- 创建时间戳
- 关联文件 URL
- 自定义元数据

### 4. 流式响应

#### 4.1 实时响应流
- SSE（Server-Sent Events）协议支持
- 逐 Token 输出
- 低延迟响应

**实现文件**: `app/api/v1/endpoints/sse_endpoints.py`

**API 端点**:
- `POST /api/v1/sessions/{sessionId}/chat/stream` - 标准流式聊天
- `POST /api/v1/agents/{agentId}/chat/stream` - Agent 流式聊天
- `POST /api/v1/rag/{ragId}/chat/stream` - RAG 流式聊天

#### 4.2 流式会话管理
- 会话注册与追踪
- 中断信号传递
- 超时和错误处理

### 5. 记忆管理

#### 5.1 记忆提取
- 从对话历史中自动提取关键信息
- 基于语义相似度的记忆检索
- 支持用户指令记忆

#### 5.2 记忆注入
- 自动将相关记忆注入到系统提示中
- Top-K 检索策略
- 可配置的记忆注入逻辑

### 6. 跟踪与监控

#### 6.1 执行跟踪
- Agent 执行过程追踪
- 模型调用信息记录
- 工具调用详情记录
- 执行阶段标记

#### 6.2 统计分析
- Token 使用统计
- 模型调用统计
- 工具使用统计
- 会话统计

### 7. 多模态支持

#### 7.1 文件上传
- 支持图片等多模态文件
- 文件 URL 管理
- 文件内容处理

### 8. 高可用支持

#### 8.1 模型故障转移
- 自动模型切换
- 服务商高可用策略
- 故障恢复机制

### 9. 计费与配额

#### 9.1 用量追踪
- Token 使用量精确统计
- 按用户和模型分类
- 实时余额检查
- 用量记录持久化

## 使用场景

### 场景一：通用问答
用户与智能体进行多轮对话，智能体基于大语言模型的通用知识回答问题，自动维护对话上下文。

**能力需求：**
- 标准对话模式
- 历史消息管理
- 上下文维护

**API 调用**:
```bash
POST /api/v1/sessions/{sessionId}/chat/stream
Content-Type: application/json

{
  "content": "你好，介绍一下你自己",
  "stream": true
}
```

### 场景二：任务执行
用户向智能体提出复杂任务（如"帮我查询今天的天气并制定出行计划"），智能体自动拆分任务、调用相应工具执行，最后汇总结果。

**能力需求：**
- Agent 智能体模式
- 工具调用
- 任务拆分与执行
- 工作流管理
- 事件驱动状态转换

**API 调用**:
```bash
POST /api/v1/agents/{agentId}/chat/stream
Content-Type: application/json

{
  "content": "帮我查询今天的天气并制定出行计划",
  "stream": true
}
```

### 场景三：知识库问答
用户询问关于特定文档的问题，系统从知识库中检索相关文档片段，基于检索结果生成精准答案。

**能力需求：**
- RAG 检索增强模式
- 文档检索与重排序
- 检索流程管理（检索、思考、回答）
- 检索结果展示

**API 调用**:
```bash
POST /api/v1/rag/{ragId}/chat/stream
Content-Type: application/json

{
  "content": "公司的年假政策是什么？",
  "stream": true
}
```

### 场景四：实时对话反馈
用户与智能体进行实时对话，智能体以流式方式快速输出响应内容，提供即时反馈。

**能力需求：**
- 流式响应
- SSE 通信
- 实时会话管理
- 中断控制

### 场景五：长期记忆对话
用户与智能体进行长期对话，智能体记住用户偏好和历史信息，在后续对话中自动应用。

**能力需求：**
- 记忆提取
- 记忆注入
- 语义检索
- 长期上下文管理

### 场景六：多模态交互
用户上传图片或文件，智能体基于多模态内容进行理解和响应。

**能力需求：**
- 文件上传处理
- 多模态内容理解
- 文件 URL 管理

### 场景七：智能体预览测试
开发者在发布智能体前，通过预览模式测试智能体的响应效果。

**能力需求：**
- 预览模式
- 流式响应
- 快速验证

**API 调用**:
```bash
POST /api/v1/agents/{agentId}/preview
Content-Type: application/json

{
  "content": "测试智能体响应",
  "stream": true
}
```

### 场景八：会话中断
用户在智能体执行过程中决定中断对话，系统立即停止当前处理并返回结果。

**能力需求：**
- 会话中断
- 实时控制
- 资源清理

## 功能特性

### 1. 灵活的处理器架构
- 基于抽象消息处理器的扩展机制
- 工厂模式自动选择处理器
- 支持自定义处理器扩展

**实现文件**: `app/application/conversation/handlers/message_handler_factory.py`

### 2. 强大的上下文管理
- ChatContext 统一管理上下文信息
- 自动加载用户、Agent、模型配置
- 支持追踪上下文和公开访问模式

### 3. 完善的领域模型
- SessionEntity - 会话实体
- MessageEntity - 消息实体
- ContextEntity - 上下文实体
- 基于 SQLAlchemy 的数据持久化

### 4. 丰富的 DTO 定义
- ChatRequest/Response - 基础请求/响应
- StreamChatRequest - 流式请求
- RagChatRequest - RAG 专用请求
- AgentChatResponse - Agent 响应

### 5. 智能工具管理
- Built-in Tool Registry - 内置工具注册
- User Tool Management - 用户工具管理
- Tool Provider - 工具提供者机制
- Agent Tool Manager - Agent 工具管理器

### 6. 工作流引擎
- 事件驱动的任务处理
- 状态机管理
- 分析器、任务执行器、汇总处理器
- 任务拆分与执行协调

### 7. 记忆服务集成
- Memory Domain Service - 记忆领域服务
- Memory Extractor - 记忆提取器
- 自动记忆注入系统提示

### 8. RAG 深度集成
- RagChatContext - RAG 专用上下文
- RagRetrievalResult - 检索结果封装
- 与 RAG 搜索服务无缝集成

### 9. 批量操作支持
- 批量消息插入
- 批量会话删除
- 批量上下文更新

### 10. 异常处理机制
- 业务异常统一处理
- 余额不足异常
- 会话不存在异常
- 超时和错误恢复

## 技术约束

### 技术栈要求
- **核心框架**: FastAPI（异步 Web 框架）、Starlette（SSE 支持）
- **通信协议**: 
  - SSE（Server-Sent Events）优先 - 使用 sse-starlette 库实现流式响应
  - WebSocket 备选 - 使用 fastapi-websockets 实现双向通信
  - HTTP/REST - 标准 API 接口
- **异步处理**: asyncio + async/await 语法
- **数据验证**: Pydantic v2（模型验证和序列化）
- **ORM 框架**: SQLAlchemy 2.0（异步 ORM）
- **缓存**: Redis（会话缓存、分布式锁）
- **限流中间件**: slowapi（速率限制）

### 模式切换规则
聊天模式由以下优先级自动选择：
1. **预览模式** (最高优先级): 当请求包含 `preview=true` 参数时
2. **RAG 模式**: 当请求包含 `rag_id` 且智能体配置了 RAG 能力时
3. **Agent 模式**: 当智能体配置了工具且 `chat_mode="agent"` 时
4. **标准模式** (默认): 其他情况

**实现文件**: `app/application/conversation/handlers/message_handler_factory.py`

模式处理器注册表采用工厂模式 + 字典注册，支持动态扩展。

### 性能指标

#### 响应延迟（P95）
- **首 Token延迟**:
  - 标准对话：< 500ms
  - Agent 模式：< 800ms（包括工具调用准备）
  - RAG 模式：< 1s（包括检索时间）
  - 预览模式：< 600ms
- **流式响应chunk间隔**: 100-200ms（逐 Token 输出）
- **SSE 推送延迟**: < 100ms
- **WebSocket 消息处理**: < 50ms

#### 并发能力
- **最大并发对话数**: 单实例 1000+ 活跃会话
- **SSE 连接数**: 单实例 5000+ 并发连接
- **消息吞吐量**: 1000+ 消息/秒
- **水平扩展**: 支持集群部署，线性扩展

#### 持久化性能
- **消息持久化延迟**: < 50ms（异步批量提交）
- **会话创建延迟**: < 30ms
- **历史消息查询**: < 200ms（100 条以内）

#### 连接管理
- **WebSocket 心跳间隔**: 30s
- **SSE 超时检测**: 90s 无活动自动断开
- **断线重连**: 支持 last-event-id 恢复（最多重试 3 次）

### 可用性要求
- **系统可用性**: > 99.5%
- **故障恢复时间**: < 30s
- **无单点故障**: 支持多实例部署 + Redis 哨兵
- **降级策略**: Redis 不可用时降级到内存模式

### 安全性要求

#### 多租户数据隔离
- **实现方式**: SQLAlchemy 查询过滤（行级隔离）
- **过滤条件**: 所有查询强制添加 `user_id` 和 `tenant_id` 过滤
- **会话访问控制**: 用户只能访问自己的会话（基于 JWT 身份验证）
- **审计日志**: 记录所有会话操作（保留 90 天）

#### 输入安全
- **消息长度限制**: 用户输入 ≤ 4000 tokens
- **防 Prompt 注入**: 正则检测恶意注入模式（如忽略指令、角色扮演攻击）
- **敏感词过滤**: 可配置的敏感词库（支持正则匹配）
- **文件上传限制**: 单文件 ≤ 10MB，类型白名单

**实现文件**: 
- `app/domain/conversation/security/prompt_injection_detector.py`
- `app/domain/conversation/security/sensitive_word_filter.py`

#### 工具调用安全
- **白名单校验**: 仅允许调用已注册的工具
- **结果过滤**: 工具返回结果必须通过安全过滤
- **权限验证**: 每次调用验证用户工具访问权限
- **沙箱执行**: 高风险工具在隔离容器执行
- **调用频率限制**: 单用户每分钟 ≤ 60 次工具调用

#### 连接安全
- **JWT 认证**: SSE/WebSocket 连接需验证 Token
- **防 CSRF**: 同源策略 + CSRF Token 双重验证
- **防会话劫持**: session_id 使用加密 UUID（32 位以上）
- **速率限制**: 单用户每秒 ≤ 5 个会话创建

### 可扩展性设计

#### 消息处理器扩展
- **注册表机制**: 基于工厂模式 + 字典注册
- **插件接口**: 继承 AbstractMessageHandler 抽象基类
- **发现机制**: 基于 Python entry_points 自动发现插件
- **热加载**: 监听 plugins 目录变化，动态加载新处理器
- **优先级**: 支持设置处理器优先级（数字越小优先级越高）

**实现文件**: `app/application/conversation/handlers/abstract_message_handler.py`

#### 自定义消息类型
- **扩展方式**: 继承 MessageType 枚举
- **处理器绑定**: 为新消息类型注册专用处理器
- **向后兼容**: 旧版本自动忽略不支持的消息类型

#### 自定义工具扩展
- **实现接口**: 实现 Tool 基类的 call 方法
- **注册机制**: 使用装饰器或配置文件注册
- **元数据**: 提供工具描述、参数 schema、使用示例

### 范围边界

#### 与 011-session-context 的边界
**011 负责（存储层）**:
- 会话数据结构定义（Session/Message/Context Entity）
- 会话 CRUD 操作（创建、查询、更新、删除）
- 上下文窗口管理和 Token 计算策略
- 历史消息持久化和分页查询
- SSE 连接管理和心跳机制

**013 负责（交互层）**:
- 聊天模式编排和处理器调度
- 流式响应逻辑（SSE/WebSocket 事件流）
- 工具调用链路集成和执行追踪
- Agent 工作流集成（调用 014 的能力）
- RAG 检索增强集成
- 记忆提取和注入逻辑
- 计费集成（Token 统计上报）

**依赖关系**: 013 依赖 011 的存储能力，013 是 011 的上层编排

#### 与 014-agent-workflow 的边界
**014 负责（工作流引擎）**:
- 任务拆分算法（LLM 驱动的任务分解）
- 工作流状态机（INIT → ANALYZING → SPLITTING → EXECUTING → SUMMARIZING → COMPLETED）
- 任务调度和依赖管理
- 并行任务执行协调
- 工作流事件总线

**013 负责（对话集成）**:
- 将 Agent 工作流集成到对话流程
- 接收 014 的事件并转换为对话消息
- 向用户展示任务执行进度
- 汇总工作流结果并返回
- 中断信号传递给工作流

**依赖关系**: 013 调用 014 的工作流能力，014 是独立的工作流引擎

#### 与 012-memory 的边界
**012 负责（长期记忆）**:
- 记忆的提取、存储和检索
- 语义相似度匹配
- 记忆向量数据库管理

**013 负责（短期上下文）**:
- 从当前对话中提取关键信息（调用 012 的接口）
- 将相关记忆注入到系统提示
- 会话结束后异步同步重要信息到 012

#### 与 016-execution-trace 的边界
**016 负责（追踪基础设施）**:
- 追踪上下文管理
- 追踪数据存储
- 追踪查询 API

**013 负责（对话追踪）**:
- 创建对话追踪上下文
- 记录模型调用、工具调用的详细信息
- 标记执行阶段（分析、执行、汇总）

## API 端点列表

### SSE 流式响应端点

| 方法 | 端点 | 描述 | 实现文件 |
|------|------|------|----------|
| POST | `/api/v1/sessions/{sessionId}/chat/stream` | 标准流式聊天 | `app/api/v1/endpoints/sse_endpoints.py` |
| POST | `/api/v1/agents/{agentId}/chat/stream` | Agent 流式聊天 | `app/api/v1/endpoints/sse_endpoints.py` |
| POST | `/api/v1/rag/{ragId}/chat/stream` | RAG 流式聊天 | `app/api/v1/endpoints/sse_endpoints.py` |

### WebSocket 端点

| 方法 | 端点 | 描述 | 实现文件 |
|------|------|------|----------|
| WebSocket | `/ws/agents/{agentId}/sessions` | Agent WebSocket 连接 | `app/api/v1/websocket/agent_websocket.py` |

### 典型场景示例

#### 示例 1：标准对话模式请求/响应
**请求**:
```json
POST /api/v1/sessions/{sessionId}/chat
{
  "content": "你好，介绍一下你自己",
  "stream": false
}
```

**响应**:
```json
{
  "session_id": "sess_abc123",
  "message_id": "msg_xyz789",
  "role": "assistant",
  "content": "你好！我是 AgentX 智能助手...",
  "token_usage": {
    "prompt_tokens": 50,
    "completion_tokens": 100,
    "total_tokens": 150
  },
  "finish_reason": "stop"
}
```

#### 示例 2：Agent 模式流式响应（SSE 事件流）
**SSE 事件序列**:
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

event: token
data: {"content":"北"}

event: token
data: {"content":"京"}

event: token
data: {"content":"天"}

event: token
data: {"content":"气"}

event: end
data: {"finish_reason":"stop","token_usage":{"total_tokens":200}}
```

#### 示例 3：RAG 模式请求/响应
**请求**:
```json
POST /api/v1/rag/{ragId}/chat
{
  "content": "公司的年假政策是什么？",
  "stream": true,
  "retrieval_params": {
    "top_k": 3,
    "similarity_threshold": 0.7
  }
}
```

**SSE 事件流**:
```
event: retrieval_start
data: {"query":"年假政策","datasets":["员工手册"]}

event: retrieval_progress
data: {"stage":"searching","progress":0.5}

event: retrieval_end
data: {"documents":[{"content":"...","score":0.92}]}

event: thinking_start
data: {}

event: thinking_progress
data: {"content":"正在分析文档..."}

event: thinking_end
data: {}

event: answer_start
data: {}

event: token
data: {"content":"根"}
event: token
data: {"content":"据"}
// ... 更多 token
event: answer_end
data: {"token_usage":{"total_tokens":350}}
```

#### 示例 4：工具调用安全校验
**校验流程**:
1. 解析 LLM 返回的工具调用请求
2. 检查工具是否在已注册工具列表中
3. 验证用户是否有该工具的访问权限
4. 检查工具调用频率是否超限
5. 执行工具调用（沙箱环境）
6. 过滤工具返回结果（移除敏感信息）
7. 将安全的结果返回给 LLM

## 依赖能力

对话管理模块依赖于以下 AgentX 平台能力：

1. **Agent 管理** - 提供智能体配置和元数据
2. **LLM 管理** - 提供大语言模型服务
3. **工具管理** - 提供工具调用能力
4. **RAG 管理** - 提供知识库检索能力
5. **记忆管理** - 提供长期记忆存储
6. **用户管理** - 提供用户和权限管理
7. **账单管理** - 提供计费和配额管理
8. **容器管理** - 提供应用执行环境
9. **高可用** - 提供故障转移能力
10. **文件存储** - 提供文件上传和管理

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