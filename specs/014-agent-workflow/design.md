# Agent 工作流技术设计

## 概述

Agent 工作流采用状态机与事件总线结合的架构，实现复杂任务的编排和处理，提供任务拆分、任务执行、摘要生成和状态管理等功能。

### 模块职责

- **013-conversation**: 对话流程控制，复杂任务委托给本模块
- **014-agent-workflow**: 纯编排引擎，负责任务调度，不存储状态
- **018-task-management**: 任务/工作流持久化、状态存储、执行追踪

## 技术架构

### 架构设计

系统采用状态机和事件总线架构。用户请求到达 Agent 消息处理器主入口，调度到任务拆分、任务执行和摘要生成等处理器。工作流状态机管理工作流状态转换，包括初始、分析中、拆分中、执行中、摘要中、完成和失败等状态。Agent 事件总线负责事件发布和订阅，实现组件解耦和异步事件处理。

**注意**：所有状态变更和任务数据都实时同步到 018-task-management 模块进行持久化，本模块仅维护内存中的运行时状态。

### 核心组件

#### AgentMessageHandler

Agent 消息处理器作为工作流主入口，负责接收用户消息、分析用户请求、调度工作流处理器、收集执行结果并返回响应给用户。

**职责**：
- 接收用户消息并判断是否为复杂任务
- 触发工作流状态机转换
- 协调各处理器按顺序执行
- 返回最终结果给用户

#### TaskSplitHandler

任务拆分处理器负责分析用户请求、识别复杂任务、拆分为子任务。

**职责**：
- 使用 LLM 分析用户意图
- 识别任务复杂度
- 生成子任务列表（包含依赖关系）
- 将任务创建请求发送到 TaskManager

#### TaskExecutionHandler

任务执行处理器负责执行子任务、管理工具调用和处理任务依赖。

**职责**：
- 从 TaskManager 获取待执行任务
- 检查任务依赖是否满足
- 执行任务（可能调用工具）
- 处理任务结果并发布事件

#### SummarizeHandler

摘要生成处理器负责生成对话摘要、压缩上下文和保存摘要数据。

**职责**：
- 根据配置判断是否需要生成摘要
- 使用 LLM 生成摘要
- 将摘要保存到 018-task-management 模块

#### AgentWorkflowStateMachine

工作流状态机管理工作流状态，处理状态转换，发布状态事件。

**状态**：INIT, ANALYZING, SPLITTING, EXECUTING, SUMMARIZING, COMPLETED, FAILED

**职责**：
- 定义状态转换规则表
- 验证状态转换合法性
- 执行状态转换并发布事件
- 通知 018-task-management 持久化状态

**状态转换表**：
```python
STATE_TRANSITIONS = {
    WorkflowState.INIT: [WorkflowState.ANALYZING],
    WorkflowState.ANALYZING: [WorkflowState.SPLITTING, WorkflowState.COMPLETED],
    WorkflowState.SPLITTING: [WorkflowState.EXECUTING, WorkflowState.FAILED],
    WorkflowState.EXECUTING: [
        WorkflowState.EXECUTING,  # 继续执行更多任务
        WorkflowState.SUMMARIZING,
        WorkflowState.COMPLETED
    ],
    WorkflowState.SUMMARIZING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
}
```

#### AgentEventBus

Agent 事件总线负责事件发布和订阅，解耦工作流组件，支持异步事件处理。

**事件类型**：
- WORKFLOW_CREATED
- WORKFLOW_STATE_CHANGED
- TASK_CREATED
- TASK_COMPLETED
- TASK_FAILED
- TOOL_CALLED
- SUMMARY_GENERATED
- WORKFLOW_COMPLETED
- WORKFLOW_FAILED

**职责**：
- 管理事件订阅者
- 发布事件到队列
- 异步处理事件循环
- 支持事件优先级（HIGH, NORMAL, LOW）

**事件结构**：
```python
class WorkflowEvent(BaseModel):
    event_id: str
    event_type: WorkflowEventType
    workflow_id: str
    task_id: Optional[str]
    data: Dict[str, Any]
    timestamp: datetime
    priority: EventPriority  # HIGH, NORMAL, LOW
```

#### TaskManager

任务管理器管理任务的创建、执行和监控，维护任务队列，处理任务依赖。

**职责**：
- 创建任务并建立依赖关系
- 调度任务到执行队列
- 监控任务执行状态
- 通知 018-task-management 更新任务状态

## 设计模式

### 状态机模式

状态机模式管理工作流的状态转换，确保状态转换的合法性。AgentWorkflowState 定义所有状态，通过事件触发状态转换，验证状态转换的合法性。

### 责任链模式

责任链模式将处理请求的多个处理器串联起来。AgentMessageHandler 到 TaskSplitHandler 到 TaskExecutionHandler 到 SummarizeHandler，每个处理器处理完请求后传递给下一个处理器，支持处理器的动态注册和移除。

### 观察者模式

观察者模式通过事件总线实现组件的解耦和通信。AgentEventBus 作为事件中心，各组件通过订阅事件获取通知，组件解耦，易于扩展。

### 事件驱动架构

事件驱动架构基于事件驱动工作流的执行。工作流状态变更发布事件，其他组件订阅事件并响应，支持异步事件处理。

## 任务处理

### 任务拆分

任务拆分流程分析用户请求的意图，根据意图生成子任务列表，支持数据分析和多查询等任务类型。系统设置任务依赖，处理任务之间的依赖关系，确保任务按正确顺序执行。

### 任务执行

任务执行流程检查任务依赖是否满足，执行任务并发布任务完成事件，返回结果。如果任务失败，系统支持重试机制或降级处理。

### 状态管理

状态管理采用状态机实现，验证状态转换的合法性，执行状态转换并发布状态变更事件。系统定义合法的状态转换路径，如初始到分析中、分析中到拆分中、拆分中到执行中或完成、执行中到执行中或摘要中或完成等。

### 事件处理

事件处理机制订阅工作流事件和任务事件，根据事件类型执行相应操作，如启动任务执行、生成摘要、完成工作流、处理工作流失败等。

## 关键流程

### 工作流执行流程

工作流执行流程包括用户发送消息到 Agent、Agent 消息处理器接收消息、分析消息意图判断是否为复杂任务、如果需要复杂处理则转换状态并调用任务拆分处理器、任务拆分处理器拆分任务、任务管理器调度任务执行、逐个或并行执行任务调用工具和处理数据、检查是否需要摘要、转换状态并返回最终结果给用户等步骤。

### 工具调用流程

工具调用流程包括任务需要使用工具、Agent 工具管理器选择工具查找符合条件的工具并验证工具权限、Agent 工具管理器调用工具构建请求并调用工具服务、获取工具结果解析结果或错误处理、将结果返回给任务等步骤。

## 错误处理

### 异常类型

系统定义任务拆分失败、任务执行失败、状态转换失败和摘要生成失败等异常类型。

**TaskSplitFailedException**：无法识别任务意图或任务拆分超出限制，降级到单任务处理模式。

**TaskExecutionFailedException**：工具调用超时或失败，支持重试或降级。

**InvalidStateException**：非法的状态转换或工作流状态不一致，抛出异常并终止工作流。

**SummaryGenerationFailedException**：摘要生成失败时不影响主流程，记录日志。

**WorkflowTimeoutException**：工作流执行超时，触发取消和补偿机制。

### 重试策略

#### 指数退避实现

```python
class ExponentialBackoffRetry:
    def __init__(self, max_retries=5, base_delay=1.0, max_delay=60.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
    
    def get_delay(self, attempt: int) -> float:
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        return delay + random.uniform(0, delay * 0.1)  # 添加抖动避免雪崩
```

#### 重试触发条件
- 网络错误（连接超时、DNS 解析失败）
- 临时性失败（服务不可用、限流）
- 工具超时（可重试的工具调用）

#### 不支持重试的场景
- 权限错误（认证失败、授权拒绝）
- 参数错误（验证失败、格式错误）
- 业务逻辑错误（数据不存在、状态冲突）

## 性能优化

### 任务并行执行

系统支持无依赖任务的并行执行，使用线程池管理并发任务，最小化上下文切换开销。

**动态并发调整算法**：
```python
def adjust_concurrency(cpu_usage: float, memory_usage: float) -> int:
    base_workers = multiprocessing.cpu_count() * 2
    if cpu_usage > 80 or memory_usage > 80:
        return max(base_workers // 2, 4)  # 降低并发
    elif cpu_usage < 50 and memory_usage < 50:
        return min(base_workers * 2, 32)  # 提高并发
    return base_workers
```

### 缓存优化

系统缓存任务拆分结果、工具定义和摘要生成结果，提升性能。

**缓存策略**：
- 任务拆分结果：LRU 缓存，TTL=5 分钟
- 工具定义：全局缓存，启动时预热
- 摘要生成结果：按 session_id 缓存，TTL=1 小时

### 异步处理

系统异步处理事件，长时间任务异步执行，避免阻塞主线程。

**异步事件循环**：
```python
async def _process_events(self):
    while self._running:
        try:
            event = await self._queue.get()
            await self._dispatch_event(event)
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.01)
```

## 长任务进度上报

### 进度上报机制

- 任务执行超过 30s 时自动启动进度上报
- 每 5s 上报一次进度（通过事件总线）
- 进度信息包含：当前步骤、完成百分比、预计剩余时间

**进度上报器实现**：
```python
class ProgressReporter:
    def __init__(self, task_id: str, event_bus: AgentEventBus):
        self.task_id = task_id
        self.event_bus = event_bus
        self.start_time = None
        self.total_steps = 0
        self.completed_steps = 0
    
    async def start(self):
        self.start_time = datetime.now()
        asyncio.create_task(self._report_loop())
    
    async def _report_loop(self):
        while True:
            await asyncio.sleep(5)
            progress = self.completed_steps / self.total_steps
            eta = self._calculate_eta()
            event = ProgressUpdateEvent(
                task_id=self.task_id,
                progress=progress,
                current_step=self._get_current_step(),
                eta_seconds=eta
            )
            self.event_bus.publish(EVENT_TYPES.TASK_PROGRESS, event)
```

### 用户中断支持

- 用户可发送取消请求（指定 task_id 或 workflow_id）
- 取消信号传播到 TaskExecutor
- 正在执行的工具调用支持取消（如果工具支持）
- 清理已分配资源（数据库连接、文件句柄）

**取消信号传播**：
```python
class TaskExecutor:
    def __init__(self):
        self._cancel_token = asyncio.Event()
    
    def cancel(self):
        self._cancel_token.set()
    
    async def execute(self, task):
        if self._cancel_token.is_set():
            raise TaskCancelledException(f"Task {task.id} was cancelled")
        # 执行任务，定期检查 cancel_token
```

### 超时处理

- 短任务超时：30s（默认）
- 长任务超时：300s（默认）
- 超时前 10s 发送告警事件
- 超时后自动取消并触发补偿

## Saga 补偿机制

### 补偿触发条件

- 工作流整体失败（某个关键任务失败且无法重试）
- 用户主动取消工作流
- 系统检测到不可恢复错误

### 补偿策略

**正向补偿**：执行相反操作（如删除已创建的文件、回滚数据库事务）

**记录补偿日志**：记录补偿操作到事件存储，便于审计和问题排查

**补偿失败重试**：最多重试 3 次，失败后告警并标记为需要人工介入

**Saga 协调器实现**：
```python
class SagaCoordinator:
    def __init__(self, workflow_id: str, event_bus: AgentEventBus):
        self.workflow_id = workflow_id
        self.event_bus = event_bus
        self.compensation_log = []
    
    def log_compensation(self, task, result):
        self.compensation_log.append({
            'task_id': task.id,
            'action': 'compensate',
            'original_result': result,
            'timestamp': datetime.now()
        })
    
    async def execute_compensation(self):
        for entry in reversed(self.compensation_log):
            await self._compensate_task(entry)
    
    async def _compensate_task(self, entry, max_attempts=3):
        for attempt in range(max_attempts):
            try:
                await self._do_compensate(entry)
                return
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Compensation failed after {max_attempts} attempts")
                    raise
                await asyncio.sleep(2 ** attempt)
```

### 补偿示例

```
工作流：数据分析 → 生成报告 → 发送邮件
失败点：发送邮件失败
补偿操作：删除临时生成的报告文件
```

## 监控指标

### 工作流级别

- `workflow_execution_active_count`: 活跃工作流数
- `workflow_execution_duration_seconds`: 执行时长直方图
- `workflow_success_rate`: 成功率（%）
- `workflow_failure_rate`: 失败率（%）

### 任务级别

- `task_execution_total`: 任务执行总数
- `task_execution_duration_seconds`: 任务执行时长
- `task_retry_total`: 任务重试次数
- `task_timeout_total`: 任务超时次数

### 事件总线

- `event_published_total`: 发布事件总数
- `event_queue_size`: 队列当前长度
- `event_processing_latency_ms`: 处理延迟
- `event_dropped_total`: 丢弃事件数（队列满时）

### 并发控制

- `thread_pool_active_threads`: 线程池活跃线程数
- `thread_pool_queue_size`: 线程池队列长度
- `concurrent_workflows`: 并发工作流数
- `max_parallel_tasks_per_workflow`: 单工作流最大并行任务数

## 监控指标

### 关键指标

系统监控工作流执行统计（工作流创建次数、平均执行时间、成功/失败率）、任务执行统计（任务总数、执行时长、工具调用次数）和摘要生成统计（摘要生成次数、摘要平均长度、Token 节省统计）等指标。

### 告警规则

系统监控工作流执行超时、任务失败率过高、工具调用失败频繁和状态机异常等情况并设置告警。

## 配置设计

### 工作流配置

工作流配置包括启用状态、状态机持久化、工作流超时、任务拆分（最大任务数、并行阈值）、任务执行（重试配置、超时）、摘要生成（Token 阈值、轮次阈值、策略）和事件总线（异步、队列大小、线程数）等配置。
