## 实施

### 一、数据模型层

- [ ] 1.1 创建 Session 实体和数据模型
     【目标对象】`app/domain/conversation/models/session.py`
     【修改目的】定义会话相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/conversation/model/SessionEntity.java`
     【修改内容】
        - 创建 Session 模型（sessions 表）
        - 定义字段：id（UUID）、title、user_id、agent_id、description、is_archived、metadata
        - 创建时间戳字段：created_at、updated_at
        - 实现 Pydantic Schema（SessionCreateSchema、SessionUpdateSchema、SessionResponseSchema）
        - 定义索引：user_id、agent_id、created_at

- [ ] 1.2 创建 Message 实体和数据模型
     【目标对象】`app/domain/conversation/models/message.py`
     【修改目的】定义消息相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/conversation/model/MessageEntity.java`
     【修改内容】
        - 创建 Message 模型（messages 表）
        - 定义字段：id（UUID）、session_id、role、content、message_type、token_count、body_token_count
        - 创建枚举类型：Role（user、assistant、system）、MessageType（TEXT、TOOL_CALL、TOOL_RESPONSE 等）
        - 创建时间戳字段：created_at、updated_at
        - 实现 Pydantic Schema（MessageCreateSchema、MessageUpdateSchema、MessageResponseSchema）
        - 定义索引：session_id、created_at、role

- [ ] 1.3 创建 Context 实体和数据模型
     【目标对象】`app/domain/conversation/models/context.py`
     【修改目的】定义上下文相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型和 JSON 列
     【相关依赖】`AgentX/domain/conversation/model/ContextEntity.java`
     【修改内容】
        - 创建 Context 模型（context 表）
        - 定义字段：id（UUID）、session_id、active_messages（JSON 列表）、summary
        - 实现 JSON 字段存储 active_messages 列表
        - 创建时间戳字段：created_at、updated_at
        - 实现 Pydantic Schema（ContextCreateSchema、ContextUpdateSchema、ContextResponseSchema）
        - 定义索引：session_id

- [ ] 1.4 实现常数定义
     【目标对象】`app/domain/conversation/constants.py`
     【修改目的】定义消息类型和角色枚举
     【修改方式】使用 Python Enum
     【相关依赖】`AgentX/domain/conversation/constant/MessageType.java`, `AgentX/domain/conversation/constant/Role.java`
     【修改内容】
        - 定义 MessageType 枚举：TEXT、TOOL_CALL、TOOL_RESPONSE、SYSTEM_PROMPT
        - 定义 Role 枚举：USER、ASSISTANT、SYSTEM
        - 定义消息处理状态常量

- [ ] 1.5 实现 MessageFactory
     【目标对象】`app/domain/conversation/factory/message_factory.py`
     【修改目的】根据不同场景创建消息对象
     【修改方式】实现工厂模式
     【相关依赖】Message 模型
     【修改内容】
        - 实现 create_user_message 方法
        - 实现 create_assistant_message 方法
        - 实现 create_tool_call_message 方法
        - 实现 create_tool_response_message 方法

### 二、仓储层

- [ ] 2.1 实现 SessionRepository
     【目标对象】`app/domain/conversation/repositories/session_repository.py`
     【修改目的】定义会话数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】Session 模型、SQLAlchemy
     【修改内容】
        - 定义 SessionRepository 接口
        - 实现 SQLAlchemy SessionRepository
        - 实现基础 CRUD 操作
        - 实现复杂查询：按用户查询、按 Agent 查询、查询归档会话
        - 实现分页查询

- [ ] 2.2 实现 MessageRepository
     【目标对象】`app/domain/conversation/repositories/message_repository.py`
     【修改目的】定义消息数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】Message 模型、SQLAlchemy
     【修改内容】
        - 定义 MessageRepository 接口
        - 实现 SQLAlchemy MessageRepository
        - 实现基础 CRUD 操作
        - 实现复杂查询：按会话查询、按角色查询、按类型查询
        - 实现分页查询和排序
        - 实现批量查询

- [ ] 2.3 实现 ContextRepository
     【目标对象】`app/domain/conversation/repositories/context_repository.py`
     【修改目的】定义上下文数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】Context 模型、SQLAlchemy
     【修改内容】
        - 定义 ContextRepository 接口
        - 实现 SQLAlchemy ContextRepository
        - 实现基础 CRUD 操作
        - 实现按会话查询上下文
        - 实现更新活跃消息列表
        - 实现更新摘要

### 三、领域服务层

- [ ] 3.1 实现 SessionDomainService
     【目标对象】`app/domain/conversation/services/session_domain_service.py`
     【修改目的】封装会话相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】SessionRepository
     【修改内容】
        - 实现创建会话逻辑
        - 实现更新会话标题逻辑
        - 实现归档会话逻辑
        - 实现恢复会话逻辑
        - 实现会话验证逻辑

- [ ] 3.2 实现 MessageDomainService
     【目标对象】`app/domain/conversation/services/message_domain_service.py`
     【修改目的】封装消息相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】MessageRepository
     【修改内容】
        - 实现创建消息逻辑
        - 实现更新消息逻辑
        - 实现删除消息逻辑
        - 实现 Token 计数逻辑
        - 实现消息验证逻辑

- [ ] 3.3 实现 ContextDomainService
     【目标对象】`app/domain/conversation/services/context_domain_service.py`
     【修改目的】封装上下文管理的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ContextRepository、MessageRepository
     【修改内容】
        - 实现创建上下文逻辑
        - 实现添加消息到上下文逻辑
        - 实现从上下文移除消息逻辑
        - 实现上下文压缩逻辑（合并历史消息为摘要）
        - 实现上下文窗口管理逻辑
        - 实现 Token 数量统计

- [ ] 3.4 实现 ContextProcessor
     【目标对象】`app/domain/conversation/services/context_processor.py`
     【修改目的】处理上下文生成和提取
     【修改方式】实现上下文处理器
     【相关依赖】ContextDomainService、MessageRepository
     【修改内容】
        - 实现构建对话上下文方法
        - 实现构建 RAG 上下文方法
        - 实现历史消息提取逻辑
        - 实现关键信息提取逻辑

- [ ] 3.5 实现 ChatCompletionHandler
     【目标对象】`app/domain/conversation/services/chat_completion_handler.py`
     【修改目的】封装 LLM 调用逻辑
     【修改方式】实现聊天完成处理器
     【相关依赖】LLMDomainService、ContextProcessor
     【修改内容】
        - 实现 sync_chat 方法（同步聊天）
        - 实现 stream_chat 方法（流式聊天）
        - 支持工具调用回调
        - 支持流式 Token 输出
        - 实现 Token 计数统计

### 四、应用服务层

- [ ] 4.1 实现 ConversationAppService
     【目标对象】`app/application/conversation/services/conversation_app_service.py`
     【修改目的】编排对话相关的用例
     【修改方式】实现应用服务
     【相关依赖】SessionDomainService、MessageDomainService、ContextDomainService
     【修改内容】
        - 实现创建会话
        - 实现获取会话列表
        - 实现获取会话详情
        - 实现更新会话
        - 实现删除会话
        - 实现归档会话
        - 实现恢复会话

- [ ] 4.2 实现聊天功能
     【目标对象】`app/application/conversation/services/chat_service.py`
     【修改目的】处理聊天请求
     【修改方式】实现聊天服务
     【相关依赖】ConversationAppService、ChatCompletionHandler
     【修改内容】
        - 实现发送消息
        - 实现获取消息历史
        - 实现删除消息
        - 实现创建会话并发送消息
        - 实现流式聊天响应

- [ ] 4.3 实现 ChatSessionManager
     【目标对象】`app/application/conversation/services/chat_session_manager.py`
     【修改目的】管理聊天会话
     【修改方式】实现会话管理器
     【相关依赖】ConversationAppService、LRU Cache
     【修改内容】
        - 实现会话缓存机制
        - 实现会话上下文缓存
        - 实现会话超时清理
        - 实现并发会话管理

- [ ] 4.4 实现 AgentMessageHandler
     【目标对象】`app/application/conversation/handlers/agent_message_handler.py`
     【修改目的】处理 Agent 对话
     【修改方式】实现消息处理器
     【相关依赖】ChatCompletionHandler、ToolManager、AgentDomainService
     【修改内容】
        - 实现 Agent 消息处理逻辑
        - 实现工具调用逻辑
        - 实现任务执行逻辑
        - 实现任务拆分逻辑
        - 实现 Agent 工作流状态管理
        - 实现信息需求分析
        - 实现摘要生成

- [ ] 4.5 实现 RagMessageHandler
     【目标对象】`app/application/conversation/handlers/rag_message_handler.py`
     【修改目的】处理 RAG 对话
     【修改方式】实现消息处理器
     【相关依赖】RAGSearchAppService、ChatCompletionHandler
     【修改内容】
        - 实现 RAG 消息处理逻辑
        - 实现文档检索逻辑
        - 实现检索结果注入逻辑
        - 实现 RAG 上下文管理

- [ ] 4.6 实现 PreviewMessageHandler
     【目标对象】`app/application/conversation/handlers/preview_message_handler.py`
     【修改目的】处理 Agent 预览对话
     【修改方式】实现消息处理器
     【相关依赖】AgentMessageHandler
     【修改内容】
        - 实现 Agent 预览消息处理
        - 实现临时会话创建
        - 实现预览结果返回

- [ ] 4.7 实现消息处理器工厂
     【目标对象】`app/application/conversation/handlers/message_handler_factory.py`
     【修改目的】根据场景创建消息处理器
     【修改方式】实现工厂模式
     【相关依赖】各种 MessageHandler
     【修改内容】
        - 实现 get_handler 方法
        - 实现 create_agent_handler
        - 实现 create_rag_handler
        - 实现 create_preview_handler

- [ ] 4.8 实现 AgentSessionAppService
     【目标对象】`app/application/conversation/services/agent_session_app_service.py`
     【修改目的】管理 Agent 会话
     【修改方式】实现应用服务
     【相关依赖】ConversationAppService、AgentMessageHandler
     【修改内容】
        - 实现创建 Agent 会话
        - 实现发送 Agent 消息（同步）
        - 实现发送 Agent 消息（流式）
        - 实现获取 Agent 会话列表

- [ ] 4.9 实现 RagSessionManager
     【目标对象】`app/application/conversation/services/rag_session_manager.py`
     【修改目的】管理 RAG 会话
     【修改方式】实现会话管理器
     【相关依赖】RAGSearchAppService、RagMessageHandler
     【修改内容】
        - 实现创建 RAG 会话
        - 实现发送 RAG 消息（同步）
        - 实现发送 RAG 消息（流式）
        - 实现检索结果返回

### 五、WebSocket 和流式响应层

- [ ] 5.1 实现 WebSocket 连接管理器
     【目标对象】`app/infrastructure/websocket/connection_manager.py`
     【修改目的】管理 WebSocket 连接
     【修改方式】实现连接管理器
     【相关依赖】websockets、asyncio
     【修改内容】
        - 实现连接池管理
        - 实现连接建立和断开处理
        - 实现消息广播
        - 实现单播消息发送
        - 实现心跳检测

- [ ] 5.2 实现 Agent WebSocket 路由
     【目标对象】`app/api/v1/websocket/agent_websocket.py`
     【修改目的】处理 Agent WebSocket 连接
     【修改方式】使用 FastAPI WebSocket
     【相关依赖】ConnectionManager、AgentSessionAppService
     【修改内容】
        - 实现连接端点：`/ws/agents/{agentId}/sessions`
        - 实现消息接收和转发
        - 实现错误处理
        - 实现认证和授权

- [ ] 5.3 实现 Session WebSocket 路由
     【目标对象】`app/api/v1/websocket/session_websocket.py`
     【修改目的】处理会话 WebSocket 连接
     【修改方式】使用 FastAPI WebSocket
     【相关依赖】ConnectionManager、ConversationAppService
     【修改内容】
        - 实现连接端点：`/ws/sessions/{sessionId}`
        - 实现消息接收和转发
        - 实现错误处理
        - 实现认证和授权

- [ ] 5.4 实现 Widget WebSocket 路由
     【目标对象】`app/api/v1/websocket/widget_websocket.py`
     【修改目的】处理 Widget WebSocket 连接
     【修改方式】使用 FastAPI WebSocket
     【相关依赖】ConnectionManager、WidgetAppService
     【修改内容】
        - 实现连接端点：`/ws/widgets/{widgetId}`
        - 实现消息接收和转发
        - 实现错误处理
        - 实现公开访问支持

- [ ] 5.5 实现 SSE 流式响应端点
     【目标对象】`app/api/v1/endpoints/sse_endpoints.py`
     【修改目的】提供 SSE 流式响应
     【修改方式】使用 sse-starlette
     【相关依赖】sse-starlette、ChatCompletionHandler
     【修改内容】
        - 实现聊天流式响应端点
        - 实现 RAG 流式响应端点
        - 实现 Token 逐字输出
        - 实现工具调用事件流
        - 实现错误处理和断开连接处理

### 六、API 路由层

- [ ] 6.1 创建会话相关端点
     【目标对象】`app/api/v1/endpoints/sessions.py`
     【修改目的】暴露会话管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ConversationAppService
     【修改内容】
        - `POST /api/v1/agents/{agentId}/sessions` - 创建会话
        - `GET /api/v1/agents/{agentId}/sessions` - 获取会话列表
        - `GET /api/v1/sessions/{sessionId}` - 获取会话详情
        - `PUT /api/v1/sessions/{sessionId}` - 更新会话
        - `DELETE /api/v1/sessions/{sessionId}` - 删除会话
        - 实现 CRUD 验证和错误处理

- [ ] 6.2 创建消息相关端点
     【目标对象】`app/api/v1/endpoints/messages.py`
     【修改目的】暴露消息管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ChatService
     【修改内容】
        - `POST /api/v1/sessions/{sessionId}/messages` - 发送消息
        - `GET /api/v1/sessions/{sessionId}/messages` - 获取消息历史
        - `GET /api/v1/sessions/{sessionId}/messages/{messageId}` - 获取单条消息
        - `DELETE /api/v1/sessions/{sessionId}/messages/{messageId}` - 删除消息
        - 实现分页和排序支持

- [ ] 6.3 创建聊天端点
     【目标对象】`app/api/v1/endpoints/chat.py`
     【修改目的】暴露聊天的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ChatService、AgentSessionAppService、RagSessionManager
     【修改内容】
        - `POST /api/v1/sessions/{sessionId}/chat` - 聊天（同步）
        - `POST /api/v1/sessions/{sessionId}/chat/stream` - 聊天（流式 SSE）
        - `POST /api/v1/agents/{agentId}/preview` - Agent 预览对话
        - `POST /api/v1/rag/{ragId}/chat` - RAG 对话
        - `POST /api/v1/rag/{ragId}/chat/stream` - RAG 流式对话
        - 实现请求验证和错误处理

- [ ] 6.4 创建 Widget 端点
     【目标对象】`app/api/v1/endpoints/widget.py`
     【修改目的】暴露 Widget 的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】WidgetAppService、WidgetMessageHandler
     【修改内容】
        - `GET /api/v1/widgets/{widgetId}/sessions` - Widget 会话列表
        - `POST /api/v1/widgets/{widgetId}/sessions` - 创建 Widget 会话
        - `POST /api/v1/widgets/{widgetId}/chat` - Widget 对话
        - 实现公开访问支持

### 七、消息处理和工作流

- [ ] 7.1 实现 Agent 工作流上下文
     【目标对象】`app/application/conversation/workflow/agent_workflow_context.py`
     【修改目的】管理 Agent 工作流状态
     【修改方式】实现工作流上下文
     【相关依赖】ChatContext、TaskManager
     【修改内容】
        - 实现 AgentWorkflowContext 类
        - 实现状态跟踪
        - 实现任务队列管理
        - 实现工具调用跟踪

- [ ] 7.2 实现 Agent 工作流状态机
     【目标对象】`app/application/conversation/workflow/agent_workflow_state.py`
     
     【修改目的】定义 Agent 工作流状态
     【修改方式】实现状态机模式
     【相关依赖】Enum
     【修改内容】
        - 定义工作流状态枚举
        - 实现状态转换逻辑
        - 实现状态验证

- [ ] 7.3 实现任务管理器
     【目标对象】`app/application/conversation/workflow/task_manager.py`
     【修改目的】管理 Agent 任务执行
     【修改方式】实现任务管理器
     【相关依赖】AgentManager、ToolManager
     【修改内容】
        - 实现任务创建
        - 实现任务执行
        - 实现任务状态跟踪
        - 实现任务取消

- [ ] 7.4 实现 Agent 事件总线
     【目标对象】`app/application/conversation/event/agent_event_bus.py`
     【修改目的】发布和订阅 Agent 事件
     【修改方式】实现事件总线
     【相关依赖】asyncio、Event
     【修改内容】
        - 实现事件发布
        - 实现事件订阅
        - 实现事件处理器注册
        - 实现事件分发

- [ ] 7.5 实现 Agent 处理器基类
     【目标对象】`app/application/conversation/handlers/agent/abstract_agent_handler.py`
     【修改目的】定义 Agent 处理器接口
     【修改方式】实现抽象基类
     【相关依赖】AgentWorkflowContext
     【修改内容】
        - 定义处理接口
        - 实现公共方法
        - 定义标准流程

- [ ] 7.6 实现分析处理器
     【目标对象】`app/application/conversation/handlers/agent/analyzer_message_handler.py`
     【修改目的】分析用户意图
     【修改方式】实现消息处理器
     【相关依赖】LLMDomainService
     【修改内容】
        - 实现意图识别
        - 实现信息需求提取
        - 实现任务建议生成

- [ ] 7.7 实现任务拆分处理器
     【目标对象】`app/application/conversation/handlers/agent/task_split_handler.py`
     【修改目的】拆分复杂任务
     【修改方式】实现消息处理器
     【相关依赖】LLMDomainService
     【修改内容】
        - 实现任务拆分逻辑
        - 实现子任务依赖关系
        - 实现任务优先级排序

- [ ] 7.8 实现任务执行处理器
     【目标对象】`app/application/conversation/handlers/agent/task_execution_handler.py`
     【修改目的】执行 Agent 任务
     【修改方式】实现消息处理器
     【相关依赖】ToolManager、TaskManager
     【修改内容】
        - 实现任务执行逻辑
        - 实现工具调用
        - 实现结果收集

- [ ] 7.9 实现摘要处理器
     【目标对象】`app/application/conversation/handlers/agent/summarize_handler.py`
     【修改目的】生成对话摘要
     【修改方式】实现消息处理器
     【相关依赖】LLMDomainService
     【修改内容】
        - 实现摘要生成逻辑
        - 实现关键信息提取
        - 实现摘要格式化

### 八、工具管理

- [ ] 8.1 实现 Agent 工具管理器
     【目标对象】`app/application/conversation/tools/agent_tool_manager.py`
     【修改目的】管理 Agent 工具调用
     【修改方式】实现工具管理器
     【相关依赖】ToolAppService、LLMDomainService
     【修改内容】
        - 实现工具注册
        - 实现工具调用
        - 实现工具结果处理
        - 实现工具调用缓存

- [ ] 8.2 实现内置工具提供者
     【目标对象】`app/application/conversation/tools/builtin/builtin_tool_provider.py`
     【修改目的】提供内置工具
     【修改方式】实现工具提供者接口
     【相关依赖】tool definition
     【修改内容】
        - 实现内置工具提供者基类
        - 实现内置工具注册表
        - 实现内置工具定义

- [ ] 8.3 实现 RAG 内置工具提供者
     【目标对象】`app/application/conversation/tools/builtin/rag_tool_provider.py`
     【修改目的】提供 RAG 相关内置工具
     【修改方式】实现工具提供者接口
     【相关依赖】RAGSearchAppService
     【修改内容】
        - 实现文档检索工具
        - 实现文档搜索工具
        - 实现工具注册

### 九、记忆提取

- [ ] 9.1 实现记忆提取服务
     【目标对象】`app/application/conversation/memory/memory_extractor.py`
     【修改目的】从对话中提取记忆
     【修改方式】实现提取服务
     【相关依赖】LLMDomainService、MemoryDomainService
     【修改内容】
        - 实现关键信息识别
        - 实现用户偏好提取
        - 实现上下文理解
        - 实现记忆项生成

- [ ] 9.2 实现记忆存储服务
     【目标对象】`app/application/conversation/memory/memory_storage.py`
     【修改目的】存储和检索对话记忆
     【修改方式】实现存储服务
     【相关依赖】MemoryDomainService
     【修改内容】
        - 实现记忆存储
        - 实现记忆检索
        - 实现记忆匹配
        - 实现记忆更新

### 十、事件监听和处理

- [ ] 10.1 实现会话事件发布器
     【目标对象】`app/application/conversation/events/conversation_event_publisher.py`
     【修改目的】发布会话相关事件
     【修改方式】实现事件发布器
     【相关依赖】AgentEventBus
     【修改内容】
        - 实现会话创建事件
        - 实现会话更新事件
        - 实现会话删除事件
        - 实现消息发送事件

- [ ] 10.2 实现会话事件监听器
     【目标对象】`app/application/conversation/events/conversation_event_listener.py`
     【修改目的】监听和响应会话事件
     【修改方式】实现事件监听器
     【相关依赖】ConversationEventPublisher
     【修改内容】
        - 实现事件订阅
        - 实现事件处理
        - 实现事件转发

- [ ] 10.3 实现 ConversationEventListener
     【目标对象】`app/application/conversation/listener/conversation_event_listener.py`
     【修改目的】监听领域事件
     【修改方式】实现事件监听器
     【相关依赖】ConversationEventPublisher
     【修改内容】
        - 订阅会话事件
        - 订阅消息事件
        - 实现事件处理逻辑

### 十一、DTO 和 Assembler

- [ ] 11.1 创建 Session DTO
     【目标对象】`app/application/conversation/dto/session_dto.py`
     【修改目的】定义会话 DTO
     【修改方式】使用 Pydantic
     【相关依赖】Session 模型
     【修改内容】
        - SessionResponseDTO
        - SessionCreateDTO
        - SessionUpdateDTO
        - SessionListResponseDTO

- [ ] 11.2 创建 Message DTO
     【目标对象】`app/application/conversation/dto/message_dto.py`
     【修改目的】定义消息 DTO
     【修改方式】使用 Pydantic
     【相关依赖】Message 模型
     【修改内容】
        - MessageResponseDTO
        - MessageCreateDTO
        - MessageUpdateDTO
        - MessageListResponseDTO

- [ ] 11.3 创建聊天 DTO
     【目标对象】`app/application/conversation/dto/chat_dto.py`
     【修改目的】定义聊天请求和响应 DTO
     【修改方式】使用 Pydantic
     【相关依赖】Session 模型、Message 模型
     【修改内容】
        - ChatRequestDTO
        - ChatResponseDTO
        - StreamChatRequestDTO
        - AgentPreviewRequestDTO
        - RagChatRequestDTO
        - AgentChatResponseDTO
        - RagRetrievalDocumentDTO

- [ ] 11.4 实现 Session Assembler
     【目标对象】`app/application/conversation/assembler/session_assembler.py`
     【修改目的】组装 Session 实体到 DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】Session 模型、Session DTO
     【修改内容】
        - 实现 to_dto 方法
        - 实现 to_entity 方法
        - 实现 to_list_dto 方法

- [ ] 11.5 实现 Message Assembler
     【目标对象】`app/application/conversation/assembler/message_assembler.py`
     【修改目的】组装 Message 实体到 DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】Message 模型、Message DTO
     【修改内容】
        - 实现 to_dto 方法
        - 实现 to_entity 方法
        - 实现 to_list_dto 方法

### 十二、数据库迁移

- [ ] 12.1 创建 sessions 表迁移脚本
     【目标对象】`alembic/versions/xxx_create_sessions.py`
     【修改目的】创建 sessions 表
     【修改方式】使用 Alembic
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义表结构
        - 创建索引
        - 定义外键约束

- [ ] 12.2 创建 messages 表迁移脚本
     【目标对象】`alembic/versions/xxx_create_messages.py`
     【修改目的】创建 messages 表
     【修改方式】使用 Alembic
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义表结构
        - 创建索引
        - 定义外键约束

- [ ] 12.3 创建 context 表迁移脚本
     【目标对象】`alembic/versions/xxx_create_context.py`
     【修改目的】创建 context 表
     【修改方式】使用 Alembic
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义表结构
        - 创建索引
        - 定义 JSON 字段类型

### 十三、单元测试

- [ ] 13.1 测试 Session 领域服务
     【目标对象】`tests/unit/domain/test_session_domain_service.py`
     【修改目的】确保 Session 领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】SessionDomainService
     【修改内容】
        - 测试创建会话
        - 测试更新会话
        - 测试归档会话
        - 测试恢复会话
        - 测试会话验证

- [ ] 13.2 测试 Message 领域服务
     【目标对象】`tests/unit/domain/test_message_domain_service.py`
     【修改目的】确保 Message 领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】MessageDomainService
     【修改内容】
        - 测试创建消息
        - 测试 Token 计数
        - 测试消息验证

- [ ] 13.3 测试 Context 领域服务
     【目标对象】`tests/unit/domain/test_context_domain_service.py`
     【修改目的】确保 Context 领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】ContextDomainService
     【修改内容】
        - 测试上下文创建
        - 测试消息添加
        - 测试上下文压缩
        - 测试上下文窗口管理

- [ ] 13.4 测试 ConversationAppService
     【目标对象】`tests/unit/application/test_conversation_app_service.py`
     【修改目的】确保对话应用服务正确性
     【修改方式】使用 pytest
     【相关依赖】ConversationAppService
     【修改内容】
        - 测试创建会话
        - 测试获取会话列表
        - 测试发送消息
        - 测试删除会话

- [ ] 13.5 测试 AgentMessageHandler
     【目标对象】`tests/unit/application/test_agent_message_handler.py`
     【修改目的】确保 Agent 消息处理器正确性
     【修改方式】使用 pytest
     【相关依赖】AgentMessageHandler
     【修改内容】
        - 测试消息处理
        - 测试工具调用
        - 测试任务执行
        - 测试摘要生成

- [ ] 13.6 测试 RagMessageHandler
     【目标对象】`tests/unit/application/test_rag_message_handler.py`
     【修改目的】确保 RAG 消息处理器正确性
     【修改方式】使用 pytest
     【相关依赖】RagMessageHandler
     【修改内容】
        - 测试消息处理
        - 测试文档检索
        - 测试上下文注入

### 十四、集成测试

- [ ] 14.1 测试会话 API 端到端
     【目标对象】`tests/integration/test_session_api.py`
     【修改目的】确保会话 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI、ConversationAppService

- [ ] 14.2 测试消息 API 端到端
     【目标对象】`tests/integration/test_message_api.py`
     【修改目的】确保消息 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI、ChatService
     【修改内容】
        - 测试发送消息端点
        - 测试获取消息历史端点
        - 测试删除消息端点

- [ ] 14.3 测试聊天 API 端到端
     【目标对象】`tests/integration/test_chat_api.py`
     【修改目的】确保聊天 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI、ChatService
     【修改内容】
        - 测试同步聊天端点
        - 测试流式聊天端点（SSE）
        - 测试 Agent 预览端点
        - 测试 RAG 对话端点

- [ ] 14.4 测试 WebSocket 连接
     【目标对象】`tests/integration/test_websocket.py`
     【修改目的】确保 WebSocket 连接正常工作
     【修改方式】使用 websockets.client
     【相关依赖】websockets、FastAPI
     【修改内容】
        - 测试 Agent WebSocket 连接
        - 测试 Session WebSocket 连接
        - 测试 Widget WebSocket 连接
        - 测试消息收发
        - 测试连接断开处理

### 十五、文档和配置

- [ ] 15.1 更新 OpenAPI 文档
     【目标对象】`app/api/v1/openapi.yaml`
     【修改目的】添加对话管理 API 文档
     【修改方式】使用 OpenAPI 规范
     【相关依赖】FastAPI 自动生成
     【修改内容】
        - 添加会话端点文档
        - 添加消息端点文档
        - 添加聊天端点文档
        - 添加 WebSocket 端点文档

- [ ] 15.2 更新配置文件
     【目标对象】`config/settings.py`
     【修改目的】添加对话管理相关配置
     【修改方式】添加配置项
     【相关依赖】环境变量
     【修改内容】
        - 添加 WebSocket 配置
        - 添加会话缓存配置
        - 添加上下文窗口配置
        - 添加流式响应配置
