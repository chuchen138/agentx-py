# Agent Management Capability Specification

本规范定义了 Agent 管理功能的需求和行为。

## ADDED Requirements

### Requirement: 创建 Agent

系统必须允许授权用户创建新的 Agent 实例。

**验收标准:**
- 用户必须已认证才能创建 Agent
- Agent 名称不能为空且长度不超过 100 字符
- 系统自动生成唯一的 Agent ID
- 新创建的 Agent 状态默认为 'draft'
- 系统记录创建时间和创建者 ID

#### Scenario: 成功创建 Agent
- **WHEN** 认证用户提交有效的 Agent 创建请求
- **THEN** 系统返回 201 Created 状态码和完整的 Agent 信息

#### Scenario: 未认证用户尝试创建
- **WHEN** 未认证用户尝试创建 Agent
- **THEN** 系统返回 401 Unauthorized 状态码

#### Scenario: Agent 名称为空
- **WHEN** 提交的 Agent 名称为空字符串
- **THEN** 系统返回 422 Validation Error 状态码

#### Scenario: Agent 名称超长
- **WHEN** 提交的 Agent 名称超过 100 字符
- **THEN** 系统返回 422 Validation Error 状态码

### Requirement: 查询 Agent 列表

系统必须允许授权用户查询其拥有的 Agent 列表。

**验收标准:**
- 用户只能查看自己创建的 Agent
- 支持分页查询 (offset/limit)
- 支持按状态过滤
- 返回列表包含 Agent 的基本信息

#### Scenario: 成功查询列表
- **WHEN** 认证用户请求 Agent 列表
- **THEN** 系统返回该用户的 Agent 列表 (可能为空)

#### Scenario: 分页查询
- **WHEN** 用户请求第 2 页，每页 10 条
- **THEN** 系统返回 offset=10, limit=10 的结果

#### Scenario: 按状态过滤
- **WHEN** 用户请求 status='published' 的 Agent
- **THEN** 系统只返回已发布的 Agent

### Requirement: 查询 Agent 详情

系统必须允许授权用户查询单个 Agent 的详细信息。

**验收标准:**
- 用户只能查看自己创建的 Agent 详情
- 返回完整的 Agent 信息包括配置
- 不存在的 Agent 返回 404

#### Scenario: 成功查询详情
- **WHEN** 用户请求自己创建的 Agent 详情
- **THEN** 系统返回完整的 Agent 信息

#### Scenario: 查询不存在的 Agent
- **WHEN** 用户请求不存在的 Agent ID
- **THEN** 系统返回 404 Not Found 状态码

#### Scenario: 查询他人的 Agent
- **WHEN** 用户尝试查看其他用户的 Agent
- **THEN** 系统返回 403 Forbidden 或 404 Not Found

### Requirement: 更新 Agent

系统必须允许授权用户更新其拥有的 Agent。

**验收标准:**
- 用户只能更新自己创建的 Agent
- 可以更新名称、描述、配置
- 不允许更新 ID、创建者、创建时间
- 更新时间自动刷新

#### Scenario: 成功更新 Agent
- **WHEN** 用户提交有效的更新请求
- **THEN** 系统更新 Agent 并返回更新后的信息

#### Scenario: 部分更新
- **WHEN** 用户只更新 Agent 名称
- **THEN** 系统只更新名称，其他字段保持不变

#### Scenario: 更新不存在的 Agent
- **WHEN** 用户更新不存在的 Agent
- **THEN** 系统返回 404 Not Found

### Requirement: 删除 Agent

系统必须允许授权用户删除其拥有的 Agent。

**验收标准:**
- 用户只能删除自己创建的 Agent
- 删除后不可恢复
- 返回删除成功的确认

#### Scenario: 成功删除 Agent
- **WHEN** 用户请求删除自己的 Agent
- **THEN** 系统删除 Agent 并返回 200 OK

#### Scenario: 删除不存在的 Agent
- **WHEN** 用户删除不存在的 Agent
- **THEN** 系统返回 404 Not Found

### Requirement: 发布 Agent

系统必须允许授权用户发布其创建的 Agent。

**验收标准:**
- 只有 Agent 所有者可以发布
- 发布后状态从 'draft' 变为 'published'
- 已发布的 Agent 可以被其他用户使用

#### Scenario: 成功发布 Agent
- **WHEN** 用户发布自己的 draft 状态 Agent
- **THEN** Agent 状态变为 'published',返回更新后的信息

#### Scenario: 重复发布
- **WHEN** 用户发布已发布的 Agent
- **THEN** 系统返回当前已发布状态，不做修改

#### Scenario: 发布他人的 Agent
- **WHEN** 用户尝试发布其他用户的 Agent
- **THEN** 系统返回 403 Forbidden
