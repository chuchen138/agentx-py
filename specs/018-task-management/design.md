# 任务管理技术设计

## 概述

任务管理能力采用分层架构设计，遵循领域驱动设计（DDD）原则，提供任务聚合和状态管理能力。**本模块仅负责持久化和查询，不包含任务执行逻辑**。

## 技术架构

### 架构分层

系统采用四层架构：

- **接口层（Interfaces）**：处理 HTTP 请求，定义 DTO，参数校验（FastAPI routers）
- **应用层（Application）**：负责业务流程编排，DTO 转换，调用领域服务（TaskAppService）
- **领域层（Domain）**：包含核心业务逻辑，实体模型，领域服务，聚合根（TaskEntity、TaskStatus、TaskAggregate、TaskDomainService）
- **基础设施层（Infrastructure）**：负责数据库访问，数据持久化（TaskRepository with SQLAlchemy）

### 核心组件

**TaskAppService**：负责任务管理的业务流程编排
- 获取当前会话的任务
- 聚合任务和子任务
- 提供任务查询能力
- 事务管理（@transactional 装饰器）

**TaskDomainService**：负责任务的领域逻辑处理
- 查询任务聚合
- 任务状态更新（验证状态转换规则）
- 任务进度更新
- 权限验证（user_id 匹配检查）

## 核心设计

### 任务实体和枚举

**TaskEntity** 包含以下字段：
- id (UUID): 任务 ID
- session_id (String): 所属会话 ID
- user_id (String): 用户 ID
- parent_task_id (String): 父任务 ID
- task_name (String): 任务名称（最大 256 字符）
- description (String): 任务描述（最大 4096 字符）
- status (TaskStatus): 任务状态
- progress (Integer): 任务进度（0-100）
- start_time (DateTime): 开始时间
- end_time (DateTime): 结束时间
- task_result (String): 任务结果（最大 65535 字符）
- version (Long): 版本号（乐观锁）
- deleted_at (DateTime): 删除时间（软删除）
- created_at (DateTime): 创建时间
- updated_at (DateTime): 更新时间

**TaskStatus 枚举**定义了任务状态：
- WAITING（等待中）
- IN_PROGRESS（进行中）
- COMPLETED（已完成）
- FAILED（失败）

**状态转换规则**：
```
WAITING → IN_PROGRESS → COMPLETED
                      ↘ FAILED
```

**TaskEntity.update_status()** 方法：
- 根据状态自动设置开始/结束时间
- 验证状态转换合法性
-  increment version字段
- 抛出 OptimisticLockException 如果版本不匹配

### 任务聚合根

**TaskAggregate** 包含父任务和子任务列表，形成树形结构：

```python
class TaskAggregate:
    def __init__(self, task: TaskEntity, sub_tasks: List[TaskEntity]):
        self.task = task  # 父任务或独立任务
        self.sub_tasks = sub_tasks  # 子任务列表（可为空）
    
    def is_all_completed(self) -> bool:
        """检查所有任务是否完成"""
        if not self.sub_tasks:
            return self.task.status == TaskStatus.COMPLETED
        return all(t.status == TaskStatus.COMPLETED for t in self.sub_tasks)
```

**聚合边界**：
- 单个会话内的任务及其子任务形成一个聚合
- 聚合内保证数据一致性（事务性）
- 跨聚合引用通过 task ID 实现

**一致性保证**：
- 父任务和子任务在同一事务中更新
- 子任务完成后，父任务状态可自动聚合（由 014 触发）
- 孤儿任务（父任务删除）级联软删除

### 任务查询和状态管理

**获取当前会话的聚合任务**：
1. 查询父任务（parent_task_id 为空，session_id 匹配）
2. 查询子任务（parent_task_id 等于父任务 ID）
3. 构建 TaskAggregate 返回结果
4. 使用 Redis 缓存结果（TTL 5 分钟）

**状态转换业务规则**：
- WAITING → IN_PROGRESS: 设置 start_time
- IN_PROGRESS → COMPLETED: 设置 end_time
- IN_PROGRESS → FAILED: 设置 end_time，记录错误信息
- 禁止反向转换（如 COMPLETED → IN_PROGRESS）

**TaskEntity.update_status()** 实现：
```python
def update_status(self, new_status: TaskStatus, version: int):
    if self.version != version:
        raise OptimisticLockException(f"Expected version {version}, got {self.version}")
    
    if not self._is_valid_transition(new_status):
        raise InvalidStatusTransitionException(f"Cannot transition from {self.status} to {new_status}")
    
    old_status = self.status
    self.status = new_status
    
    if new_status == TaskStatus.IN_PROGRESS and not self.start_time:
        self.start_time = datetime.now()
    
    if new_status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not self.end_time:
        self.end_time = datetime.now()
    
    self.version += 1
    self.updated_at = datetime.now()
```

### 数据持久化

**数据库表设计**（tasks 表）：
```sql
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    parent_task_id UUID,
    task_name VARCHAR(256) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL,
    progress INTEGER DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    task_result TEXT,
    version BIGINT DEFAULT 0,
    deleted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id)
);

-- 索引
CREATE INDEX idx_session_created ON tasks(session_id, created_at DESC);
CREATE INDEX idx_user_status ON tasks(user_id, status);
CREATE INDEX idx_parent_task ON tasks(parent_task_id);
CREATE INDEX idx_deleted_at ON tasks(deleted_at);

-- 行级安全策略（RLS）
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
CREATE POLICY user_isolation_policy ON tasks
    FOR ALL
    USING (user_id = current_setting('app.current_user_id')::VARCHAR 
           OR current_setting('app.is_admin')::BOOLEAN = TRUE);
```

## 关键设计决策

**使用聚合根模式**的优点：
- 任务和子任务形成一个聚合，通过聚合根管理整体生命周期
- 保证数据一致性（同一事务内更新）
- 简化查询逻辑（一次性返回父子任务树）

**任务状态的自动管理**：
- 使用 update_status() 方法自动设置时间戳
- 减少手动错误
- 内置状态转换验证

**查询优化策略**：
- 只查询必要的任务数据
- 使用 SQL 排序获取最新任务（ORDER BY created_at DESC）
- 避免 N+1 查询问题（使用 JOIN 或批量查询）
- Redis 缓存热点数据（当前会话任务）

## 性能优化

### 索引策略

为常用查询字段建立索引：
- `idx_session_created`: (session_id, created_at DESC) - 覆盖索引
- `idx_user_status`: (user_id, status) - 复合索引
- `idx_parent_task`: (parent_task_id) - 单字段索引

使用 EXPLAIN ANALYZE 分析查询计划，确保索引命中。

### 缓存策略

**Cache Hit Rate Target**: >80% for current session queries

**缓存键模式**：
- `task:session:{session_id}:current` - 当前会话任务

**TTL 配置**：
- 进度缓存：5 分钟
- 状态变更时立即失效
- 任务完成后失效

**缓存方法**：
```python
async def get_current_session_tasks(session_id: str) -> TaskAggregate:
    cache_key = f"task:session:{session_id}:current"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)
    
    # 查询数据库
    aggregate = await repository.find_aggregate_by_session(session_id)
    
    # 写入缓存
    await redis.setex(cache_key, 300, json.dumps(aggregate))
    return aggregate
```

### 批量更新

支持批量更新任务状态，减少数据库操作次数：
```python
async def bulk_update_statuses(task_ids: List[str], new_status: TaskStatus):
    async with db.begin():
        await db.execute(
            update(Task).where(Task.id.in_(task_ids)).values(status=new_status)
        )
```

### 连接池配置

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=CPU_CORES * 2 + DISK_SPINDLES,  # 默认 20
    max_overflow=30,
    pool_recycle=3600,  # 1 小时回收
    pool_pre_ping=True  # 连接前探测
)
```

### 慢查询监控

- 慢查询阈值：>100ms
- 记录慢查询日志（SQL + 参数 + 耗时）
- 定期分析慢查询日志优化索引

## 扩展性设计

**支持不同类型的任务**：
- 工作流任务（workflow_task）
- 子任务（sub_task）
- 工具调用任务（tool_call_task）

**支持任务优先级**（未来扩展）：
- priority 字段（HIGH, MEDIUM, LOW）
- 控制任务执行顺序

**支持任务依赖关系**（未来扩展）：
- task_dependencies 表（task_id, depends_on_task_id）
- 执行前检查依赖是否完成

**支持失败重试机制**（由 014 负责）：
- 018 仅记录重试后的状态
- 不存储重试次数等元数据

## 集成与安全

### 模块集成

**与 014-agent-workflow 集成**：
- 014 调用 TaskAppService.update_status() 在状态机转换时
- 014 调用 TaskAppService.create_task() 在创建任务时
- 直接方法调用（无 HTTP 开销）
- 异常处理和回滚由 014 协调

**与会话模块集成**：
- 每个会话可以有多个任务
- 任务属于特定的会话（session_id 外键）
- 会话删除时级联软删除所有任务

**与 Agent 模块集成**：
- 任务是 Agent 执行产生的
- 任务内容与 Agent 能力相关
- Agent 的任务分解逻辑创建任务（通过 014）

**与定时任务集成**：
- 定时任务可以创建会话任务
- 定时任务执行时设置任务结果
- 定时任务的状态与会话任务关联

**与 016-execution-trace 深度集成**：

每个任务状态变更自动产生 Trace Span：

```python
# 在 TaskDomainService.update_status() 中
async def update_status(self, task_id: str, new_status: TaskStatus, user_id: str):
    task = await repository.find_by_id(task_id)
    old_status = task.status
    
    # 更新状态
    task.update_status(new_status, expected_version)
    await repository.save(task)
    
    # 发布事件到 016
    event = TaskStatusChangedEvent(
        task_id=task_id,
        old_status=old_status.value,
        new_status=new_status.value,
        timestamp=datetime.now(),
        user_id=user_id,
        trace_id=generate_trace_id()  # 关联 ID
    )
    await event_bus.publish(event)
```

**事件 payload**：
```json
{
  "event_type": "TASK_STATUS_CHANGED",
  "data": {
    "task_id": "task-123",
    "old_status": "IN_PROGRESS",
    "new_status": "COMPLETED",
    "timestamp": "2026-03-14T10:30:00Z",
    "user_id": "user-456",
    "trace_id": "trace-789"
  }
}
```

016 监听事件并创建 trace span，通过 trace_id 关联任务和执行链路。

### 安全设计

**查询拦截器**：
自动注入 `WHERE user_id = :current_user_id` 条件：
```python
class UserIsolationInterceptor:
    @asynccontextmanager
    async def intercept(self, user_id: str):
        # 设置 PostgreSQL session 变量
        await db.execute("SET LOCAL app.current_user_id = :user_id", {"user_id": user_id})
        yield
        # RLS 策略自动生效
```

**加密存储**：
- AES-256 加密敏感任务结果
- 密钥从环境变量读取
- 标记敏感任务（is_sensitive 字段）

```python
from cryptography.fernet import Fernet

class TaskResultEncryption:
    def __init__(self):
        self.key = os.getenv("TASK_ENCRYPTION_KEY")
        self.cipher = Fernet(self.key)
    
    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

**审计日志**：
独立的 `task_audit_log` 表：
```sql
CREATE TABLE task_audit_log (
    id UUID PRIMARY KEY,
    task_id UUID NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- TASK_CREATED, TASK_STATUS_CHANGED, TASK_DELETED
    old_value TEXT,  -- JSON 格式
    new_value TEXT,  -- JSON 格式
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**访问模式检测**：
- 检测频繁跨用户访问（可疑行为）
- 大批量数据导出告警
- 记录所有管理员查询操作

### 数据一致性

**事务管理**：
- 使用 `@transactional` 装饰器
- 保证多个任务更新的一致性
- 支持事务回滚

```python
@Transactional
async def update_task_with_subtasks(self, task_id: str, new_status: TaskStatus):
    # 更新父任务
    parent = await repository.find_by_id(task_id)
    parent.update_status(new_status)
    
    # 级联更新子任务
    subtasks = await repository.find_subtasks(task_id)
    for subtask in subtasks:
        subtask.update_status(new_status)
    
    # 全部成功才提交，否则回滚
```

**乐观锁实现**：
```python
async def update_with_optimistic_lock(self, task: TaskEntity, expected_version: int):
    result = await db.execute(
        update(Task)
        .where(Task.id == task.id, Task.version == expected_version)
        .values(**task.to_dict(), version=task.version + 1)
    )
    
    if result.rowcount == 0:
        raise OptimisticLockException("Version mismatch")
```

**重试策略**：
乐观锁冲突时的指数退避重试：
```python
async def update_with_retry(self, task_id: str, new_status: TaskStatus, max_retries=3):
    for attempt in range(max_retries):
        try:
            task = await repository.find_by_id(task_id)
            task.update_status(new_status, task.version)
            await repository.save(task)
            return
        except OptimisticLockException:
            if attempt == max_retries - 1:
                raise
            wait_time = 0.1 * (2 ** attempt)  # 100ms, 200ms, 400ms
            await asyncio.sleep(wait_time)
```

**外键约束**：
- 保证关联完整性
- 使用数据库约束保证数据有效性
- 定期检查数据一致性（后台任务）

## 技术栈

**后端框架**：
- FastAPI（API 路由）
- SQLAlchemy 2.0（ORM，async 支持）
- Pydantic v2（数据验证）
- aioredis（Redis 客户端）

**数据库**：
- PostgreSQL 15+（主存储，启用 RLS）
- Redis 7+（缓存层，可选）

**消息队列**：
- RabbitMQ 或 Redis Streams（事件总线，用于 016 集成）

**工具库**：
- Alembic（数据库迁移）
- pytest + pytest-asyncio（测试）
- cryptography（加密）

## 监控与告警

### 监控指标

**延迟指标**：
- 状态更新延迟 P95 <50ms
- 查询延迟 P95 <100ms
- 缓存命中率 >80%

**吞吐量指标**：
- 每秒任务更新数
- 每秒任务查询数
- 并发任务追踪数（≥5000）

**错误率指标**：
- 乐观锁冲突率
- 数据库连接错误率
- 权限拒绝次数

### 告警配置

**P0 告警**（立即响应）：
- 数据库不可用
- 错误率 >5%
- 平均延迟 >500ms

**P1 告警**（30 分钟内响应）：
- 缓存命中率 <50%
- 慢查询数量突增
- 乐观锁冲突率 >10%

**P2 告警**（工作时间响应）：
- 连接池使用率 >80%
- 磁盘空间 <20%
- 单个任务更新失败

## 未来演进方向

**异步任务执行**（不属于 018，由 014 负责）：
- 引入 Celery 或 ARQ 实现异步任务
- 018 仅提供持久化服务

**任务编排框架**（不属于 018）：
- 可视化任务流程设计器
- 复杂的任务编排和依赖管理
- 018 作为底层存储层

**实时执行监控**（与 016 合作）：
- 任务执行成功率统计
- 平均耗时分析
- 任务执行分析和优化建议

**任务模板功能**（未来扩展）：
- 用户可以基于模板快速创建任务
- 支持模板的参数化配置
- 018 负责存储模板数据
