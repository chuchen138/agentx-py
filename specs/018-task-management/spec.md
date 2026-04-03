# 任务管理能力 - 需求说明与场景描述

## 1. 概述

任务管理能力是 AgentX 平台的会话任务管理能力，提供对 Agent 执行过程中产生的任务（Task）的管理和追踪。主要关注单次会话内的任务生命周期持久化、状态存储和执行追踪。

### 1.1 模块定位

- **核心作用**：为任务/工作流提供持久化存储和状态管理（仅持久化和查询，不包含执行逻辑）
- **服务对象**：014-agent-workflow（编排引擎）、013-conversation（对话管理）
- **应用场景**：任务状态存储、执行追踪、历史记录查询

### 1.2 模块职责边界

- **013-conversation**: 对话流程控制，复杂任务委托给 014
- **014-agent-workflow**: 纯编排引擎，负责任务调度、状态机管理、任务拆分，不存储状态
- **018-task-management**: 任务/工作流持久化、状态存储、执行追踪（仅持久化层）

**重要说明**：
- 014 模块负责任务的编排逻辑（拆分、调度、依赖管理、状态机转换）
- 本模块负责将任务和工作的状态持久化到数据库，并提供查询能力
- 014 通过直接调用 018 的服务层方法（无 HTTP 开销），实现状态持久化
- 本模块**不包含**任务执行引擎、超时检测、自动重试等执行逻辑

### 1.3 核心价值

- **任务追踪**：记录会话内的任务执行情况
- **状态管理**：提供任务生命周期的状态管理
- **进度跟踪**：记录任务执行的进度信息
- **层级管理**：支持任务和子任务的层级关系
- **结果记录**：保存任务执行的最终结果

---

## 1.4 技术约束

### 1.4.1 技术栈

- **存储**：PostgreSQL（tasks 表），Redis（进度缓存，可选）
- **ORM**：SQLAlchemy（支持 async）
- **API 框架**：FastAPI（内部服务调用，非 HTTP）
- **调用方式**：同步方法调用（014 直接调用 018 服务层）

### 1.4.2 性能要求

- **状态更新延迟**：<50ms (P95)
- **查询当前会话任务**：<100ms (P95)
- **并发任务追踪**：≥5000 个任务（跨所有会话）
- **进度更新吞吐量**：≥1000 次更新/秒

### 1.4.3 安全要求

- **访问控制**：所有查询必须强制过滤 `user_id` + `session_id`
- **数据隔离**：PostgreSQL 行级安全策略（RLS）
- **敏感数据**：包含 PII 的任务结果必须加密存储
- **审计日志**：记录任务创建/状态变更（谁、何时、什么操作）

---

## 2. 核心能力

### 2.1 任务管理

任务管理是核心功能，提供对任务的 CRUD 操作。

#### 功能描述

- **任务查询**：查询当前会话的任务信息
- **任务状态更新**：更新任务的执行状态
- **任务结果记录**：保存任务执行的结果
- **任务进度跟踪**：记录任务的执行进度

#### 关键数据

**TaskDTO（任务数据传输对象）**

- `id`：任务 ID
- `sessionId`：会话 ID
- `userId`：用户 ID
- `parentTaskId`：父任务 ID
- `taskName`：任务名称
- `description`：任务描述
- `status`：任务状态
- `progress`：任务进度
- `startTime`：开始时间
- `endTime`：结束时间
- `taskResult`：任务结果
- `createdAt`：创建时间
- `updatedAt`：更新时间

---

### 2.2 任务状态管理

任务状态管理是任务管理的核心，定义了任务的生命周期。

#### 功能描述

- **状态转换**：管理任务状态的转换
- **自动状态更新**：根据任务执行自动更新状态
- **开始时间记录**：任务开始时记录开始时间
- **结束时间记录**：任务完成或失败时记录结束时间

#### 任务状态（TaskStatus）

**WAITING（等待中）**

- 任务已创建，等待执行

**IN_PROGRESS（进行中）**

- 任务正在执行

**COMPLETED（已完成）**

- 任务执行成功完成

**FAILED（失败）**

- 任务执行失败

---

### 2.3 任务层级管理

支持任务层级关系，一个任务可以有多个子任务。

#### 功能描述

- **父任务创建**：创建父任务
- **子任务管理**：为父任务创建子任务
- **任务关联**：通过 parentTaskId 建立任务间的层级关系

#### 任务层级关系

```
父任务（Parent Task）
    ├── 子任务 1（Subtask 1）
    ├── 子任务 2（Subtask 2）
    └── 子任务 3（Subtask 3）
```

---

### 2.4 会话任务查询

提供基于会话的任务查询能力。

#### 功能描述

- **当前会话任务查询**：获取当前会话的最新任务
- **任务列表查询**：查询会话的所有任务
- **任务详情查询**：获取单个任务的详细信息

---

## 3. 核心场景

### 3.1 Agent 任务分解

Agent 在执行过程中将复杂任务分解为多个子任务。

**场景描述**：

1. 用户发起一个复杂的 Agent 请求
2. Agent 分析需求，识别需要多个步骤
3. Agent 创建一个父任务
4. 根据需求分解出多个子任务
5. 设置子任务的状态为 WAITING
6. 依次执行子任务
7. 子任务完成后，更新父任务状态

**关键业务规则**：

- 父任务的状态由子任务决定
- 所有子任务完成后，父任务才完成
- 子任务独立管理自己的状态

### 3.2 任务执行状态跟踪

在 Agent 执行过程中，跟踪每个任务的执行状态。

**场景描述**：

1. Agent 开始执行一个任务
2. 任务状态更新为 IN_PROGRESS
3. 记录任务开始时间
4. 任务执行过程中，更新任务进度
5. 任务完成后，状态更新为 COMPLETED
6. 记录任务结束时间和结果

**关键业务规则**：

- 任务开始时自动设置开始时间
- 任务完成时自动设置结束时间
- 最终状态决定结束时间的记录

### 3.3 任务失败处理

任务执行失败时的处理流程。

**场景描述**：

1. 任务执行过程中发生异常
2. 任务状态更新为 FAILED
3. 记录任务结束时间
4. 记录错误信息（如果有）
5. Agent 根据失败情况决定是否重试或终止

**关键业务规则**：

- 失败任务不自动重试（由业务逻辑决定）
- 失败信息记录在任务结果中
- 父任务可能因为子任务失败而失败

### 3.4 查询当前会话任务

用户和 Agent 查询当前会话的任务信息。

**场景描述**：

1. Agent 执行过程中需要查询当前任务
2. 调用接口获取当前会话的 TaskAggregate
3. 获取最新创建的任务及所有子任务
4. 根据任务信息决定下一步操作

**关键业务规则**：

- 返回的是最新创建的任务
- 包含完整的任务层级关系
- 支持任务状态的实时跟踪

---

## 4. 数据模型

### 4.1 TaskEntity

任务实体类，定义任务的基本结构。

| 字段名 | 类型 | 说明 | 约束 |
|-------|------|------|------|
| id | String | 任务 ID | UUID, 主键 |
| session_id | String | 会话 ID | 外键，索引 |
| user_id | String | 用户 ID | 外键，索引 |
| parent_task_id | String | 父任务 ID | 外键，索引，可空 |
| task_name | String | 任务名称 | 最大 256 字符 |
| description | String | 任务描述 | 最大 4096 字符 |
| status | TaskStatus | 任务状态 | 索引 |
| progress | Integer | 任务进度（0-100） | 默认 0 |
| start_time | LocalDateTime | 开始时间 | 可空 |
| end_time | LocalDateTime | 结束时间 | 可空 |
| task_result | String | 任务结果 | 最大 65535 字符 |
| version | Long | 版本号 | 乐观锁，默认 0 |
| deleted_at | LocalDateTime | 删除时间 | 软删除，可空 |
| created_at | LocalDateTime | 创建时间 | 默认当前时间 |
| updated_at | LocalDateTime | 更新时间 | 自动更新 |

**索引设计**：
- `idx_session_created`: (session_id, created_at DESC) - 查询会话最新任务
- `idx_user_status`: (user_id, status) - 按用户和状态查询
- `idx_parent_task`: (parent_task_id) - 查询子任务
- `idx_deleted_at`: (deleted_at) - 软删除过滤

### 4.2 TaskStatus

任务状态枚举，定义任务的生命周期状态。

| 状态 | 说明 |
|------|------|
| WAITING | 等待中 |
| IN_PROGRESS | 进行中 |
| COMPLETED | 已完成 |
| FAILED | 失败 |

### 4.3 TaskAggregate

任务聚合根，包含任务和子任务的整体信息。

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

---

## 5. 失败处理规则

### 5.1 超时处理

- **责任模块**：超时检测由 014-agent-workflow 负责
- **018 职责**：仅记录超时后的状态变更（FAILED）
- **结果截断**：任务结果超过 65535 字符时自动截断并标记

### 5.2 孤儿任务处理

- **场景**：父任务被删除后，子任务成为孤儿任务
- **处理策略**：级联软删除（子任务 deleted_at 同步设置）
- **查询过滤**：默认查询自动排除已软删除的任务

### 5.3 事务回滚

- **约束违反**：外键约束、唯一约束违反时立即回滚
- **乐观锁冲突**：version 不匹配时抛出 OptimisticLockException
- **错误传递**：数据访问异常传递给调用方（014）处理

---

## 6. 接口定义

### 6.1 获取当前会话任务

```http
GET /api/v1/tasks/current-session
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| session_id | String | 是 | 会话 ID |
| user_id | String | 是 | 用户 ID |
| include_deleted | Boolean | 否 | 是否包含已删除（默认 false） |

**响应数据**：

```json
{
  "task": {
    "id": "task-123",
    "session_id": "session-456",
    "user_id": "user-789",
    "parent_task_id": null,
    "task_name": "父任务",
    "description": "任务描述",
    "status": "IN_PROGRESS",
    "progress": 50,
    "start_time": "2026-03-14T10:00:00Z",
    "end_time": null,
    "task_result": null,
    "version": 1,
    "created_at": "2026-03-14T09:00:00Z",
    "updated_at": "2026-03-14T10:00:00Z"
  },
  "sub_tasks": [
    {
      "id": "subtask-1",
      "session_id": "session-456",
      "user_id": "user-789",
      "parent_task_id": "task-123",
      "task_name": "子任务 1",
      "description": null,
      "status": "COMPLETED",
      "progress": 100,
      "start_time": "2026-03-14T10:10:00Z",
      "end_time": "2026-03-14T10:20:00Z",
      "task_result": "子任务 1 完成",
      "version": 2,
      "created_at": "2026-03-14T09:10:00Z",
      "updated_at": "2026-03-14T10:20:00Z"
    }
  ]
}
```

### 6.2 查询任务列表（支持过滤和分页）

```http
GET /api/v1/tasks/query
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| user_id | String | 是 | 用户 ID |
| session_id | String | 否 | 会话 ID 过滤 |
| status | String | 否 | 状态过滤 |
| offset | Integer | 否 | 偏移量（默认 0） |
| limit | Integer | 否 | 每页数量（默认 20） |

**响应数据**：

```json
{
  "tasks": [
    {
      "id": "task-123",
      "session_id": "session-456",
      "user_id": "user-789",
      "parent_task_id": null,
      "task_name": "任务名称",
      "description": "任务描述",
      "status": "COMPLETED",
      "progress": 100,
      "start_time": "2026-03-14T10:00:00Z",
      "end_time": "2026-03-14T10:30:00Z",
      "task_result": "任务完成",
      "version": 2,
      "created_at": "2026-03-14T09:00:00Z",
      "updated_at": "2026-03-14T10:30:00Z"
    }
  ],
  "total": 150,
  "offset": 0,
  "limit": 20
}
```

### 6.3 更新任务状态

```http
PATCH /api/v1/tasks/{task_id}/status
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| user_id | String | 是 | 用户 ID（权限验证） |
| status | TaskStatus | 是 | 新状态 |
| version | Integer | 是 | 期望版本号（乐观锁检查） |
| progress | Integer | 否 | 新进度（可选） |
| task_result | String | 否 | 任务结果（可选） |

**成功响应**：200 OK

**失败响应**：
- 404 Not Found: 任务不存在
- 403 Forbidden: 无权访问该任务（user_id 不匹配）
- 400 Bad Request: 参数错误
- 500 Internal Server Error: 服务器内部错误

### 6.4 创建任务

```http
POST /api/v1/tasks/
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| session_id | String | 是 | 会话 ID |
| user_id | String | 是 | 用户 ID |
| task_name | String | 是 | 任务名称 |
| description | String | 否 | 任务描述 |
| parent_task_id | String | 否 | 父任务 ID |

**成功响应**：200 OK

### 6.5 更新任务进度

```http
PATCH /api/v1/tasks/{task_id}/progress
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| user_id | String | 是 | 用户 ID |
| progress | Integer | 是 | 新进度（0-100） |

**成功响应**：200 OK

### 6.6 删除任务

```http
DELETE /api/v1/tasks/{task_id}
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| user_id | String | 是 | 用户 ID |

**成功响应**：200 OK

**失败响应**：
- 404 Not Found: 任务不存在
- 403 Forbidden: 无权访问该任务（user_id 不匹配）
   