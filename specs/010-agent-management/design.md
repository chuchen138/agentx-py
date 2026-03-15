# 智能体管理技术设计

## 概述

本文档描述智能体管理模块的技术设计方案。模块基于领域驱动设计（DDD）分层架构，采用 Python + FastAPI + SQLAlchemy 技术栈，实现 Agent 全生命周期管理、版本控制、Widget 配置、工作空间管理等核心功能。

## 技术架构

### 技术栈选型

- **Web 框架**：FastAPI（异步高性能）
- **ORM 框架**：SQLAlchemy 2.0（异步模式）
- **数据验证**：Pydantic v2
- **数据库**：PostgreSQL 14+
- **缓存**：Redis 6+
- **消息队列**：RabbitMQ / Redis Streams（异步通知和日志）
- **认证**：JWT（PyJWT 库）
- **密码加密**：bcrypt

### 架构分层

系统采用经典的分层架构：

```
┌─────────────────────────────────────────┐
│         Interfaces Layer                │
│   (API Routes, WebSocket, Events)       │
├─────────────────────────────────────────┤
│         Application Layer               │
│   (App Services, DTOs, Assemblers)      │
├─────────────────────────────────────────┤
│           Domain Layer                  │
│   (Entities, Value Objects, Repositories,
│    Domain Services, Business Rules)     │
├─────────────────────────────────────────┤
│      Infrastructure Layer               │
│   (Repository Implementations, Database,
│    Cache, Message Queue, External APIs) │
└─────────────────────────────────────────┘
```

**各层职责**：

- **Interfaces Layer**：处理外部请求（HTTP API、WebSocket），参数校验，身份认证，响应格式化
- **Application Layer**：编排业务流程，调用领域服务，DTO 转换，事务管理
- **Domain Layer**：封装核心业务逻辑，定义领域模型和业务规则，不依赖外部依赖
- **Infrastructure Layer**：提供技术实现（数据库持久化、缓存、消息队列、第三方 API 集成）

## 领域模型设计

### 聚合与聚合根

智能体管理模块包含三个主要聚合：

1. **Agent 聚合**（聚合根：AgentEntity）
   - 管理 Agent 基本信息、能力配置、状态
   - 包含多个版本实体
   - 包含多个 Widget 实体

2. **Version 聚合**（聚合根：AgentVersionEntity）
   - 管理版本快照、发布状态、审核流程
   - 作为 Agent 的子聚合

3. **Workspace 聚合**（聚合根：WorkspaceAgentEntity）
   - 管理工作空间中的 Agent 列表
   - 管理个性化的 LLM 模型配置

### 核心领域实体

#### AgentEntity（聚合根）

**职责**：智能体的核心领域模型，封装 Agent 的基本信息和能力配置

**属性**：
- `id`: str - 全局唯一 ID（UUID 格式）
- `user_id`: str - 创建者用户 ID
- `name`: str - Agent 名称（必填，长度限制 1-50 字符）
- `description`: str - 描述信息（可选，最大 500 字符）
- `avatar_url`: str - 头像 URL（可选）
- `system_prompt`: str - 系统提示词（可选，最大 8000 token）
- `welcome_message`: str - 欢迎消息（可选，最大 500 字符）
- `tool_ids`: List[str] - 关联的工具 ID 列表
- `knowledge_base_ids`: List[str] - 关联的知识库 ID 列表
- `tool_preset_params`: Dict[str, Any] - 工具预设参数（JSON 结构）
- `current_version_id`: Optional[str] - 当前发布的版本 ID
- `enabled`: bool - 是否启用（默认 True）
- `support_multimodal`: bool - 是否支持多模态（默认 False）
- `created_at`: datetime - 创建时间
- `updated_at`: datetime - 最后更新时间

**业务规则**：
- 名称在用户维度内必须唯一
- 工具和知识库的引用需要验证访问权限
- 删除时需要检查是否存在已发布版本
- 禁用状态下不允许被添加到工作空间

**行为方法**：
- `add_tool(tool_id: str)` - 添加工具（需验证权限）
- `remove_tool(tool_id: str)` - 移除工具
- `add_knowledge_base(kb_id: str)` - 添加知识库（需验证权限）
- `remove_knowledge_base(kb_id: str)` - 移除知识库
- `enable()` - 启用 Agent
- `disable()` - 禁用 Agent
- `create_snapshot()` - 创建当前配置的快照（用于版本发布）

#### AgentVersionEntity（实体）

**职责**：记录 Agent 的版本信息和发布状态

**属性**：
- `id`: str - 版本唯一 ID
- `agent_id`: str - 所属 Agent ID
- `version_number`: str - 版本号（语义化版本，如 1.0.0）
- `agent_name_snapshot`: str - Agent 名称快照
- `system_prompt_snapshot`: str - 系统提示词快照
- `tool_ids_snapshot`: List[str] - 工具列表快照
- `knowledge_base_ids_snapshot`: List[str] - 知识库列表快照
- `change_log`: str - 变更日志
- `publish_status`: PublishStatusEnum - 发布状态（REVIEWING/PUBLISHED/REJECTED/REMOVED）
- `review_rejection_reason`: Optional[str] - 审核拒绝原因
- `reviewer_id`: Optional[str] - 审核人 ID
- `published_at`: Optional[datetime] - 发布时间
- `created_at`: datetime - 创建时间

**发布状态枚举**：
```python
class PublishStatusEnum(str, Enum):
    REVIEWING = "REVIEWING"      # 审核中
    PUBLISHED = "PUBLISHED"      # 已发布
    REJECTED = "REJECTED"        # 已拒绝
    REMOVED = "REMOVED"          # 已下架
```

**业务规则**：
- 版本号在同一 Agent 下必须唯一且严格递增
- 审核通过后才能上架到市场
- 被拒绝的版本需要修改后重新提交
- 已下架的版本从市场隐藏

#### AgentWidgetEntity（实体）

**职责**：管理 Widget 配置和访问控制

**属性**：
- `id`: str - Widget 唯一 ID
- `agent_id`: str - 所属 Agent ID
- `public_id`: str - 公开访问 ID（全局唯一，用于嵌入）
- `name`: str - Widget 名称
- `widget_type`: WidgetTypeEnum - Widget 类型（AGENT/RAG）
- `model_id`: str - 使用的 LLM 模型 ID
- `model_provider`: str - 模型提供商
- `allowed_domains`: List[str] - 允许的域名列表（JSON 存储）
- `daily_call_limit`: int - 每日调用次数限制（-1 表示无限制）
- `enabled`: bool - 是否启用
- `embed_code`: str - 自动生成的嵌入代码
- `created_at`: datetime - 创建时间
- `updated_at`: datetime - 更新时间

**Widget 类型枚举**：
```python
class WidgetTypeEnum(str, Enum):
    AGENT = "AGENT"  # Agent 类型，使用完整工具流程
    RAG = "RAG"      # RAG 类型，直接使用 RAG 对话流程
```

**业务规则**：
- Public ID 全局唯一，随机生成（16 位字母数字组合）
- 域名白名单为空时表示允许所有域名
- 达到每日调用限制后拒绝新请求
- 禁用状态下无法被访问

#### WorkspaceAgentEntity（实体）

**职责**：管理工作空间中的 Agent

**属性**：
- `id`: str - 唯一 ID
- `user_id`: str - 用户 ID
- `agent_id`: str - Agent ID（可以是自己或他人的已发布 Agent）
- `custom_name`: Optional[str] - 自定义名称（可选，覆盖原名称）
- `added_at`: datetime - 添加时间

**业务规则**：
- 同一用户不能重复添加同一 Agent
- 只能添加已发布的他人 Agent
- 删除原 Agent 不影响工作空间记录（保留引用）

#### LLMModelConfig（值对象）

**职责**：LLM 模型配置参数

**属性**：
- `model_id`: str - 模型 ID
- `provider`: str - 模型提供商
- `temperature`: float - 温度参数（0-2，默认 0.7）
- `top_p`: float - Top P 参数（0-1，默认 0.7）
- `top_k`: int - Top K 参数（默认 50）
- `max_tokens`: Optional[int] - 最大 Token 数
- `strategy_type`: TokenOverflowStrategyEnum - Token 溢出策略
- `reserve_ratio`: Optional[float] - 预留缓冲比例（滑动窗口策略）
- `summary_threshold`: Optional[int] - 摘要触发阈值（摘要策略）

**Token 溢出策略枚举**：
```python
class TokenOverflowStrategyEnum(str, Enum):
    NONE = "NONE"                    # 不处理，直接截断
    SLIDING_WINDOW = "SLIDING_WINDOW" # 滑动窗口策略
    SUMMARY = "SUMMARY"              # 摘要策略
```

**业务规则**：
- temperature 范围必须在 0-2 之间
- top_p 范围必须在 0-1 之间
- strategy_type 为 SLIDING_WINDOW 时必须设置 reserve_ratio
- strategy_type 为 SUMMARY 时必须设置 summary_threshold

## 仓储接口设计

### AgentRepository

**职责**：定义 Agent 数据访问的标准接口

**接口方法**：
- `create(agent: AgentEntity) -> AgentEntity` - 创建 Agent
- `update(agent: AgentEntity) -> AgentEntity` - 更新 Agent
- `delete(agent_id: str) -> bool` - 删除 Agent
- `find_by_id(agent_id: str) -> Optional[AgentEntity]` - 根据 ID 查询
- `find_by_user_id(user_id: str, filters: dict) -> List[AgentEntity]` - 按用户查询
- `find_by_name(user_id: str, name_pattern: str) -> List[AgentEntity]` - 按名称搜索
- `find_published_agents() -> List[AgentEntity]` - 查询已上架的 Agent
- `find_agent_names(ids: List[str]) -> Dict[str, str]` - 批量查询 Agent 名称

### VersionRepository

**职责**：定义版本数据访问接口

**接口方法**：
- `create(version: AgentVersionEntity) -> AgentVersionEntity` - 创建版本
- `find_by_agent_id(agent_id: str) -> List[AgentVersionEntity]` - 查询 Agent 的所有版本
- `find_latest_version(agent_id: str) -> Optional[AgentVersionEntity]` - 查询最新版本
- `find_by_version_number(agent_id: str, version_number: str) -> Optional[AgentVersionEntity]` - 根据版本号查询
- `find_published_version(agent_id: str) -> Optional[AgentVersionEntity]` - 查询已发布版本
- `count_reviewing_versions() -> int` - 统计待审核版本数量
- `find_versions_for_review(status: PublishStatusEnum) -> List[AgentVersionEntity]` - 查询特定状态的版本

### WidgetRepository

**职责**：定义 Widget 数据访问接口

**接口方法**：
- `create(widget: AgentWidgetEntity) -> AgentWidgetEntity` - 创建 Widget
- `update(widget: AgentWidgetEntity) -> AgentWidgetEntity` - 更新 Widget
- `delete(widget_id: str) -> bool` - 删除 Widget
- `find_by_id(widget_id: str) -> Optional[AgentWidgetEntity]` - 根据 ID 查询
- `find_by_agent_id(agent_id: str) -> List[AgentWidgetEntity]` - 按 Agent 查询
- `find_by_public_id(public_id: str) -> Optional[AgentWidgetEntity]` - 根据 Public ID 查询
- `increment_daily_calls(widget_id: str, date: date) -> int` - 增加当日调用次数
- `get_daily_calls(widget_id: str, date: date) -> int` - 获取当日调用次数

## 领域服务设计

### AgentDomainService

**职责**：封装 Agent 核心业务逻辑

**方法**：
- `create_agent(user_id: str, create_cmd: CreateAgentCommand) -> AgentEntity`
  - 验证用户余额（调用计费系统）
  - 自动生成默认 LLM 配置
  - 验证工具和知识库权限
  - 创建 Agent 实体并持久化

- `update_agent(agent_id: str, update_cmd: UpdateAgentCommand) -> AgentEntity`
  - 验证用户对 Agent 的所有权
  - 验证更新的工具和知识库权限
  - 执行业务规则校验
  - 更新并返回

- `delete_agent(agent_id: str) -> bool`
  - 检查是否存在已发布版本
  - 级联删除关联数据（Widget、工作空间记录）
  - 执行删除操作

- `validate_tool_permissions(tool_ids: List[str], user_id: str) -> bool`
  - 验证用户是否有权限使用指定工具
  - 工具必须是用户自己的或公开的

- `generate_system_prompt(agent_info: AgentInfo) -> str`
  - 调用 LLM 服务生成结构化提示词
  - 基于 Agent 名称、描述、工具列表生成

### VersionDomainService

**职责**：管理版本生命周期

**方法**：
- `publish_new_version(agent_id: str, change_log: str) -> AgentVersionEntity`
  - 获取 Agent 当前配置快照
  - 自动计算下一个版本号（语义化递增）
  - 创建版本实体，状态设为 REVIEWING
  - 发送审核通知

- `submit_for_review(version_id: str) -> None`
  - 验证版本状态
  - 转换为 REVIEWING 状态

- `approve_version(version_id: str, reviewer_id: str) -> None`
  - 转换为 PUBLISHED 状态
  - 记录审核人和审核时间
  - 更新 Agent 的 current_version_id
  - 同步到市场模块

- `reject_version(version_id: str, rejection_reason: str, reviewer_id: str) -> None`
  - 转换为 REJECTED 状态
  - 记录拒绝原因和审核人
  - 发送拒绝通知

- `remove_version(version_id: str) -> None`
  - 转换为 REMOVED 状态
  - 从市场下架

### WidgetDomainService

**职责**：管理 Widget 配置和访问控制

**方法**：
- `create_widget(agent_id: str, create_cmd: CreateWidgetCommand) -> AgentWidgetEntity`
  - 验证 Agent 所有权
  - 生成唯一的 Public ID
  - 自动生成嵌入代码
  - 创建 Widget 实体

- `validate_domain_access(widget: AgentWidgetEntity, referer_domain: str) -> bool`
  - 空表返回 True（允许所有域名）
  - 精确匹配验证
  - 通配符匹配验证（支持 *.example.com）

- `check_daily_limit(widget: AgentWidgetEntity, current_date: date) -> bool`
  - 获取当日已调用次数
  - 判断是否超过限制
  - 返回 True 表示可以继续调用

- `generate_embed_code(widget: AgentWidgetEntity) -> str`
  - 基于 Public ID 生成 JavaScript SDK 嵌入代码
  - 支持自定义样式配置

### WorkspaceDomainService

**职责**：管理工作空间操作

**方法**：
- `add_to_workspace(user_id: str, agent_id: str) -> WorkspaceAgentEntity`
  - 验证 Agent 是否存在
  - 如果是他人 Agent，验证是否为已发布状态
  - 检查是否重复添加
  - 创建工作空间记录

- `remove_from_workspace(user_id: str, agent_id: str) -> bool`
  - 查找工作空间记录
  - 执行删除

- `update_model_config(user_id: str, agent_id: str, config: LLMModelConfig) -> LLMModelConfig`
  - 验证配置参数合法性
  - 更新或创建配置

## 状态机设计

### 版本发布状态机

**状态定义**：
- REVIEWING（审核中）
- PUBLISHED（已发布）
- REJECTED（已拒绝）
- REMOVED（已下架）

**状态转换规则**：

```
初始状态 --> REVIEWING（创建新版本）
REVIEWING --> PUBLISHED（管理员审核通过）
REVIEWING --> REJECTED（管理员审核拒绝）
REJECTED --> REVIEWING（重新提交审核）
PUBLISHED --> REMOVED（管理员下架）
REMOVED --> PUBLISHED（重新上架）
```

**状态转换表**：

| 当前状态 | 目标状态 | 触发条件 | 前置条件 |
|---------|---------|---------|---------|
| INIT | REVIEWING | 发布新版本 | 无 |
| REVIEWING | PUBLISHED | 审核通过 | 审核人角色权限 |
| REVIEWING | REJECTED | 审核拒绝 | 需填写拒绝原因 |
| REJECTED | REVIEWING | 重新提交 | 版本号自动升级 |
| PUBLISHED | REMOVED | 下架操作 | 管理员权限 |
| REMOVED | PUBLISHED | 重新上架 | 管理员权限 |

## 数据模型设计

### 数据库表结构

#### agents 表

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 主键，UUID |
| user_id | VARCHAR(36) | NOT NULL, INDEX | 创建者用户 ID |
| name | VARCHAR(50) | NOT NULL | Agent 名称 |
| description | VARCHAR(500) | NULL | 描述 |
| avatar_url | VARCHAR(500) | NULL | 头像 URL |
| system_prompt | TEXT | NULL | 系统提示词 |
| welcome_message | VARCHAR(500) | NULL | 欢迎消息 |
| tool_ids | JSON | NULL | 工具 ID 列表 |
| knowledge_base_ids | JSON | NULL | 知识库 ID 列表 |
| tool_preset_params | JSON | NULL | 工具预设参数 |
| current_version_id | VARCHAR(36) | NULL | 当前发布版本 ID |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| support_multimodal | BOOLEAN | DEFAULT FALSE | 多模态支持 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | ON UPDATE NOW() | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_user_id (user_id)
- INDEX idx_name (name)
- INDEX idx_enabled (enabled)

#### agent_versions 表

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 版本 ID |
| agent_id | VARCHAR(36) | NOT NULL, INDEX | 所属 Agent ID |
| version_number | VARCHAR(20) | NOT NULL | 版本号 |
| agent_name_snapshot | VARCHAR(50) | NOT NULL | 名称快照 |
| system_prompt_snapshot | TEXT | NULL | 提示词快照 |
| tool_ids_snapshot | JSON | NULL | 工具列表快照 |
| knowledge_base_ids_snapshot | JSON | NULL | 知识库列表快照 |
| change_log | VARCHAR(1000) | NULL | 变更日志 |
| publish_status | VARCHAR(20) | NOT NULL, INDEX | 发布状态 |
| review_rejection_reason | VARCHAR(1000) | NULL | 拒绝原因 |
| reviewer_id | VARCHAR(36) | NULL | 审核人 ID |
| published_at | TIMESTAMP | NULL | 发布时间 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |

**索引**：
- PRIMARY KEY (id)
- INDEX idx_agent_id (agent_id)
- UNIQUE INDEX idx_agent_version (agent_id, version_number)
- INDEX idx_publish_status (publish_status)

#### agent_widgets 表

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | Widget ID |
| agent_id | VARCHAR(36) | NOT NULL, INDEX | 所属 Agent ID |
| public_id | VARCHAR(16) | NOT NULL, UNIQUE | 公开访问 ID |
| name | VARCHAR(100) | NOT NULL | Widget 名称 |
| widget_type | VARCHAR(20) | NOT NULL | Widget 类型 |
| model_id | VARCHAR(50) | NOT NULL | 模型 ID |
| model_provider | VARCHAR(50) | NOT NULL | 模型提供商 |
| allowed_domains | JSON | NULL | 域名白名单 |
| daily_call_limit | INT | DEFAULT -1 | 每日调用限制 |
| enabled | BOOLEAN | DEFAULT TRUE | 是否启用 |
| embed_code | TEXT | NOT NULL | 嵌入代码 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | ON UPDATE NOW() | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_public_id (public_id)
- INDEX idx_agent_id (agent_id)

#### workspace_agents 表

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 主键 |
| user_id | VARCHAR(36) | NOT NULL, INDEX | 用户 ID |
| agent_id | VARCHAR(36) | NOT NULL, INDEX | Agent ID |
| custom_name | VARCHAR(50) | NULL | 自定义名称 |
| added_at | TIMESTAMP | DEFAULT NOW() | 添加时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_user_agent (user_id, agent_id)
- INDEX idx_agent_id (agent_id)

#### llm_model_configs 表

| 字段名 | 类型 | 约束 | 说明 |
|-------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | 主键 |
| user_id | VARCHAR(36) | NOT NULL, INDEX | 用户 ID |
| agent_id | VARCHAR(36) | NOT NULL, INDEX | Agent ID |
| model_id | VARCHAR(50) | NOT NULL | 模型 ID |
| provider | VARCHAR(50) | NOT NULL | 提供商 |
| temperature | FLOAT | DEFAULT 0.7 | 温度参数 |
| top_p | FLOAT | DEFAULT 0.7 | Top P 参数 |
| top_k | INT | DEFAULT 50 | Top K 参数 |
| max_tokens | INT | NULL | 最大 Token 数 |
| strategy_type | VARCHAR(20) | DEFAULT 'NONE' | Token 溢出策略 |
| reserve_ratio | FLOAT | NULL | 预留缓冲比例 |
| summary_threshold | INT | NULL | 摘要触发阈值 |
| created_at | TIMESTAMP | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMP | ON UPDATE NOW() | 更新时间 |

**索引**：
- PRIMARY KEY (id)
- UNIQUE INDEX idx_user_agent (user_id, agent_id)
- INDEX idx_agent_id (agent_id)

## 应用服务设计

### AgentAppService

**职责**：编排 Agent 管理的完整业务流程

**服务方法**：
- `create_agent(cmd: CreateAgentCommand, user_id: str) -> AgentDTO`
  - 参数验证
  - 调用领域服务创建 Agent
  - 转换为 DTO 返回

- `update_agent(agent_id: str, cmd: UpdateAgentCommand, user_id: str) -> AgentDTO`
  - 权限验证
  - 调用领域服务更新
  - 返回更新后的 DTO

- `delete_agent(agent_id: str, user_id: str) -> bool`
  - 权限验证
  - 调用领域服务删除
  - 记录审计日志

- `get_agent(agent_id: str, user_id: str) -> AgentDTO`
  - 权限验证（查看自己的或已发布的）
  - 查询并返回 DTO

- `list_agents(user_id: str, filters: AgentFilter) -> Page[AgentDTO]`
  - 支持分页
  - 支持名称、状态过滤
  - 返回分页结果

- `toggle_agent_status(agent_id: str, enabled: bool, user_id: str) -> AgentDTO`
  - 权限验证
  - 切换启用状态
  - 返回更新后的 DTO

### VersionAppService

**职责**：编排版本管理流程

**服务方法**：
- `publish_version(agent_id: str, change_log: str, user_id: str) -> VersionDTO`
  - 验证 Agent 所有权
  - 调用领域服务创建新版本
  - 触发审核流程

- `review_version(version_id: str, approved: bool, reason: str, reviewer_id: str) -> VersionDTO`
  - 验证审核人权限
  - 调用领域服务审核
  - 记录审核日志

- `get_version_history(agent_id: str, user_id: str) -> List[VersionDTO]`
  - 查询所有版本历史
  - 按创建时间倒序排列

- `get_latest_version(agent_id: str) -> VersionDTO`
  - 查询最新版本
  - 无需权限验证

## 缓存设计

### 缓存策略

**缓存内容**：
- 热门 Agent 列表（用户维度）
- Widget 配置（按 Public ID）
- 已发布版本快照（按 Agent ID）
- 每日调用次数计数（按 Widget ID + 日期）

**TTL 设置**：
- Agent 列表：5 分钟
- Widget 配置：10 分钟
- 版本快照：30 分钟
- 调用计数：次日凌晨 0 点过期

**缓存失效场景**：
- Agent 信息变更时清除对应缓存
- Widget 配置更新时清除对应缓存
- 版本发布后清除版本快照缓存

## 安全设计

### RBAC 权限模型

**权限点定义**：
- `agent:create` - 创建智能体
- `agent:edit` - 编辑自己的智能体
- `agent:delete` - 删除自己的智能体
- `agent:publish` - 发布智能体到市场
- `agent:review` - 审核市场智能体（管理员）
- `agent:remove` - 下架市场智能体（管理员）

**角色定义**：
- **普通用户**：拥有 agent:create, agent:edit, agent:delete, agent:publish
- **审核员**：额外拥有 agent:review
- **管理员**：拥有所有权限，包括 agent:remove

### 二次验证（2FA）

**触发场景**：
- 删除已发布的 Agent
- 批量下架操作
- 修改 Widget调用限额
- 导出 Agent 配置

**验证方式**：
- 邮箱验证码：6 位数字，有效期 5 分钟
- 短信验证码：6 位数字，有效期 5 分钟
- TOTP：基于时间的动态验证码

## 性能优化设计

### 数据库优化

**索引策略**：
- 所有外键字段建立索引（user_id, agent_id）
- 常用查询字段建立索引（name, publish_status）
- 组合索引优化排序查询

**查询优化**：
- 避免 N+1 查询（使用 JOIN 预加载关联数据）
- 分页查询使用游标分页（基于 ID 而非 OFFSET）
- 大数据量查询使用只读副本

### 缓存优化

**多级缓存**：
- L1：应用内缓存（本地内存，存储热点数据）
- L2：分布式缓存（Redis，存储共享数据）

**缓存预热**：
- 启动时加载热门 Agent 列表
- 定时任务刷新缓存

## 扩展性设计

### 插件式扩展

**工具类型扩展**：
- 工具注册表（tools_registry 表）
- 工具适配器模式（ToolAdapter 接口）
- 动态加载新工具类型

**知识库类型扩展**：
- 知识库适配器接口（KnowledgeBaseAdapter）
- 支持接入不同类型知识库（向量数据库、传统数据库、API 等）

**Widget 类型扩展**：
- Widget 渲染模板机制
- Widget 配置 Schema 定义
- 插件注册表

### 配置扩展

**可扩展参数**：
- LLM 模型参数支持动态新增
- Token 溢出策略支持自定义实现
- 系统限制可通过配置文件调整

## 审计与监控

### 审计日志

**记录内容**：
- 操作类型（CREATE/UPDATE/DELETE/PUBLISH/REVIEW）
- 操作人 ID
- 操作时间
- 操作对象（Agent ID、Version ID）
- 操作详情（JSON 格式）

**存储方式**：
- 独立审计日志表（audit_logs）
- 异步写入（消息队列解耦）
- 定期归档（90 天后数据归档到冷存储）

### 监控指标

**关键指标**：
- API 延迟（P50/P90/P99）
- API 错误率（4xx/5xx）
- Widget调用量和成功率
- 版本发布频率
- 审核平均时长

**告警规则**：
- API 错误率 > 1% 持续 5 分钟
- API P99 延迟 > 2 秒 持续 10 分钟
- Widget调用失败率 > 5% 持续 5 分钟
