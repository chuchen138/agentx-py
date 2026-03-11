# Agent 工作流实施清单

## 概述

本实施清单基于 spec.md 和 design.md，定义 Agent 工作流模块的具体实施步骤，包括任务拆分、任务执行、摘要生成、状态机和事件总线等功能。

## 实施

### 1. 数据模型层

- [ ] 1.1 定义工作流实体和数据模型
     【目标对象】`app/domain/workflow/model/`
     【修改目的】定义 Agent 工作流相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 Workflow 模型 (workflows 表)
          * 字段:id, workflow_id, session_id, user_id, agent_id, status, current_state, created_at, updated_at, completed_at
          * 索引:idx_session_id, idx_user_id, idx_status
        - 创建 Task 模型 (tasks 表)
          * 字段:id, task_id, workflow_id, parent_task_id, task_name, task_type, description, status, priority, depends_on, result_data, error_message, retry_count, created_at, started_at, completed_at
          * 索引:idx_workflow_id, idx_parent_task_id, idx_status
        - 创建 WorkflowEvent 模型 (workflow_events 表)
          * 字段:id, event_id, workflow_id, event_type, event_data, created_at
          * 索引:idx_workflow_id, idx_event_type
        - 创建 Summary 模型 (summaries 表)
          * 字段:id, summary_id, session_id, workflow_id, summary_text, token_count, created_at
          * 索引:idx_session_id
        - 实现 Pydantic Schema
          * WorkflowDTO, WorkflowCreateRequest, WorkflowListRequest
          * TaskDTO, TaskCreateRequest, TaskUpdateRequest
          * WorkflowEventDTO
          * SummaryDTO

- [ ] 1.2 实现工作流状态枚举
     【目标对象】`app/domain/workflow/constant/`
     【修改目的】定义工作流状态
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 WorkflowState 枚举
          * INIT - 初始化
          * ANALYZING - 分析中
          * SPLITTING - 拆分中
          * EXECUTING - 执行中
          * SUMMARIZING - 摘要中
          * COMPLETED - 完成
          * FAILED - 失败
        - 实现状态转换验证逻辑

- [ ] 1.3 实现任务状态枚举
     【目标对象】`app/domain/workflow/constant/`
     【修改目的】定义任务状态
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 TaskStatus 枚举
          * PENDING - 待执行
          * RUNNING - 执行中
          * COMPLETED - 完成
          * FAILED - 失败
          * CANCELLED - 已取消
        - 实现状态转换逻辑

- [ ] 1.4 实现任务类型枚举
     【目标对象】`app/domain/workflow/constant/`
     【修改目的】定义任务类型
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 TaskType 枚举
          * DATA_ANALYSIS - 数据分析
          * MULTI_QUERY - 多查询
          * INFORMATION_RETRIEVAL - 信息查询
          * REPORT_GENERATION - 报告生成
          * TOOL_EXECUTION - 工具执行
          * CUSTOM - 自定义
        - 实现任务类型与处理器的映射

### 2. 仓储层

- [ ] 2.1 实现工作流仓储模式
     【目标对象】`app/domain/workflow/repository.py`
     【修改目的】定义工作流数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 WorkflowRepository 接口
        - 实现 SQLAlchemyWorkflowRepository
          * create(workflow_data) -> Workflow
          * get_by_id(workflow_id) -> Workflow
          * get_by_session_id(session_id) -> List[Workflow]
          * get_by_user_id(user_id, page, size) -> Page[Workflow]
          * get_active_workflows() -> List[Workflow]
          * update_status(workflow_id, status, state)
          * complete_workflow(workflow_id, result_data)
          * fail_workflow(workflow_id, error_message)
          * delete(workflow_id)

- [ ] 2.2 实现任务仓储模式
     【目标对象】`app/domain/workflow/repository.py`
     【修改目的】定义任务数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 TaskRepository 接口
        - 实现 SQLAlchemyTaskRepository
          * create(task_data) -> Task
          * get_by_id(task_id) -> Task
          * get_by_workflow_id(workflow_id) -> List[Task]
          * get_pending_tasks(workflow_id) -> List[Task]
          * get_completed_tasks(workflow_id) -> List[Task]
          * get_task_dependencies(task_id) -> List[Task]
          * update_status(task_id, status, result_data, error_message)
          * increment_retry(task_id)
          * count_by_workflow(workflow_id) -> int

- [ ] 2.3 实现事件仓储模式
     【目标对象】`app/domain/workflow/repository.py`
     【修改目的】定义工作流事件数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 WorkflowEventRepository 接口
        - 实现 SQLAlchemyWorkflowEventRepository
          * record_event(event_data) -> WorkflowEvent
          * get_by_workflow_id(workflow_id, limit) -> List[WorkflowEvent]
          * get_by_event_type(event_type, limit) -> List[WorkflowEvent]
          * clear_events(workflow_id)

- [ ] 2.4 实现摘要仓储模式
     【目标对象】`app/domain/workflow/repository.py`
     【修改目的】定义摘要数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 SummaryRepository 接口
        - 实现 SQLAlchemySummaryRepository
          * save_summary(summary_data) -> Summary
          * get_by_session_id(session_id) -> Summary
          * get_by_workflow_id(workflow_id) -> Summary
          * update_summary(summary_id, summary_text, token_count)

### 3. 领域服务层

- [ ] 3.1 实现工作流状态机
     【目标对象】`app/domain/workflow/state_machine.py`
     【修改目的】管理工作流状态转换
     【修改方式】使用状态机模式
     【相关依赖】WorkflowRepository, WorkflowEventBus
     【修改内容】
        - 创建 AgentWorkflowState 类
          * 定义状态转换规则表
          * 验证状态转换合法性
          * 执行状态转换
          * 发布状态变更事件
        - 实现方法:
          * transition_to(new_state, trigger_event) -> bool
          * can_transition(to_state) -> bool
          * get_current_state() -> WorkflowState
          * persist_state()
          * restore_state(workflow_id)

- [ ] 3.2 实现事件总线
     【目标对象】`app/domain/workflow/event_bus.py`
     【修改目的】解耦工作流组件，实现异步事件处理
     【修改方式】使用观察者模式和事件驱动架构
     【相关依赖】asyncio, concurrent.futures
     【修改内容】
        - 创建 AgentEventBus 类 (单例)
          * _subscribers: Dict[EventType, List[EventHandler]]
          * _event_queue: asyncio.Queue
        - 实现方法:
          * subscribe(event_type, handler)
          * unsubscribe(event_type, handler)
          * publish(event_type, event_data, async=True)
          * start_event_loop()
          * stop_event_loop()
        - 定义事件类型:
          * WORKFLOW_CREATED
          * WORKFLOW_STATE_CHANGED
          * TASK_CREATED
          * TASK_COMPLETED
          * TASK_FAILED
          * TOOL_CALLED
          * SUMMARY_GENERATED
          * WORKFLOW_COMPLETED
          * WORKFLOW_FAILED

- [ ] 3.3 实现任务管理器
     【目标对象】`app/domain/workflow/task_manager.py`
     【修改目的】管理任务的创建、调度和监控
     【修改方式】使用责任链模式
     【相关依赖】TaskRepository, WorkflowEventBus
     【修改内容】
        - 创建 TaskManager 类
          * _task_queue: PriorityQueue
          * _executing_tasks: Dict[task_id, TaskInfo]
          * _thread_pool: ThreadPoolExecutor
        - 实现方法:
          * create_task(workflow_id, task_definition) -> Task
          * schedule_task(task_id)
          * execute_task(task_id)
          * complete_task(task_id, result_data)
          * fail_task(task_id, error_message, should_retry)
          * cancel_task(task_id)
          * get_task_status(task_id) -> TaskStatus
          * get_pending_tasks(workflow_id) -> List[Task]
          * check_dependencies_satisfied(task) -> bool

- [ ] 3.4 实现任务拆分处理器
     【目标对象】`app/domain/workflow/handlers/task_split.py`
     【修改目的】分析用户请求并拆分为子任务
     【修改方式】使用 LLM 进行任务分析和拆分
     【相关依赖】LLM Service, TaskManager
     【修改内容】
        - 创建 TaskSplitHandler 类
          * analyze_request(user_message, context) -> AnalysisResult
          * identify_complexity(analysis_result) -> bool
          * split_into_tasks(analysis_result) -> List[TaskDefinition]
          * set_task_dependencies(tasks) -> List[Task]
          * handle(user_message, context) -> SplitResult
        - 实现任务拆分策略:
          * 基于意图识别
          * 基于模板匹配
          * 基于 LLM 推理
        - 降级处理:
          * 拆分失败时降级到单任务模式

- [ ] 3.5 实现任务执行处理器
     【目标对象】`app/domain/workflow/handlers/task_execution.py`
     【修改目的】执行子任务和管理工具调用
     【修改方式】使用策略模式处理不同类型任务
     【相关依赖】TaskManager, ToolManager, WorkflowEventBus
     【修改内容】
        - 创建 TaskExecutionHandler 类
          * _task_executors: Dict[TaskType, TaskExecutor]
        - 实现方法:
          * register_executor(task_type, executor)
          * execute_task(task) -> TaskResult
          * handle_tool_call(task, tool_name, tool_args) -> ToolResult
          * process_tool_result(tool_result) -> ProcessedResult
          * handle_retry(task, max_retries)
        - 实现任务执行器:
          * DataAnalysisTaskExecutor
          * MultiQueryTaskExecutor
          * InformationRetrievalTaskExecutor
          * ReportGenerationTaskExecutor
          * ToolExecutionTaskExecutor
        - 超时控制:
          * 设置任务超时时间
          * 超时自动取消
          * 超时告警

- [ ] 3.6 实现摘要生成处理器
     【目标对象】`app/domain/workflow/handlers/summarize.py`
     【修改目的】生成对话摘要压缩上下文
     【修改方式】使用 LLM 生成摘要
     【相关依赖】LLM Service, SummaryRepository, TokenManagementService
     【修改内容】
        - 创建 SummarizeHandler 类
          * check_summary_needed(context) -> bool
          * generate_summary(context, strategy) -> str
          * save_summary(session_id, summary_text)
          * restore_context_from_summary(summary) -> List[Message]
        - 实现摘要触发策略:
          * TokenThresholdStrategy - Token 超过阈值
          * TurnCountStrategy - 对话轮次达到阈值
          * TaskCompletionStrategy - 任务链完成
          * ImportanceBasedStrategy - 基于重要性
        - 实现摘要压缩策略:
          * 提取关键信息
          * 保留重要消息
          * 合并相似内容

- [ ] 3.7 实现工具管理器
     【目标对象】`app/domain/workflow/tool_manager.py`
     【修改目的】管理和调用各种工具
     【修改方式】使用工厂模式
     【相关依赖】ToolRegistry, PermissionService
     【修改内容】
        - 创建 ToolManager 类
          * _tool_registry: ToolRegistry
          * _permission_service: PermissionService
        - 实现方法:
          * register_tool(tool_name, tool_definition)
          * select_tool(task_requirement) -> Tool
          * verify_permission(user_id, tool_name) -> bool
          * call_tool(tool_name, arguments) -> ToolResult
          * parse_tool_result(tool_result) -> ParsedResult
          * handle_tool_error(error) -> ErrorMessage
        - 支持的工具类型:
          * 内置工具 (RAG 检索、文件操作)
          * 用户自定义工具
          * MCP 工具 (外部服务器)
        - 安全控制:
          * 工具黑名单
          * 参数验证
          * 结果过滤

### 4. 应用服务层

- [ ] 4.1 实现工作流应用服务
     【目标对象】`app/application/workflow/`
     【修改目的】编排工作流相关的用例
     【修改方式】实现应用服务
     【相关依赖】WorkflowRepository, AgentEventBus, TaskManager
     【修改内容】
        - 实现 WorkflowAppService
          * create_workflow(user_id, agent_id, session_id) -> WorkflowDTO
          * get_workflow(workflow_id) -> WorkflowDTO
          * list_user_workflows(user_id, page, size) -> Page[WorkflowDTO]
          * list_session_workflows(session_id) -> List[WorkflowDTO]
          * get_active_workflow(session_id) -> WorkflowDTO
          * cancel_workflow(workflow_id, reason)
          * retry_workflow(workflow_id) -> WorkflowDTO
          * replay_workflow(workflow_id) -> WorkflowDTO
          * check_workflow_exists(workflow_id) -> bool

- [ ] 4.2 实现任务应用服务
     【目标对象】`app/application/workflow/`
     【修改目的】编排任务管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】TaskRepository, TaskManager
     【修改内容】
        - 实现 TaskAppService
          * get_task(task_id) -> TaskDTO
          * list_workflow_tasks(workflow_id) -> List[TaskDTO]
          * get_task_status(task_id) -> TaskStatusDTO
          * retry_task(task_id) -> TaskDTO
          * cancel_task(task_id)
          * get_task_dependencies(task_id) -> List[TaskDTO]
          * get_task_dependents(task_id) -> List[TaskDTO]

- [ ] 4.3 实现摘要应用服务
     【目标对象】`app/application/workflow/`
     【修改目的】编排摘要管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】SummaryRepository, SummarizeHandler
     【修改内容】
        - 实现 SummaryAppService
          * get_summary(session_id) -> SummaryDTO
          * get_summary_by_workflow(workflow_id) -> SummaryDTO
          * regenerate_summary(session_id, strategy) -> SummaryDTO
          * delete_summary(summary_id)
          * list_summaries(user_id, page, size) -> Page[SummaryDTO]

- [ ] 4.4 实现工作流配置服务
     【目标对象】`app/application/workflow/`
     【修改目的】管理工作流配置
     【修改方式】使用配置中心
     【相关依赖】无
     【修改内容】
        - 实现 WorkflowConfigService
          * is_workflow_enabled() -> bool
          * get_max_tasks_per_workflow() -> int
          * get_parallel_threshold() -> int
          * get_task_retry_config() -> RetryConfig
          * get_task_timeout() -> int
          * get_summary_token_threshold() -> int
          * get_summary_turn_threshold() -> int
          * is_state_persistence_enabled() -> bool
          * get_workflow_timeout() -> int

### 5. API 路由层

- [ ] 5.1 创建工作流管理 API 路由
     【目标对象】`app/api/v1/workflow/`
     【修改目的】暴露工作流管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】WorkflowAppService
     【修改内容】
        - `POST /api/v1/workflows` - 创建工作流
          * 请求:WorkflowCreateRequest
          * 响应:WorkflowDTO
        - `GET /api/v1/workflows/{workflow_id}` - 获取工作流详情
          * 响应:WorkflowDTO
        - `GET /api/v1/workflows` - 获取用户工作流列表 (分页)
          * 参数:page, size
          * 响应:Page[WorkflowDTO]
        - `GET /api/v1/sessions/{session_id}/workflows` - 获取会话工作流列表
          * 响应:List[WorkflowDTO]
        - `DELETE /api/v1/workflows/{workflow_id}` - 删除工作流
        - `POST /api/v1/workflows/{workflow_id}/cancel` - 取消工作流
        - `POST /api/v1/workflows/{workflow_id}/retry` - 重试工作流
        - `POST /api/v1/workflows/{workflow_id}/replay` - 重放工作流

- [ ] 5.2 创建任务管理 API 路由
     【目标对象】`app/api/v1/workflow/`
     【修改目的】暴露任务管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】TaskAppService
     【修改内容】
        - `GET /api/v1/workflows/{workflow_id}/tasks` - 获取任务列表
          * 响应:List[TaskDTO]
        - `GET /api/v1/tasks/{task_id}` - 获取任务详情
          * 响应:TaskDTO
        - `GET /api/v1/tasks/{task_id}/status` - 获取任务状态
          * 响应:TaskStatusDTO
        - `POST /api/v1/tasks/{task_id}/retry` - 重试任务
        - `POST /api/v1/tasks/{task_id}/cancel` - 取消任务
        - `GET /api/v1/tasks/{task_id}/dependencies` - 获取任务依赖
          * 响应:List[TaskDTO]

- [ ] 5.3 创建摘要管理 API 路由
     【目标对象】`app/api/v1/workflow/`
     【修改目的】暴露摘要管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】SummaryAppService
     【修改内容】
        - `GET /api/v1/sessions/{session_id}/summaries` - 获取会话摘要
          * 响应:SummaryDTO
        - `GET /api/v1/workflows/{workflow_id}/summaries` - 获取工作流摘要
          * 响应:SummaryDTO
        - `POST /api/v1/sessions/{session_id}/summaries/regenerate` - 重新生成摘要
          * 请求:{strategy: str}
          * 响应:SummaryDTO
        - `DELETE /api/v1/summaries/{summary_id}` - 删除摘要
        - `GET /api/v1/summaries` - 获取用户摘要列表 (分页)
          * 参数:page, size
          * 响应:Page[SummaryDTO]

- [ ] 5.4 创建工作流事件 API 路由
     【目标对象】`app/api/v1/workflow/`
     【修改目的】暴露工作流事件的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】WorkflowEventRepository
     【修改内容】
        - `GET /api/v1/workflows/{workflow_id}/events` - 获取工作流事件列表
          * 参数:limit
          * 响应:List[WorkflowEventDTO]
        - `GET /api/v1/events/types` - 获取事件类型统计
          * 响应:Dict[event_type, count]

### 6. 基础设施层

- [ ] 6.1 实现工作流配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置工作流运行参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - workflow.enabled - 是否启用工作流
        - workflow.state.persistence - 状态持久化开关
        - workflow.timeout - 工作流超时时间 (秒)
        - workflow.task.max_count - 最大任务数
        - workflow.task.parallel_threshold - 并行阈值
        - workflow.task.retry.max_attempts - 最大重试次数
        - workflow.task.retry.backoff - 重试退避时间
        - workflow.task.timeout - 任务超时时间 (秒)
        - workflow.summary.token_threshold - Token 阈值
        - workflow.summary.turn_threshold - 轮次阈值
        - workflow.summary.strategy - 摘要策略
        - workflow.eventbus.async - 是否异步
        - workflow.eventbus.queue_size - 事件队列大小
        - workflow.eventbus.thread_count - 事件处理线程数

- [ ] 6.2 实现线程池管理
     【目标对象】`app/infrastructure/concurrent/`
     【修改目的】管理工作流并发执行
     【修改方式】使用 ThreadPoolExecutor
     【相关依赖】concurrent.futures
     【修改内容】
        - 创建 WorkflowThreadPool 类
          * _executor: ThreadPoolExecutor
          * _max_workers: int
        - 实现方法:
          * submit(task_callable) -> Future
          * shutdown(wait=True)
          * get_active_count() -> int
          * get_queue_size() -> int
        - 配置参数:
          * max_workers (默认：CPU 核心数*2)
          * thread_name_prefix

- [ ] 6.3 实现定时任务清理
     【目标对象】`app/infrastructure/scheduler/`
     【修改目的】定期清理过期工作流和任务
     【修改方式】使用 APScheduler
     【相关依赖】APScheduler, WorkflowRepository
     【修改内容】
        - 创建定时任务
          * 每天凌晨 2 点执行
          * 清理 30 天前的已完成工作流
          * 清理无主任务 (orphan tasks)
        - 配置任务参数:
          * misfire_grace_time
          * coalesce

### 7. 事件监听器

- [ ] 7.1 实现工作流事件监听器
     【目标对象】`app/application/workflow/listener.py`
     【修改目的】监听工作流事件并处理
     【修改方式】实现事件监听器
     【相关依赖】AgentEventBus, WorkflowRepository
     【修改内容】
        - 创建 WorkflowEventListener 类
          * on_workflow_created(event)
            - 记录工作流创建日志
            - 初始化工作流状态
          * on_workflow_state_changed(event)
            - 持久化状态变更
            - 触发下一步处理
          * on_workflow_completed(event)
            - 记录完成时间
            - 发送完成通知
          * on_workflow_failed(event)
            - 记录错误信息
            - 触发告警
            - 尝试降级处理

- [ ] 7.2 实现任务事件监听器
     【目标对象】`app/application/workflow/listener.py`
     【修改目的】监听任务事件并处理
     【修改方式】实现事件监听器
     【相关依赖】AgentEventBus, TaskManager
     【修改内容】
        - on_task_created(event)
          * 调度任务执行
          * 检查依赖关系
        - on_task_completed(event)
          * 更新任务状态
          * 触发依赖任务检查
          * 收集任务结果
        - on_task_failed(event)
          * 记录失败日志
          * 判断是否重试
          * 传播失败到工作流

- [ ] 7.3 实现工具调用事件监听器
     【目标对象】`app/application/workflow/listener.py`
     【修改目的】监听工具调用事件
     【修改方式】实现事件监听器
     【相关依赖】AgentEventBus, ToolManager
     【修改内容】
        - on_tool_called(event)
          * 记录工具调用日志
          * 统计工具使用频率
        - on_tool_error(event)
          * 记录错误信息
          * 触发重试或降级

- [ ] 7.4 实现摘要生成事件监听器
     【目标对象】`app/application/workflow/listener.py`
     【修改目的】监听摘要生成事件
     【修改方式】实现事件监听器
     【相关依赖】AgentEventBus, SummaryRepository
     【修改内容】
        - on_summary_generated(event)
          * 保存摘要到数据库
          * 更新上下文
          * 记录 Token 节省统计

### 8. 测试

- [ ] 8.1 编写单元测试
     【目标对象】`tests/test_workflow_service.py`
     【修改目的】确保工作流功能正确性
     【修改方式】使用 pytest
     【相关依赖】WorkflowAppService, TaskManager, AgentWorkflowState
     【修改内容】
        - 测试工作流创建
        - 测试状态机状态转换
        - 测试任务拆分
        - 测试任务执行
        - 测试任务依赖管理
        - 测试摘要生成
        - 测试事件发布和订阅
        - 测试工具调用
        - 测试错误处理和重试

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_workflow_api.py`
     【修改目的】确保工作流 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, WorkflowAppService
     【修改内容】
        - 测试创建工作流 API
        - 测试获取工作流详情 API
        - 测试获取任务列表 API
        - 测试取消工作流 API
        - 测试重试工作流 API
        - 测试获取摘要 API
        - 测试完整工作流执行流程

- [ ] 8.3 编写性能测试
     【目标对象】`tests/performance/test_workflow_performance.py`
     【修改目的】测试工作流性能
     【修改方式】使用 pytest-benchmark
     【相关依赖】WorkflowAppService, TaskManager
     【修改内容】
        - 测试高并发工作流创建
        - 测试大量任务并行执行
        - 测试事件总线吞吐量
        - 测试内存使用情况
        - 测试状态机性能

### 9. 监控和日志

- [ ] 9.1 实现工作流监控指标
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控工作流运行状态
     【修改方式】使用 Prometheus 指标
     【相关依赖】prometheus_client
     【修改内容】
        - 定义工作流执行统计 Gauge/Counter
          * workflow_created_total - 工作流创建次数
          * workflow_completed_total - 工作流完成次数
          * workflow_failed_total - 工作流失败次数
          * workflow_execution_duration_seconds - 执行时长 Histogram
          * active_workflows - 活跃工作流数
        - 定义任务执行统计
          * tasks_created_total - 任务创建次数
          * tasks_completed_total - 任务完成次数
          * tasks_failed_total - 任务失败次数
          * task_execution_duration_seconds - 执行时长 Histogram
          * tool_calls_total - 工具调用次数
        - 定义摘要生成统计
          * summaries_generated_total - 摘要生成次数
          * summary_token_saved_total - Token 节省数量

- [ ] 9.2 实现工作流日志记录
     【目标对象】`app/infrastructure/logging/`
     【修改目的】记录工作流执行日志
     【修改方式】使用结构化日志
     【相关依赖】loguru
     【修改内容】
        - 工作流创建日志
        - 状态变更日志
        - 任务执行日志
        - 工具调用日志
        - 摘要生成日志
        - 错误日志
        - 性能日志

### 10. 错误处理

- [ ] 10.1 定义工作流异常
     【目标对象】`app/core/exceptions/`
     【修改目的】定义工作流相关异常
     【修改方式】自定义异常类
     【相关依赖】无
     【修改内容】
        - WorkflowNotFoundException (404)
          * 工作流不存在时抛出
        - TaskSplitFailedException (400)
          * 任务拆分失败时抛出
        - TaskExecutionFailedException (500)
          * 任务执行失败时抛出
        - InvalidStateException (400)
          * 非法状态转换时抛出
        - WorkflowTimeoutException (408)
          * 工作流超时时抛出
        - ToolCallTimeoutException (408)
          * 工具调用超时时抛出
        - DependencyNotSatisfiedException (400)
          * 任务依赖不满足时抛出

- [ ] 10.2 实现错误处理中间件
     【目标对象】`app/api/middleware/`
     【修改目的】统一处理工作流错误
     【修改方式】实现 FastAPI 中间件
     【相关依赖】FastAPI
     【修改内容】
        - 捕获 WorkflowNotFoundException
          * 返回 404 错误响应
        - 捕获 TaskSplitFailedException
          * 降级到单任务模式
        - 捕获 TaskExecutionFailedException
          * 尝试重试或降级
        - 捕获 InvalidStateException
          * 记录错误并终止工作流
        - 捕获超时异常
          * 取消工作流并清理资源

### 11. 性能优化

- [ ] 11.1 实现任务缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升任务执行性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 缓存任务拆分结果
        - 缓存工具定义
        - 缓存摘要生成结果
        - 实现缓存预热
        - 实现缓存过期和淘汰

- [ ] 11.2 实现任务并行优化
     【目标对象】`app/domain/workflow/task_manager.py`
     【修改目的】优化无依赖任务的并行执行
     【修改方式】使用线程池和优先级队列
     【相关依赖】concurrent.futures, queue.PriorityQueue
     【修改内容】
        - 识别无依赖任务
        - 批量提交到线程池
        - 最小化上下文切换
        - 动态调整并发度

- [ ] 11.3 实现异步事件处理
     【目标对象】`app/domain/workflow/event_bus.py`
     【修改目的】提升事件处理性能
     【修改方式】使用 asyncio
     【相关依赖】asyncio
     【修改内容】
        - 异步事件循环
        - 非阻塞事件发布
        - 批量事件处理
        - 事件优先级队列
