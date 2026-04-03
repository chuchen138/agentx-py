# 定时任务技术设计

## 概述

定时任务能力采用分层架构设计，遵循领域驱动设计（DDD）原则，提供灵活的定时任务创建、调度和执行能力。基于 Python + FastAPI + APScheduler/Celery + Redis + Docker 技术栈实现。

## 技术架构

### 架构分层

**接口层（Interface Layer）**
- 职责：处理 HTTP 请求，参数校验，响应返回
- 组件：FastAPI Router, Pydantic DTO/Schema
- 关键实现：
  - [app/api/v1/scheduledtask/routes.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py)
  - [app/api/v1/scheduledtask/__init__.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/__init__.py)

**应用层（Application Layer）**
- 职责：业务流程编排，DTO 转换，事务管理
- 组件：ScheduledTaskAppService, TaskValidator, TaskAssembler
- 关键实现：
  - [app/application/scheduledtask/service.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/service.py)
  - [app/application/scheduledtask/validator.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/validator.py)
  - [app/application/scheduledtask/assembler.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/assembler.py)
  - [app/application/scheduledtask/__init__.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/__init__.py)

**领域层（Domain Layer）**
- 职责：核心业务逻辑，实体模型，领域服务
- 组件：ScheduledTaskEntity, RepeatConfig, ScheduledTaskDomainService, TaskScheduleService, ScheduledTaskExecutionService, ScheduleTaskExecutor
- 关键实现：
  - [app/domain/scheduledtask/model.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/model.py) - 实体定义
  - [app/domain/scheduledtask/schemas.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/schemas.py) - DTO/Schema
  - [app/domain/scheduledtask/service.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/service.py) - 领域服务
  - [app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py) - 执行服务
  - [app/domain/scheduledtask/repository.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/repository.py) - 仓储接口
  - [app/domain/scheduledtask/constant/repeat_type.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/repeat_type.py) - 重复类型枚举
  - [app/domain/scheduledtask/constant/task_status.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/task_status.py) - 任务状态枚举
  - [app/domain/scheduledtask/constant/__init__.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/__init__.py)
  - [app/domain/scheduledtask/__init__.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/__init__.py)

**基础设施层（Infrastructure Layer）**
- 职责：数据持久化，外部系统集成，技术中间件
- 组件：ScheduledTaskRepository (SQLAlchemy), Redis Queue, Docker Sandbox, Distributed Lock
- 关键实现：
  - [app/infrastructure/distributed_lock.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/infrastructure/distributed_lock.py) - 分布式锁实现

**数据库迁移**
- [alembic/versions/007_create_scheduled_task_tables.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/alembic/versions/007_create_scheduled_task_tables.py)

### 核心组件

**ScheduledTaskAppService**
- 职责：定时任务业务流程编排
- 方法：create_task, update_task, delete_task, get_task_list, get_task_detail, pause_task, resume_task, trigger_task_manually
- 依赖：ScheduledTaskDomainService, TaskValidator, TaskAssembler
- 文件：[app/application/scheduledtask/service.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/service.py)

**TaskScheduleService**
- 职责：任务调度时间计算，调度器管理
- 方法：calculate_next_execute_time, validate_repeat_config
- 调度器选择：
  - 单实例：APScheduler with PersistentJobStore (Redis)
  - 分布式：Celery Beat + Redis Broker
- 依赖：APScheduler, croniter
- 文件：[app/domain/scheduledtask/service.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/service.py)

**ScheduledTaskExecutionService**
- 职责：任务执行管理，分布式锁，重试机制
- 方法：execute_task, handle_retry, handle_timeout, record_execution_log
- 依赖：DistributedLock, TaskSandbox, ExecutionLogger
- 文件：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

**ScheduleTaskExecutor**
- 职责：实际执行任务，触发 Agent，状态更新
- 方法：execute
- 执行模式：
  - 普通模式：直接调用 Agent API
  - 沙箱模式：创建 Docker 容器执行
- 文件：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

**TaskValidator**
- 职责：任务内容校验，敏感词过滤
- 方法：validate_content, validate_repeat_config, validate_resource_quota, sanitize_content
- 文件：[app/application/scheduledtask/validator.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/validator.py)

**DistributedLock**
- 职责：分布式环境防重复执行
- 方法：acquire, release, extend
- 实现：Redis SETNX + Watchdog
- 文件：[app/infrastructure/distributed_lock.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/infrastructure/distributed_lock.py)

## API 端点

| 方法 | 端点 | 描述 | 文件 |
|------|------|------|------|
| POST | `/api/v1/scheduled-tasks` | 创建定时任务 | [routes.py#L31](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L31) |
| GET | `/api/v1/scheduled-tasks` | 获取任务列表 | [routes.py#L54](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L54) |
| GET | `/api/v1/scheduled-tasks/{id}` | 获取任务详情 | [routes.py#L72](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L72) |
| PUT | `/api/v1/scheduled-tasks/{id}` | 更新定时任务 | [routes.py#L89](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L89) |
| DELETE | `/api/v1/scheduled-tasks/{id}` | 删除定时任务 | [routes.py#L116](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L116) |
| POST | `/api/v1/scheduled-tasks/{id}/pause` | 暂停任务 | [routes.py#L137](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L137) |
| POST | `/api/v1/scheduled-tasks/{id}/resume` | 恢复任务 | [routes.py#L159](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L159) |
| POST | `/api/v1/scheduled-tasks/{id}/trigger` | 手动触发执行 | [routes.py#L181](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L181) |
| GET | `/api/v1/scheduled-tasks/{id}/execution-logs` | 获取执行历史 | [routes.py#L203](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/api/v1/scheduledtask/routes.py#L203) |

## 核心设计

### 任务实体和枚举

**ScheduledTask 实体**
- 文件：[app/domain/scheduledtask/model.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/model.py)

```python
class ScheduledTask(Base):
    __tablename__ = 'scheduled_tasks'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), nullable=False, index=True)
    agent_id = Column(String(36), nullable=False, index=True)
    session_id = Column(String(36), nullable=False, index=True)
    content = Column(String(10000), nullable=False)
    repeat_type = Column(Enum(RepeatType), nullable=False)
    repeat_config = Column(JSON, nullable=False)
    status = Column(Enum(ScheduleTaskStatus), nullable=False, default=ScheduleTaskStatus.PENDING)
    last_execute_time = Column(DateTime, nullable=True)
    next_execute_time = Column(DateTime, nullable=False, index=True)
    max_retry_count = Column(Integer, default=3)
    timeout_minutes = Column(Integer, default=30)
    last_error = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    notify_on_failure = Column(Boolean, default=True)
    docker_image = Column(String(255), default='agentx/task-sandbox:latest')
    resource_quota = Column(JSON, default={'cpu_limit': 1.0, 'memory_limit': '512M'})
    version = Column(Integer, default=0)  # 乐观锁
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

**RepeatType 枚举**
- 文件：[app/domain/scheduledtask/constant/repeat_type.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/repeat_type.py)

```python
class RepeatType(str, Enum):
    IMMEDIATE = "immediate"      # 立即执行
    INTERVAL = "interval"        # 间隔重复
    DAILY = "daily"              # 每日重复
    WEEKLY = "weekly"            # 每周重复
    CUSTOM = "custom"            # 自定义 Cron
```

**ScheduleTaskStatus 枚举**
- 文件：[app/domain/scheduledtask/constant/task_status.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/task_status.py)

```python
class ScheduleTaskStatus(str, Enum):
    PENDING = "pending"          # 待执行
    RUNNING = "running"          # 执行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 执行失败
    PAUSED = "paused"            # 已暂停
```

### 重复配置和执行时间计算

**RepeatConfig Schema**
- 文件：[app/domain/scheduledtask/schemas.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/schemas.py)

```python
class RepeatConfigSchema(BaseModel):
    interval_hours: Optional[int] = None        # INTERVAL 类型使用
    execute_time: Optional[str] = None          # DAILY/WEEKLY 类型使用，格式 HH:mm
    week_days: Optional[List[int]] = None       # WEEKLY 类型使用，[1,2,3,4,5,6,7]
    cron_expression: Optional[str] = None       # CUSTOM 类型使用
```

**TaskScheduleService 时间计算逻辑**
- 文件：[app/domain/scheduledtask/service.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/service.py)

```python
class TaskScheduleService:
    def calculate_next_execute_time(self, task: ScheduledTask, base_time: datetime = None) -> datetime:
        base_time = base_time or datetime.utcnow()
        
        if task.repeat_type == RepeatType.INTERVAL:
            return base_time + timedelta(hours=task.repeat_config.interval_hours)
        
        elif task.repeat_type == RepeatType.DAILY:
            next_time = base_time.replace(
                hour=int(task.repeat_config.execute_time.split(':')[0]),
                minute=int(task.repeat_config.execute_time.split(':')[1]),
                second=0, microsecond=0
            )
            if next_time <= base_time:
                next_time += timedelta(days=1)
            return next_time
        
        elif task.repeat_type == RepeatType.WEEKLY:
            current_weekday = base_time.isoweekday()
            target_days = sorted(task.repeat_config.week_days)
            days_ahead = min((d - current_weekday) % 7 for d in target_days)
            if days_ahead == 0 and base_time.hour >= int(task.repeat_config.execute_time.split(':')[0]):
                days_ahead = 7
            next_time = base_time + timedelta(days=days_ahead)
            next_time = next_time.replace(
                hour=int(task.repeat_config.execute_time.split(':')[0]),
                minute=int(task.repeat_config.execute_time.split(':')[1]),
                second=0, microsecond=0
            )
            return next_time
        
        elif task.repeat_type == RepeatType.CUSTOM:
            cron = croniter(task.repeat_config.cron_expression, base_time)
            return cron.get_next(datetime)
```

### 任务调度和执行

**分布式锁实现**
- 文件：[app/infrastructure/distributed_lock.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/infrastructure/distributed_lock.py)

```python
class DistributedLock:
    def __init__(self, lock_key: str, timeout: int = 300, redis_client=None):
        self.lock_key = f"distributed_lock:{lock_key}"
        self.timeout = timeout
        self.token = str(uuid.uuid4())
        self.redis = redis_client
        self._locked = False
    
    def acquire(self, blocking: bool = True, blocking_timeout: int = 10) -> bool:
        """尝试获取锁，blocking=False 表示非阻塞"""
        if not self.redis:
            return True
        acquired = self.redis.set(
            self.lock_key,
            self.token,
            nx=True,  # 仅当不存在时设置
            ex=self.timeout
        )
        if acquired:
            self._locked = True
        return bool(acquired)
    
    def release(self) -> bool:
        """释放锁（Lua 脚本保证原子性）"""
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = self.redis.eval(lua_script, 1, self.lock_key, self.token)
        if result:
            self._locked = False
        return bool(result)
```

### 数据持久化

**数据库表结构**
- 迁移文件：[alembic/versions/007_create_scheduled_task_tables.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/alembic/versions/007_create_scheduled_task_tables.py)

```sql
CREATE TABLE scheduled_tasks (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL,
    agent_id VARCHAR(36) NOT NULL,
    session_id VARCHAR(36) NOT NULL,
    content VARCHAR(10000) NOT NULL,
    repeat_type VARCHAR(20) NOT NULL,
    repeat_config JSON NOT NULL,
    status VARCHAR(20) NOT NULL,
    last_execute_time DATETIME,
    next_execute_time DATETIME NOT NULL,
    max_retry_count INT DEFAULT 3,
    timeout_minutes INT DEFAULT 30,
    last_error TEXT,
    retry_count INT DEFAULT 0,
    notify_on_failure BOOLEAN DEFAULT TRUE,
    docker_image VARCHAR(255),
    resource_quota JSON,
    version INT DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_agent_id (agent_id),
    INDEX idx_session_id (session_id),
    INDEX idx_next_execute_time (next_execute_time),
    INDEX idx_status (status)
);

CREATE TABLE task_execution_logs (
    id VARCHAR(36) PRIMARY KEY,
    task_id VARCHAR(36) NOT NULL,
    execute_time DATETIME NOT NULL,
    status VARCHAR(20) NOT NULL,
    result TEXT,
    error_message TEXT,
    duration BIGINT,  -- milliseconds
    container_id VARCHAR(64),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task_id (task_id),
    INDEX idx_execute_time (execute_time)
);
```

## 关键设计决策

**调度器选型**
- 单实例场景：APScheduler，轻量级，与 FastAPI 集成简单
- 分布式场景：Celery Beat + Redis，支持任务去重、故障转移、负载均衡
- 不推荐 Django-Cron：项目未使用 Django 框架

**幂等性保证**
- 幂等 key 生成：`idem_key = f"idem:{task_id}:{int(execute_time.timestamp())}"`
- 实现方式：Redis SETNX + 数据库唯一约束
- 过期时间：执行时间 + 2 倍超时时间
- 文件：[app/infrastructure/distributed_lock.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/infrastructure/distributed_lock.py)

**超时处理**
- 软超时：达到超时时间的 80% 时发送警告
- 硬超时：达到超时时间后强制终止（Docker 容器 kill / subprocess.terminate）
- 超时任务状态：标记为 FAILED，记录超时错误
- 文件：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

**重试策略**
- 重试条件：网络异常、数据库连接失败、Agent 暂时不可用
- 不重试：权限错误、输入校验失败、业务逻辑错误
- 退避算法：1分钟、5分钟、15分钟
- 文件：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

## 性能优化

**调度性能**
- 批量注册：支持一次注册多个任务（减少 Redis IO）
- 懒加载：仅在任务到期前 5 分钟加载到内存调度器
- 分级存储：近期任务存 Redis，远期任务存 MySQL

**并发控制**
- 线程池：ThreadPoolExecutor(max_workers=50)
- 信号量：限制同一 Agent 的并发任务数（防止过载）
- 队列限流：Redis 队列长度超过阈值时拒绝新任务

**索引优化**
- 常用查询字段建索引：user_id, next_execute_time, status
- 覆盖索引：(user_id, status) 组合索引
- 定期清理：执行日志归档到历史表（>90 天）

## 扩展性设计

**新增重复类型步骤**
1. 在 [RepeatType 枚举](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/constant/repeat_type.py) 中添加新值
2. 在 [RepeatConfigSchema](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/schemas.py) 中添加对应配置字段
3. 在 [TaskScheduleService.calculate_next_execute_time](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/service.py) 中添加计算逻辑
4. 在前端添加 UI 支持

**自定义执行器**
```python
class CustomTaskExecutor(TaskExecutor):
    async def execute(self, task: ScheduledTask) -> Dict[str, Any]:
        # 自定义执行逻辑
        # 例如：调用外部系统、执行特定工作流
        pass
```
- 基类定义：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

## 集成与安全

### 模块集成

**与 013/014 Agent 执行集成**
- 上下文传递：任务触发时使用 task.session_id 创建会话上下文
- 参数注入：在 task.content 中替换 `{{scheduled_task_id}}` 等变量
- 执行追踪：生成 trace_id 关联到 016 执行追踪模块
- Agent 执行器：[app/domain/scheduledtask/executor.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/executor.py)

**与 006 容器管理集成**
- 复用容器创建逻辑（TaskSandbox 委托给 ContainerManagementService）
- 共享容器镜像仓库
- 统一资源配额管理

**与 019 计费集成**
- 每次执行记录计费事件：source_type="scheduled_task", source_id=task.id
- 支持按任务维度统计成本
- 计费项：Token 消耗 + 执行时长

### 安全设计

**输入校验**
- 文件：[app/application/scheduledtask/validator.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/application/scheduledtask/validator.py)

```python
class TaskValidator:
    CONTENT_MAX_LENGTH = 10000
    SENSITIVE_PATTERNS = [
        r'\bimport\s+os\b',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\b__import__\s*\(',
    ]
    SENSITIVE_WORDS = ['password', 'secret', 'token', 'apikey']
    
    @classmethod
    def validate_content(cls, content: str) -> Tuple[bool, str]:
        if len(content) > cls.CONTENT_MAX_LENGTH:
            return False, f'Content exceeds maximum length of {cls.CONTENT_MAX_LENGTH}'
        
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, content, re.IGNORECASE):
                return False, 'Content contains prohibited executable code'
        
        return True, ""
    
    @classmethod
    def sanitize_content(cls, content: str) -> str:
        for word in cls.SENSITIVE_WORDS:
            content = re.sub(rf'\b{word}\s*=\s*\S+', f'{word}=[REDACTED]', content, flags=re.IGNORECASE)
        return content
```

**权限隔离**
- 用户只能访问自己的任务（所有查询添加 user_id 过滤）
- RBAC 扩展：管理员可查看所有任务，普通用户仅查看自己创建的任务
- 操作审计：记录所有任务的创建/修改/删除操作日志

**沙箱隔离**
- 强制 Docker 容器执行（生产环境）
- 禁用容器网络访问
- 只读文件系统 + 临时目录隔离
- 资源配额限制（CPU/内存）

### 数据一致性

**事务管理**
- 使用 SQLAlchemy 会话管理事务
- 任务状态更新 + 执行日志记录在同一事务中
- 异常时自动回滚

**乐观锁**
- 使用 version 字段控制并发更新
- UPDATE 时检查 version 匹配
- 冲突时抛出 OptimisticConcurrencyError
- 实现：[app/domain/scheduledtask/repository.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/domain/scheduledtask/repository.py)

**幂等记录**
- 文件：[app/infrastructure/distributed_lock.py](file:///c:/Users/SXF-Admin/Documents/platform/code/agentx-py/app/infrastructure/distributed_lock.py)

```python
class IdempotencyManager:
    def check_and_set(self, task_id: str, execute_time: datetime, expire_seconds: int = 7200) -> bool:
        key = f"idem:{task_id}:{int(execute_time.timestamp())}"
        return bool(self.redis.set(key, '1', nx=True, ex=expire_seconds))
```

## 监控告警

**监控指标（Prometheus）**
```python
from prometheus_client import Counter, Histogram, Gauge

TASK_EXECUTION_TOTAL = Counter('scheduled_task_execution_total', 'Total task executions', ['task_id', 'status'])
TASK_EXECUTION_DURATION = Histogram('scheduled_task_execution_duration_seconds', 'Task execution duration')
TASK_QUEUE_SIZE = Gauge('scheduled_task_queue_size', 'Number of pending tasks')
TASK_FAILURE_STREAK = Gauge('scheduled_task_failure_streak', 'Consecutive failures per task', ['task_id'])
```

**告警规则（AlertManager）**
```yaml
groups:
  - name: scheduled_tasks
    rules:
      - alert: HighTaskFailureRate
        expr: rate(scheduled_task_execution_total{status="failed"}[5m]) > 0.1
        annotations:
          summary: "高任务失败率"
      
      - alert: TaskQueueBacklog
        expr: scheduled_task_queue_size > 100
        annotations:
          summary: "任务队列积压"
      
      - alert: ConsecutiveFailures
        expr: scheduled_task_failure_streak >= 3
        annotations:
          summary: "任务连续失败"
```

## 技术栈总结

**核心框架**
- Web 框架：FastAPI >= 0.100
- 调度引擎：APScheduler >= 3.9 或 Celery >= 5.3
- ORM：SQLAlchemy >= 2.0
- 验证：Pydantic >= 2.0

**中间件**
- 数据库：MySQL 8.0 / PostgreSQL 15
- 缓存/队列：Redis >= 7.0
- 容器：Docker >= 24.0

**监控**
- 指标：Prometheus + Grafana
- 告警：AlertManager
- 日志：ELK Stack / Loki

**测试**
- 单元测试：pytest + pytest-asyncio
- 集成测试：FastAPI TestClient + pytest
- Mock：unittest.mock + fakeredis
