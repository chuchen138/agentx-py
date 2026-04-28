# 管理后台技术设计

## 概述

管理后台模块采用应用服务层划分模式，按照领域职责分为独立的服务，提供官方资源管理、工具审核等管理功能，确保管理操作与用户操作清晰分离。

## 技术架构

### 架构设计

管理后台采用分层架构设计，接口层处理管理后台的 HTTP 请求，应用层按领域职责划分为 AdminLLMAppService、AdminToolAppService、AdminAuditAppService 等独立服务，领域层提供 LLM 和 Tool 等领域服务支持。

### API 接口设计

#### 管理员用户管理 API

| 接口路径 | 方法 | 功能描述 | 权限要求 |
|---------|------|---------|---------|
| `/api/v1/admin/users` | POST | 创建管理员 | SUPER_ADMIN 或 ADMIN |
| `/api/v1/admin/users` | GET | 获取管理员列表 | ADMIN |
| `/api/v1/admin/users/{admin_id}` | GET | 获取管理员详情 | ADMIN |
| `/api/v1/admin/users/{admin_id}/role` | PUT | 更新管理员角色 | SUPER_ADMIN |
| `/api/v1/admin/users/{admin_id}/permissions` | PUT | 更新管理员权限 | SUPER_ADMIN |
| `/api/v1/admin/users/{admin_id}/deactivate` | POST | 停用管理员 | SUPER_ADMIN |
| `/api/v1/admin/users/{admin_id}` | DELETE | 删除管理员 | SUPER_ADMIN |

#### 官方服务商管理 API

| 接口路径 | 方法 | 功能描述 | 权限要求 |
|---------|------|---------|---------|
| `/api/v1/admin/providers` | POST | 创建官方服务商 | ADMIN |
| `/api/v1/admin/providers` | GET | 获取官方服务商列表 | ALL (所有用户可查) |
| `/api/v1/admin/providers/{provider_id}` | GET | 获取服务商详情 | ALL |
| `/api/v1/admin/providers/{provider_id}` | PUT | 更新官方服务商 | ADMIN |
| `/api/v1/admin/providers/{provider_id}` | DELETE | 删除官方服务商 | SUPER_ADMIN |
| `/api/v1/admin/providers/{provider_id}/logs` | GET | 获取操作日志 | ADMIN |

#### 工具审核 API

| 接口路径 | 方法 | 功能描述 | 权限要求 |
|---------|------|---------|---------|
| `/api/v1/admin/tools/audit` | POST | 提交工具审核申请 | AUTHENTICATED_USER |
| `/api/v1/admin/tools/audit/pending` | GET | 获取待审核列表 | AUDITOR |
| `/api/v1/admin/tools/audit/records` | GET | 获取审核记录列表 | AUDITOR |
| `/api/v1/admin/tools/audit/{record_id}` | GET | 获取审核记录详情 | AUDITOR |
| `/api/v1/admin/tools/audit/{record_id}/start` | POST | 开始审核 | AUDITOR |
| `/api/v1/admin/tools/audit/{record_id}/approve` | POST | 审核通过 | AUDITOR |
| `/api/v1/admin/tools/audit/{record_id}/reject` | POST | 审核拒绝 | AUDITOR |
| `/api/v1/admin/tools/audit/{record_id}/cancel` | POST | 取消审核 | APPLICANT |
| `/api/v1/admin/tools/audit/tool/{tool_id}/history` | GET | 获取审核历史 | ADMIN |

#### 审计日志 API

| 接口路径 | 方法 | 功能描述 | 权限要求 |
|---------|------|---------|---------|
| `/api/v1/admin/logs` | GET | 获取审计日志列表 | ADMIN |
| `/api/v1/admin/logs/resource/{resource_type}/{resource_id}` | GET | 获取资源操作日志 | ADMIN |
| `/api/v1/admin/logs/timerange` | GET | 按时间范围查询日志 | ADMIN |
| `/api/v1/admin/logs/search` | GET | 搜索日志 | ADMIN |
| `/api/v1/admin/logs/export` | GET | 导出日志 | ADMIN |
| `/api/v1/admin/logs/action-types` | GET | 获取操作类型列表 | ADMIN |
| `/api/v1/admin/logs/resource-types` | GET | 获取资源类型列表 | ADMIN |

### 部署形态

- **独立 FastAPI 应用**：路由前缀 `/admin`，与用户服务共享数据库但逻辑隔离
- **前端框架**：React Admin + Ant Design Pro（暗色主题支持）
- **认证方式**：JWT Token（有效期 2 小时）+ Refresh Token（有效期 7 天）
- **双因素认证**：敏感操作强制 TOTP（Google Authenticator 兼容）

### 核心组件

### AdminLLMAppService

负责官方服务商的创建和管理、服务商配置的更新和维护、密钥安全和掩码处理以及管理员权限验证。关键是创建服务商时设置官方标识、更新服务商时支持密钥掩码处理、管理员修改操作绑定操作用户、配置变更触发相关事件。

### AdminToolAppService

负责官方工具的审核和管理、工具审核流程控制、审核决策和意见记录以及工具发布管理。包括审核工具、查询待审核工具列表和发布官方工具等功能。

## 设计模式

### 应用服务模式

应用服务封装业务用例，协调领域层和基础设施层，不包含业务逻辑只负责协调，调用领域服务执行业务操作。

### 组装器模式

组装器在 DTO 和实体之间进行转换，使用 ProviderAssembler 在 ProviderEntity 和 ProviderDTO 之间转换，使用 ToolAssembler 在 ToolEntity 和 ToolDTO 之间转换。

## 官方服务商管理

### 官方服务商创建

管理员创建官方服务商时，系统转换为实体、设置为官方服务商、由领域服务处理创建操作并返回 DTO。

### 密钥掩码处理

系统支持密钥掩码更新流程。用户查看服务商配置时系统返回掩码后的密钥（保留最后 4 位字符，前面用星号替代，例：`sk-proj***abcd`），用户修改配置时系统判断是否为掩码，掩码则保留原密钥，新密钥则更新为新密钥，最后加密存储到数据库。密钥使用 AES-256-GCM 加密存储，加密密钥与应用配置分离，传输时使用 HTTPS。前后端双重脱敏：后端返回掩码数据，前端不展示完整密钥。

## 工具审核流程

### 审核操作

工具审核流程包括权限验证、获取待审核工具、记录审核结果（审核人、审核结果、审核意见、审核时间）、更新工具状态（审核通过标记为 OFFICIAL 并发布，审核拒绝标记为 REJECTED）、保存审核记录和工具状态等步骤。

### 审核流程

流程包括用户提交工具发布申请、工具进入审核状态、管理员查看待审核列表、管理员审核工具（检查工具定义、测试接口可用性、查看工具文档）、管理员做出审核决策（通过则标记为 OFFICIAL 并发布，拒绝则标记为 REJECTED 并记录拒绝原因）、审核结果反馈给用户、工具状态更新等步骤。

## 审计日志设计

### 操作记录

审计日志包含官方服务商管理（创建、更新、删除操作的时间、操作人、相关信息）和工具审核（审核、发布操作的时间、操作人、工具 ID、相关信息）的内容。

### 审计日志格式

审计日志记录时间戳、操作人、操作类型、资源信息（类型、ID、名称）和变更列表（字段、旧值、新值）等内容。

### 防篡改机制

- **append-only 表结构**：审计日志表禁止 UPDATE/DELETE 操作（数据库权限控制）
- **哈希链**：每条日志包含 prev_log_hash 字段（上一条日志的 SHA-256 哈希），第一条日志的 prev_log_hash 为全 0
- **完整性验证**：遍历日志链，重新计算哈希比对
- **归档策略**：热数据（90 天）存 PostgreSQL，冷数据（>90 天）自动迁移到 S3 Glacier
- **区块链存证**：定期（每天）将日志哈希链根哈希上链（可选）

## 权限控制设计

### RBAC 模型

系统采用基于角色的访问控制（RBAC）模型，支持细粒度权限管理。

**角色定义**：
- **SUPER_ADMIN**：超级管理员，拥有所有权限，可管理其他管理员
- **ADMIN**：管理员，拥有常规管理权限（创建/修改官方资源）
- **AUDITOR**：审核员，仅拥有工具审核权限

**权限模型**：
- 权限格式：`resource:action:condition`
  - 示例：`provider:create:own`、`tool:audit:any`、`log:query:own`
- 角色 - 权限映射表存储在数据库 `admin_role_permissions` 表
- 支持权限继承（SUPER_ADMIN 继承 ADMIN 和 AUDITOR 所有权限）

**权限验证流程**：
1. 从请求头提取管理员 ID 和 JWT Token
2. 验证 Token 有效性（Redis 黑名单检查）
3. 从数据库或缓存加载管理员角色和权限
4. 验证所需权限是否在权限集合中
5. 记录权限验证日志

### 角色定义

ADMIN 角色拥有所有管理权限，可以创建和管理官方资源、审核用户提交的工具。USER 角色只能使用官方资源、不能执行管理操作、可以申请工具发布。

### 权限检查

系统实现权限检查，获取用户角色并验证是否为管理员，非管理员用户执行管理操作时抛出权限拒绝异常。

### 权限控制方式

系统在查询和更新语句中直接添加用户 ID 条件，数据库层面隔离确保数据安全，避免应用层权限漏洞，简化业务逻辑。

## 异常处理

### 异常类型

系统定义权限不足、资源不存在、密钥验证失败、审核冲突等异常类型，权限不足时非 ADMIN 用户执行管理操作抛出权限拒绝异常，资源不存在时修改不存在服务商或工具抛出资源不存在异常，密钥验证失败时密钥格式错误或无效抛出无效密钥异常，审核冲突时工具已在审核中或已发布抛出审核冲突异常。

## 性能优化

### 批量操作

系统支持批量审核工具、批量更新服务商配置，减少数据库往返次数。单次批量上限 100 条，事务边界内原子性操作。

### 查询缓存

系统缓存官方服务商列表和工具审核列表，TTL 设置为 300 秒。变更时主动失效缓存。

### 异步处理

系统非关键操作异步执行，如发送通知邮件、更新统计信息、写入审计日志等。

### 查询优化

- 复合索引：idx_audit_logs_admin_created、idx_audit_logs_action_resource
- 游标分页：基于 keyset pagination，避免 offset 性能问题
- 覆盖索引：减少回表查询
- 分区表：审计日志按月分区，自动创建新分区

### 全文搜索

支持 pg_trgm 或 Elasticsearch 全文搜索，百万级数据 < 1s 返回。

## 监控指标

### 关键指标

系统监控管理员操作统计（操作类型分布、操作人员统计、操作趋势）、审核效率（平均审核时间、待审核数量、审核通过率）、官方资源使用（官方服务商调用次数、官方工具使用次数、用户分布）等指标。

### 告警规则

系统监控待审核工具超过阈值（>50 持续 1 小时）、审核超时超过阈值（>24 小时）、官方服务商标记为不健康（连续 3 次调用失败）、权限验证失败率突增（5 分钟内 > 10%）、管理员异地登录等情况并设置告警。

### 日志收集

使用结构化日志（JSON 格式，包含 trace_id、span_id），通过 Filebeat 收集到 Loki/ELK，支持实时检索。

## 安全考虑

### 密钥安全

密钥值仅在创建和重置时返回，之后无法查询。密钥采用 16 位随机字符串，提供足够熵值。密钥格式固定，便于识别和管理。密钥使用 AES-256-GCM 加密存储，加密密钥与应用配置分离。

### 访问控制

用户只能管理自己的资源，所有操作都需要用户身份认证。数据库层面添加用户 ID 条件，确保数据安全。

### 输入验证

系统使用 Pydantic 进行请求参数校验，Agent ID 和用户 ID 校验为非空，密钥名称校验为非空。

### 审计日志

系统记录所有操作日志和安全审计日志，便于问题追溯和安全分析。

### 双因素认证

敏感操作（删除、批量审核、权限变更）强制 TOTP 验证。登录异常检测（异地 IP、新设备）触发二次验证。

### IP 白名单

支持限制管理员登录 IP 范围（CIDR 格式），SUPER_ADMIN 不受 IP 限制（紧急情况下使用）。

## 配置设计

### 管理后台配置

管理后台配置包括启用状态、所需角色、严格模式（即使非敏感操作也需要管理员权限）、密钥掩码长度（前 6 后 4）、需要确认、敏感操作列表（删除服务商、删除工具、批量审核）、默认审核状态、是否自动发布、审核员分配方式等配置。

### 审计日志配置

审计日志保留天数（默认 90 天热数据，2 年冷数据）、自动清理开关、最大上传大小（字节）、审核超时时间（小时）、是否启用自动审核等配置。

### 权限缓存配置

权限缓存启用开关、缓存 TTL（默认 300 秒）、缓存预热开关、缓存命中率监控阈值（默认 95%）。
