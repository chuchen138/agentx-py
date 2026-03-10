# 任务管理能力 - 需求说明与场景描述

## 1. 概述

任务管理能力是 AgentX 平台的会话任务管理能力，提供对 Agent 执行过程中产生的任务（Task）的管理和追踪。主要关注单次会话内的任务生命周期，包括任务创建、执行、完成和状态管理。

### 1.1 模块定位

- **核心作用**：为会话内的任务执行提供管理能力
- **服务对象**：Agent 执行引擎、任务处理器
- **应用场景**：Agent 任务分解、任务执行追踪、任务状态管理

### 1.2 核心价值

- **任务追踪**：记录会话内的任务执行情况
- **状态管理**：提供任务生命周期的状态管理
- **进度跟踪**：记录任务执行的进度信息
- **层级管理**：支持任务和子任务的层级关系
- **结果记录**：保存任务执行的最终结果

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

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | String | 任务 ID |
| sessionId | String | 会话 ID |
| userId | String | 用户 ID |
| parentTaskId | String | 父任务 ID |
| taskName | String | 任务名称 |
| description | String | 任务描述 |
| status | TaskStatus | 任务状态 |
| progress | Integer | 任务进度（0-100） |
| startTime | LocalDateTime | 开始时间 |
| endTime | LocalDateTime | 结束时间 |
| taskResult | String | 任务结果 |
| createdAt | LocalDateTime | 创建时间 |
| updatedAt | LocalDateTime | 更新时间 |

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

```java
public class TaskAggregate {
    private TaskEntity task;
    private List<TaskEntity> subTasks;
    
    public TaskAggregate(TaskEntity task, List<TaskEntity> subTasks) {
        this.task = task;
        this.subTasks = subTasks;
    }
}
```

---

## 5. 接口定义

### 5.1 获取当前会话任务

```http
GET /api/tasks/current-session
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| sessionId | String | 是 | 会话 ID |
| userId | String | 是 | 用户 ID |

**响应数据**：

```json
{
  "task": {
    "id": "task-123",
    "taskName": "父任务",
    "status": "IN_PROGRESS",
    "progress": 50
  },
  "subTasks": [
    {
      "id": "subtask-1",
      "taskName": "子任务 1",
      "status": "COMPLETED",
      "progress": 100
   