# 对话管理技术设计

## 概述

对话管理模块采用分层架构设计，符合领域驱动设计原则。支持多种聊天模式、流式响应、Agent 工作流、RAG 检索增强、记忆集成、高可用和计费集成等核心功能。

## 技术架构

### 分层架构

系统采用四层架构：接口层（REST API/WebSocket/SSE）处理 HTTP 请求和定义 DTO；应用层协调业务用例，包括对话应用服务、会话管理器和消息处理器工厂；领域层封装核心业务逻辑，管理会话、消息、上下文等实体模型和仓储接口；基础设施层提供持久化、缓存、外部服务集成和消息队列支持。

### 设计原则

遵循领域驱动设计、依赖倒置、分层清晰、单一职责和开闭原则，确保各层职责明确、扩展灵活。

## 核心组件

### 应用层组件

ConversationAppService 作为应用层统一入口，负责对话业务编排。核心依赖包括领域服务（会话、消息、对话）、消息处理器工厂、LLM 领域服务、Token 领域服务、计费服务和会话管理器。提供创建会话、删除会话、获取会话列表、流式聊天（包括 Agent 聊天和 RAG 聊天）、预览对话等核心功能。

MessageHandlerFactory 根据请求类型选择合适的处理器，包括标准对话处理器、Agent 智能体处理器、RAG 检索增强处理器和预览处理器。

AbstractMessageHandler 定义消息处理的核心流程，支持处理流式聊天、管理对话上下文、支持工具调用、集成记忆服务、执行跟踪和账单计费。子类实现包括 ChatMessageHandler（标准对话）、AgentMessageHandler（Agent 对话，支持工具调用）、RagMessageHandler（RAG 对话，支持检索增强）和 PreviewMessageHandler（预览对话）。

ChatSessionManager 管理正在进行的聊天会话，支持会话注册与注销、会话中断控制、SSE 连接管理、超时处理和自动清理。

### 领域层组件

领域模型包括 SessionEntity（会话实体）、MessageEntity（消息实体）和 ContextEntity（上下文实体）。消息类型枚举定义 TEXT、TOOL_CALL、TASK_EXEC、TASK_STATUS_TO_LOADING、TASK_STATUS_TO_FINISH、TASK_SPLIT_FINISH、RAG_RETRIEVAL_START/PROGRESS/END、RAG_THINKING_START/PROGRESS/END、RAG_ANSWER_START/PROGRESS/END 等多种类型。

领域服务包括 ConversationDomainService（获取会话消息、批量插入消息、保存消息、删除会话消息、更新消息 token 数量）、ContextDomainService（获取上下文、插入或更新上下文）、ChatCompletionHandler（封装与大模型的交互逻辑，支持同步完成和流式完成）和 ContextProcessor（管理对话上下文的构建、更新和压缩，支持历史消息加载、Token 计算、上下文压缩、消息摘要生成和上下文溢出处理）。

ChatContext 封装对话所需的所有信息，包括会话 ID、用户 ID、用户消息、智能体实体、模型实体、服务商实体、大模型配置、上下文实体、历史消息列表、MCP server 名称、多模态文件、高可用实例 ID、流式响应标志、追踪上下文、公开访问标志和公开访问 ID。

## 设计模式

系统采用工厂模式，根据请求类型自动选择合适的消息处理器；采用策略模式，不同的聊天模式使用不同的处理策略；采用模板方法模式，定义处理流程骨架，子类实现具体步骤；采用责任链模式，Agent 处理器链条包括任务拆分、任务执行和结果汇总；采用观察者模式，通过事件总线协调工作流；采用构建器模式，构建复杂对象如 ChatContext 和 AgentChatResponse。

## 流式响应实现

使用 Spring SseEmitter 实现服务器推送事件，创建 SSE 发射器，注册到会话管理器，异步处理消息逻辑，完成后关闭发射器。定义通用的消息传输接口，支持发送消息、发送结束消息和发送错误信息。

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

### MyBatis-Plus 集成

使用 MyBatis-Plus 进行数据访问，支持创建会话、列表查询、批量操作等常用功能。

### 批量操作

支持批量插入消息、批量删除消息等操作，提高数据访问效率。

## 接口定义

ConversationAppService 提供创建会话、删除会话、获取会话列表、流式聊天（包括 Agent 聊天和 RAG 聊天）和预览对话等接口。ChatSessionManager 提供注册会话、移除会话、中断会话和检查会话是否中断等接口。ConversationDomainService 提供获取会话消息、批量插入消息、保存消息、删除会话消息和更新消息 token 数量等接口。ContextDomainService 提供获取上下文、插入或更新上下文等接口。ChatCompletionHandler 提供同步完成聊天和流式完成聊天等接口。

## 数据模型

数据库表结构包括 sessions 表（会话表）、messages 表（消息表）和 contexts 表（上下文表）。sessions 表包含会话 ID、标题、用户 ID、Agent ID、描述、归档标志、元数据等字段。messages 表包含消息 ID、会话 ID、角色、内容、消息类型、创建时间、token 数量、服务商、模型、元数据、文件 URL 等字段。contexts 表包含上下文 ID、会话 ID、历史消息 ID 列表、总 token 数、最大容量、摘要等字段。

## 技术栈

核心框架包括 Spring Boot 3.x、Spring Web MVC、MyBatis-Plus 和 LangChain4j（LLM 集成）。数据存储包括 MySQL 8.0（关系型数据库）和 Redis（缓存，可选）。通信协议包括 HTTP/REST（API 接口）和 SSE（流式响应）。工具库包括 Hutool（Java 工具库）、Lombok（注解简化代码）和 Jackson（JSON 处理）。

## 性能优化

连接池管理包括数据库连接池（HikariCP）和 HTTP 客户端连接池。缓存策略包括会话缓存、消息历史缓存和模型配置缓存。异步处理包括消息保存异步化、记忆提取异步化和计费记录异步化。批量操作包括批量消息插入和批量对象属性映射。

## 安全设计

数据隔离基于 user_id 的用户数据隔离和基于 session_id 的会话隔离。权限控制确保只能访问自己的会话和消息。敏感信息过滤保护系统提示中的敏感信息和用户上传文件的路径。

## 扩展设计

### 自定义处理器

可以继承 AbstractMessageHandler 实现自定义处理逻辑，使用 @Component 注解标记为 Spring Bean。

### 自定义消息类型

可以扩展 MessageType 枚举，添加自定义消息类型。

### 自定义工具

可以实现 BuiltInTool 接口，提供自定义工具，使用 @Component 注解标记为 Spring Bean。

## 监控与日志

日志级别包括 INFO（正常操作日志）、WARN（警告日志）和 ERROR（错误日志）。监控指标包括会话创建速率、消息处理速率、平均响应时间、Token 消耗统计和错误率。审计日志包括用户操作审计、模型调用审计、工具使用审计和计费记录。
