# 会话上下文实施清单

## 概述

本实施清单基于 spec.md 和 design.md，定义会话上下文管理模块的具体实施步骤，包括会话管理、SSE 实时通信、Token 计算和溢出处理等功能。

## 实施

### 1. 数据模型层

- [ ] 1.1 定义会话上下文实体和数据模型
     【目标对象】`app/domain/session/model/`
     【修改目的】定义会话上下文相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 SessionEntity 模型 (sessions 表)
          * 字段:id, session_id, user_id, agent_id, status, created_at, updated_at
          * 索引:idx_user_id, idx_agent_id, idx_status
        - 创建 MessageEntity 模型 (messages 表)
          * 字段:id, message_id, session_id, role, content, token_count, created_at
          * 索引:idx_session_id, idx_created_at
        - 创建 ContextEntity 模型 (contexts 表)
          * 字段:id, context_id, session_id, context_data, version, created_at
          * 索引:idx_session_id
        - 实现 Pydantic Schema
          * SessionDTO, SessionCreateRequest, SessionListRequest
          * MessageDTO, MessageCreateRequest
          * ContextDTO

- [ ] 1.2 实现会话状态枚举
     【目标对象】`app/domain/session/constant/`
     【修改目的】定义会话状态
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 SessionStatus 枚举
          * ACTIVE - 活跃状态
          * INTERRUPTED - 中断状态
          * COMPLETED - 完成状态
          * EXPIRED - 过期状态
        - 实现状态转换逻辑

- [ ] 1.3 实现 Token 计算策略接口
     【目标对象】`app/domain/session/token/`
     【修改目的】定义不同模型的 Token 计算策略
     【修改方式】使用 Strategy 模式
     【相关依赖】tiktoken
     【修改内容】
        - 定义 TokenCalculator 接口
          * calculate(text: str) -> int
        - 实现 GPT4TokenCalculator
          * 使用 tiktoken 编码 cl100k_base
        - 实现 GPT35TokenCalculator
          * 使用 tiktoken 编码 cl100k_base
        - 实现 ClaudeTokenCalculator
          * 使用 Anthropic Token 计算方法
        - 实现 LengthBasedTokenCalculator
          * 基于长度估算 (降级方案)
        - 实现 TokenCalculatorFactory
          * 根据模型名称选择计算器

- [ ] 1.4 实现 Token 溢出处理策略
     【目标对象】`app/domain/session/token/`
     【修改目的】处理 Token 超出限制的情况
     【修改方式】使用 Strategy 模式
     【相关依赖】TokenCalculator
     【修改内容】
        - 定义 TruncationStrategy 枚举
          * FROM_START - 从开头截断
          * FROM_END - 从尾部截断
          * IMPORTANT_FIRST - 保留重要消息优先
        - 定义 SummaryStrategy
          * 对早期消息进行摘要
          * 保留摘要和重要消息
        - 实现 TokenOverflowHandler
          * 计算当前 Token 数量
          * 应用溢出策略
          * 返回处理后的消息列表

### 2. 仓储层

- [ ] 2.1 实现会话仓储模式
     【目标对象】`app/domain/session/repository.py`
     【修改目的】定义会话数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 SessionRepository 接口
        - 实现 SQLAlchemySessionRepository
          * create(session_data) -> SessionEntity
          * get_by_id(session_id) -> SessionEntity
          * get_by_user_id(user_id, page, size) -> List[SessionEntity]
          * get_active_sessions() -> List[SessionEntity]
          * update_status(session_id, status)
          * delete(session_id)
          * count_by_user(user_id) -> int

- [ ] 2.2 实现消息仓储模式
     【目标对象】`app/domain/session/repository.py`
     【修改目的】定义消息数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 MessageRepository 接口
        - 实现 SQLAlchemyMessageRepository
          * create(message_data) -> MessageEntity
          * get_by_session_id(session_id, limit, before) -> List[MessageEntity]
          * get_last_n_messages(session_id, n) -> List[MessageEntity]
          * count_by_session(session_id) -> int
          * delete_by_session(session_id)

- [ ] 2.3 实现上下文仓储模式
     【目标对象】`app/domain/session/repository.py`
     【修改目的】定义上下文数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ContextRepository 接口
        - 实现 SQLAlchemyContextRepository
          * save_or_update(session_id, context_data)
          * get_by_session_id(session_id) -> ContextEntity
          * delete_by_session(session_id)

### 3. 领域服务层

- [ ] 3.1 实现会话管理器
     【目标对象】`app/domain/session/service.py`
     【修改目的】管理活跃会话的生命周期
     【修改方式】使用单例模式和 ConcurrentHashMap
     【相关依赖】SessionRepository, SSE
     【修改内容】
        - 创建 ChatSessionManager(单例)
          * _sessions: ConcurrentMap[str, SessionInfo]
          * register_session(session_id, user_id, agent_id, sse_emitter) -> SessionInfo
          * unregister_session(session_id)
          * get_session(session_id) -> SessionInfo
          * get_active_sessions_count() -> int
          * interrupt_session(session_id)
          * cleanup_expired_sessions(timeout_seconds)
        - 实现 SessionInfo 类
          * session_id, user_id, agent_id, status
          * sse_emitter, created_at, last_activity_at
          * is_expired(timeout) -> bool

- [ ] 3.2 实现 SSE 消息推送服务
     【目标对象】`app/domain/session/service.py`
     【修改目的】通过 SSE 向客户端推送实时消息
     【修改方式】使用 FastAPI SSE
     【相关依赖】ChatSessionManager, FastAPI
     【修改内容】
        - 实现 SSEMessageService
          * send_message(session_id, message_type, data)
            - 查找会话信息
            - 检查会话状态
            - 发送 SSE 事件
            - 处理发送失败
          * send_text_message(session_id, text)
          * send_error_message(session_id, error_message)
          * send_session_end(session_id)
        - 实现 SSE 连接管理
          * on_completion 回调清理
          * on_timeout 回调清理
          * on_error 回调处理

- [ ] 3.3 实现 Token 管理服务
     【目标对象】`app/domain/session/service.py`
     【修改目的】管理 Token 计算和溢出处理
     【修改方式】使用策略模式
     【相关依赖】TokenCalculator, TokenOverflowHandler
     【修改内容】
        - 实现 TokenManagementService
          * calculate_messages_token(messages, model_name) -> int
          * check_token_limit(messages, max_tokens, model_name) -> bool
          * handle_overflow(messages, max_tokens, strategy) -> List[Message]
          * apply_summary_strategy(messages, ratio) -> List[Message]
          * apply_truncation_strategy(messages, strategy) -> List[Message]
        - 实现 Token 缓存
          * LRU Cache 缓存文本 Token 计算结果
          * 缓存过期配置

- [ ] 3.4 实现会话持久化服务
     【目标对象】`app/domain/session/service.py`
     【修改目的】将会话数据持久化到数据库
     【修改方式】异步持久化
     【相关依赖】SessionRepository, MessageRepository
     【修改内容】
        - 实现 SessionPersistenceService
          * persist_session(session_info)
          * persist_message(session_id, message)
          * batch_persist_messages(session_id, messages)
          * archive_session(session_id)
          * should_persist() -> bool (配置开关)

### 4. 应用服务层

- [ ] 4.1 实现会话应用服务
     【目标对象】`app/application/session/`
     【修改目的】编排会话管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ChatSessionManager, SessionRepository, TokenManagementService
     【修改内容】
        - 实现 SessionAppService
          * create_session(user_id, agent_id) -> SessionDTO
          * get_session(session_id) -> SessionDTO
          * list_user_sessions(user_id, page, size) -> Page[SessionDTO]
          * interrupt_session(session_id)
          * close_session(session_id)
          * get_current_session_token(user_id) -> str
          * check_session_exists(session_id) -> bool

- [ ] 4.2 实现消息应用服务
     【目标对象】`app/application/session/`
     【修改目的】编排消息管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】MessageRepository, TokenManagementService
     【修改内容】
        - 实现 MessageAppService
          * send_message(session_id, role, content) -> MessageDTO
          * get_session_messages(session_id, limit, before) -> List[MessageDTO]
          * get_last_messages(session_id, n) -> List[MessageDTO]
          * calculate_message_token(content, model) -> int
          * clear_session_messages(session_id)

- [ ] 4.3 实现上下文应用服务
     【目标对象】`app/application/session/`
     【修改目的】编排上下文管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ContextRepository
     【修改内容】
        - 实现 ContextAppService
          * save_context(session_id, context_data)
          * get_context(session_id) -> ContextDTO
          * update_context(session_id, context_data)
          * delete_context(session_id)

- [ ] 4.4 实现会话配置服务
     【目标对象】`app/application/session/`
     【修改目的】管理会话配置
     【修改方式】使用配置中心或配置文件
     【相关依赖】无
     【修改内容】
        - 实现 SessionConfigService
          * is_session_enabled() -> bool
          * get_session_timeout() -> int
          * get_max_active_sessions() -> int
          * get_token_limit(model_name) -> int
          * get_overflow_strategy() -> str
          * is_persistence_enabled() -> bool

### 5. API 路由层

- [ ] 5.1 创建会话管理 API 路由
     【目标对象】`app/api/v1/session/`
     【修改目的】暴露会话管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】SessionAppService
     【修改内容】
        - `POST /api/v1/sessions` - 创建会话
          * 请求:SessionCreateRequest
          * 响应:SessionDTO
        - `GET /api/v1/sessions/{session_id}` - 获取会话详情
          * 响应:SessionDTO
        - `GET /api/v1/sessions` - 获取用户会话列表 (分页)
          * 参数:page, size
          * 响应:Page[SessionDTO]
        - `DELETE /api/v1/sessions/{session_id}` - 删除会话
        - `POST /api/v1/sessions/{session_id}/interrupt` - 中断会话
        - `POST /api/v1/sessions/{session_id}/close` - 关闭会话

- [ ] 5.2 创建消息管理 API 路由
     【目标对象】`app/api/v1/session/`
     【修改目的】暴露消息管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MessageAppService
     【修改内容】
        - `GET /api/v1/sessions/{session_id}/messages` - 获取消息列表
          * 参数:limit, before
          * 响应:List[MessageDTO]
        - `POST /api/v1/sessions/{session_id}/messages` - 发送消息
          * 请求:MessageCreateRequest
          * 响应:MessageDTO
        - `DELETE /api/v1/sessions/{session_id}/messages` - 清空消息

- [ ] 5.3 创建 SSE 流式 API 路由
     【目标对象】`app/api/v1/session/`
     【修改目的】提供 SSE 实时消息推送
     【修改方式】使用 FastAPI StreamingResponse
     【相关依赖】ChatSessionManager, SSEMessageService
     【修改内容】
        - `GET /api/v1/sessions/{session_id}/stream` - SSE 消息流
          * 建立 SSE 连接
          * 注册到 ChatSessionManager
          * 监听并推送消息
          * 处理连接断开
        - `POST /api/v1/conversation/interrupt` - 客户端中断对话
          * 调用 ChatSessionManager.interrupt_session()

- [ ] 5.4 创建上下文管理 API 路由
     【目标对象】`app/api/v1/session/`
     【修改目的】暴露上下文管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ContextAppService
     【修改内容】
        - `GET /api/v1/sessions/{session_id}/context` - 获取上下文
          * 响应:ContextDTO
        - `PUT /api/v1/sessions/{session_id}/context` - 更新上下文
          * 请求:ContextDTO
        - `DELETE /api/v1/sessions/{session_id}/context` - 删除上下文

- [ ] 5.5 创建 Token 计算 API 路由
     【目标对象】`app/api/v1/session/`
     【修改目的】提供 Token 计算服务
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】TokenManagementService
     【修改内容】
        - `POST /api/v1/tokens/calculate` - 计算 Token 数量
          * 请求:{text: str, model: str}
          * 响应:{token_count: int}
        - `POST /api/v1/tokens/check` - 检查 Token 是否超限
          * 请求:{messages: List[Message], max_tokens: int, model: str}
          * 响应:{exceeded: bool, current_tokens: int}

### 6. 基础设施层

- [ ] 6.1 实现 SSE 配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置 SSE 连接参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - sse.timeout - SSE 超时时间 (秒)
        - sse.heartbeat.interval - 心跳间隔 (毫秒)
        - sse.reconnect.max_retries - 最大重连次数
        - sse.reconnect.backoff - 重连退避时间 (毫秒)

- [ ] 6.2 实现会话配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置会话管理参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - session.enabled - 是否启用会话管理
        - session.timeout - 空闲超时时间 (秒)
        - session.max_duration - 最大会话时长 (秒)
        - session.max_active - 最大活跃会话数
        - session.storage.enabled - 是否启用存储
        - session.storage.ttl - 会话过期时间 (秒)

- [ ] 6.3 实现 Token 配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置 Token 管理参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - token.default_limit - 默认 Token 限制
        - token.overflow.strategy - 溢出处理策略
        - token.calculator.method - Token 计算方法
        - token.cache.enabled - 是否启用 Token 缓存
        - token.cache.size - LRU 缓存大小

- [ ] 6.4 实现定时任务清理超时会话
     【目标对象】`app/infrastructure/scheduler/`
     【修改目的】定期清理过期会话
     【修改方式】使用 APScheduler
     【相关依赖】ChatSessionManager
     【修改内容】
        - 创建定时任务
          * 每 5 分钟执行一次
          * 调用 cleanup_expired_sessions()
        - 配置任务参数
          * misfire_grace_time
          * coalesce

### 7. 事件监听器

- [ ] 7.1 实现 SSE 连接事件监听器
     【目标对象】`app/application/session/listener.py`
     【修改目的】监听 SSE 连接事件
     【修改方式】实现事件监听器
     【相关依赖】ChatSessionManager
     【修改内容】
        - on_sse_connect(session_id, user_id)
          * 记录连接日志
          * 更新会话活跃时间
        - on_sse_disconnect(session_id, reason)
          * 清理会话资源
          * 记录断开原因
          * 触发持久化

- [ ] 7.2 实现会话生命周期事件监听器
     【目标对象】`app/application/session/listener.py`
     【修改目的】监听会话生命周期事件
     【修改方式】实现事件监听器
     【相关依赖】SessionRepository, MessageRepository
     【修改内容】
        - on_session_created(session_id, user_id, agent_id)
          * 发送通知 (可选)
          * 记录统计信息
        - on_session_interrupted(session_id)
          * 记录中断日志
          * 触发消息清理
        - on_session_closed(session_id)
          * 持久化会话数据
          * 释放资源
          * 发送结束通知

### 8. 测试

- [ ] 8.1 编写单元测试
     【目标对象】`tests/test_session_service.py`
     【修改目的】确保会话管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ChatSessionManager, TokenManagementService
     【修改内容】
        - 测试会话创建和注册
        - 测试会话查询
        - 测试会话中断
        - 测试会话清理
        - 测试 Token 计算 (各种模型)
        - 测试 Token 溢出处理
        - 测试 SSE 消息推送
        - 测试并发会话管理

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_session_api.py`
     【修改目的】确保会话 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient 和 httpx
     【相关依赖】FastAPI, SessionAppService
     【修改内容】
        - 测试创建会话 API
        - 测试获取会话列表 API
        - 测试中断会话 API
        - 测试 SSE 连接
        - 测试消息推送流程
        - 测试 Token 计算 API
        - 测试上下文管理 API
        - 测试会话过期清理

- [ ] 8.3 编写性能测试
     【目标对象】`tests/performance/test_session_performance.py`
     【修改目的】测试会话管理性能
     【修改方式】使用 pytest-benchmark
     【相关依赖】ChatSessionManager
     【修改内容】
        - 测试高并发会话创建
        - 测试大量 SSE 连接
        - 测试 Token 计算性能
        - 测试内存使用情况
        - 测试清理任务效率

### 9. 监控和日志

- [ ] 9.1 实现会话监控指标
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控会话管理运行状态
     【修改方式】使用 Prometheus 指标
     【相关依赖】prometheus_client
     【修改内容】
        - 定义活跃会话数 Gauge
        - 定义会话创建速率 Counter
        - 定义平均会话时长 Histogram
        - 定义消息推送延迟 Histogram
        - 定义 Token 使用量 Counter
        - 定义会话中断率 Gauge

- [ ] 9.2 实现会话日志记录
     【目标对象】`app/infrastructure/logging/`
     【修改目的】记录会话管理日志
     【修改方式】使用结构化日志
     【相关依赖】loguru
     【修改内容】
        - 会话创建日志
        - 会话中断日志
        - SSE 连接/断开日志
        - Token 计算日志
        - 错误日志
        - 性能日志

### 10. 错误处理

- [ ] 10.1 定义会话管理异常
     【目标对象】`app/core/exceptions/`
     【修改目的】定义会话管理相关异常
     【修改方式】自定义异常类
     【相关依赖】无
     【修改内容】
        - SessionNotFoundException (404)
          * 会话不存在时抛出
        - SessionExpiredException (410)
          * 会话已过期时抛出
        - TokenLimitExceededException (400)
          * Token 超出限制时抛出
        - SSEConnectionException (500)
          * SSE 连接失败时抛出

- [ ] 10.2 实现错误处理中间件
     【目标对象】`app/api/middleware/`
     【修改目的】统一处理会话管理错误
     【修改方式】实现 FastAPI 中间件
     【相关依赖】FastAPI
     【修改内容】
        - 捕获 SessionNotFoundException
          * 返回 404 错误响应
        - 捕获 TokenLimitExceededException
          * 返回 400 错误响应和建议
        - 捕获 SSE 相关异常
          * 记录日志
          * 清理会话资源
        - 降级处理
          * Token 计算失败降级到长度估算

### 11. 性能优化

- [ ] 11.1 实现会话缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升会话查询性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 缓存活跃会话信息
        - 缓存最近消息列表
        - 缓存 Token 计算结果
        - 实现缓存预热
        - 实现缓存过期和淘汰

- [ ] 11.2 实现消息批量处理
     【目标对象】`app/domain/session/service.py`
     【修改目的】优化消息处理性能
     【修改方式】批量操作
     【相关依赖】无
     【修改内容】
        - 批量持久化消息
        - 批量 Token 计算
        - 批量发送 SSE 消息
        - 消息压缩 (大消息)

- [ ] 11.3 实现并发控制
     【目标对象】`app/domain/session/`
     【修改目的】保证并发安全
     【修改方式】使用线程安全数据结构
     【相关依赖】concurrent.futures
     【修改内容】
        - ConcurrentHashMap 存储会话
        - 异步执行耗时操作
        - 限流控制 (最大并发会话数)
        - 防止并发重复请求
