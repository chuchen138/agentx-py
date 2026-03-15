## 实施清单

### 阶段一：项目初始化与基础架构

- [ ] 1.1 创建 Python FastAPI 项目结构
     【目标对象】整个后端项目
     【修改目的】搭建 Python FastAPI 项目基础框架
     【修改方式】使用 FastAPI 应用脚手架创建项目结构
     【相关依赖】无
     【修改内容】
        - 创建目录结构（app/domain/infrastructure/interfaces/tests）
        - 配置文件（settings.py, alembic.ini）
        - 初始化 SQLAlchemy 和 Alembic
        - 配置 Pydantic 和数据验证

- [ ] 1.2 定义核心数据模型（ORM Models）
     【目标对象】`app/domain/agent/model/`
     【修改目的】定义 Agent 管理相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型，使用 Pydantic 定义 Schema
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - Agent 模型（agents 表）：ID、名称、头像、描述、系统提示词、欢迎消息等
        - AgentVersion 模型（agent_versions 表）：版本 ID、Agent ID、版本号、快照数据等
        - AgentWidget 模型（agent_widgets 表）：Widget ID、Agent ID、Public ID、域名白名单等
        - WorkspaceAgent 模型（workspace_agents 表）：工作空间 Agent 关联
        - LLMModelConfig 模型（llm_model_configs 表）：LLM 参数配置
        - 定义对应的 Pydantic Schema（Create/Update/Response DTO）

- [ ] 1.3 实现 Agent 仓储模式
     【目标对象】`app/domain/agent/repository.py`
     【修改目的】定义 Agent 数据访问接口
     【修改方式】实现 Repository 模式，封装数据库操作
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AgentRepository 接口（抽象基类）
        - 实现 SQLAlchemyAgentRepository
        - 实现 CRUD 基本操作
        - 实现复杂查询（按用户 ID 过滤、按名称搜索、状态过滤）
        - 实现版本历史查询
        - 实现已上架 Agent 查询

- [ ] 1.4 实现 Widget 仓储
     【目标对象】`app/domain/agent/widget_repository.py`
     【修改目的】定义 Widget 数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 WidgetRepository 接口
        - 实现 Widget CRUD 操作
        - 实现域名白名单校验查询
        - 实现调用次数统计和限额检查

- [ ] 1.5 实现工作空间仓储
     【目标对象】`app/domain/workspace/repository.py`
     【修改目的】定义工作空间数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 WorkspaceRepository 接口
        - 实现工作空间 Agent 的增删改查
        - 实现 LLM 模型配置管理

### 阶段二：领域服务与业务逻辑

- [ ] 2.1 实现 Agent 领域服务
     【目标对象】`app/domain/agent/service.py`
     【修改目的】封装 Agent 核心业务逻辑
     【修改方式】实现领域服务层，包含业务规则验证
     【相关依赖】AgentRepository, 工具模块，知识库模块
     【修改内容】
        - Agent 创建逻辑（含默认 LLM 配置创建）
        - Agent 更新逻辑（权限验证、工具和知识库引用验证）
        - Agent 删除逻辑（级联删除验证）
        - Agent 状态管理（启用/禁用）
        - 工具和知识库权限校验
        - 系统提示词 AI 辅助生成服务

- [ ] 2.2 实现版本管理服务
     【目标对象】`app/domain/agent/version_service.py`
     【修改目的】管理 Agent 版本生命周期
     【修改方式】实现版本发布、审核、查询逻辑
     【相关依赖】AgentRepository, VersionRepository
     【修改内容】
        - 版本号自动生成（语义化版本递增）
        - 版本快照创建（保存当前配置）
        - 版本状态机管理（审核中 -> 已发布/拒绝 -> 已下架）
        - 版本历史查询
        - 最新版本获取

- [ ] 2.3 实现审核流程服务
     【目标对象】`app/domain/agent/review_service.py`
     【修改目的】处理版本发布审核流程
     【修改方式】实现审核状态转换和通知机制
     【相关依赖】VersionRepository, 通知模块
     【修改内容】
        - 提交审核（状态转换为 REVIEWING）
        - 审核通过（状态转换为 PUBLISHED）
        - 审核拒绝（状态转换为 REJECTED，记录拒绝原因）
        - 下架操作（状态转换为 REMOVED）
        - 审核通知（邮件/站内信通知用户）
        - 审核历史记录

- [ ] 2.4 实现 Widget 领域服务
     【目标对象】`app/domain/agent/widget_service.py`
     【修改目的】管理 Widget 配置和访问控制
     【修改方式】实现 Widget 业务逻辑
     【相关依赖】WidgetRepository, 缓存服务
     【修改内容】
        - Widget 创建和配置
        - Public ID 生成（确保唯一性）
        - 域名白名单校验（支持通配符）
        - 每日调用限额检查和计数
        - 嵌入代码生成
        - Widget 启用/禁用

- [ ] 2.5 实现工作空间领域服务
     【目标对象】`app/domain/workspace/service.py`
     【修改目的】管理工作空间和个人配置
     【修改方式】实现工作空间业务逻辑
     【相关依赖】WorkspaceRepository, LLMConfigRepository
     【修改内容】
        - 添加 Agent 到工作空间（支持自己和别人的已发布 Agent）
        - 从工作空间移除 Agent
        - LLM 模型配置管理（增删改查）
        - Token 溢出策略执行（滑动窗口、摘要策略）
        - 工作空间 Agent 列表查询

### 阶段三：应用服务层

- [ ] 3.1 实现 Agent 应用服务
     【目标对象】`app/application/agent/agent_app_service.py`
     【修改目的】编排 Agent 管理用例
     【修改方式】实现应用服务层，协调领域服务
     【相关依赖】AgentDomainService, VersionService, WidgetService
     【修改内容】
        - CreateAgentAppService：创建 Agent
        - UpdateAgentAppService：更新 Agent
        - DeleteAgentAppService：删除 Agent
        - GetAgentAppService：查询单个 Agent
        - ListAgentsAppService：查询 Agent 列表
        - EnableDisableAgentAppService：状态切换

- [ ] 3.2 实现版本管理应用服务
     【目标对象】`app/application/agent/version_app_service.py`
     【修改目的】编排版本管理用例
     【修改方式】实现应用服务层
     【相关依赖】VersionService, ReviewService
     【修改内容】
        - PublishVersionAppService：发布新版本
        - ReviewVersionAppService：审核版本（管理员）
        - GetVersionHistoryAppService：查询版本历史
        - GetLatestVersionAppService：获取最新版本

- [ ] 3.3 实现 Widget 应用服务
     【目标对象】`app/application/agent/widget_app_service.py`
     【修改目的】编排 Widget 管理用例
     【修改方式】实现应用服务层
     【相关依赖】WidgetService
     【修改内容】
        - CreateWidgetAppService：创建 Widget
        - UpdateWidgetAppService：更新 Widget 配置
        - DeleteWidgetAppService：删除 Widget
        - GetWidgetAppService：查询 Widget 详情
        - GenerateEmbedCodeAppService：生成嵌入代码

- [ ] 3.4 实现工作空间应用服务
     【目标对象】`app/application/workspace/workspace_app_service.py`
     【修改目的】编排工作空间管理用例
     【修改方式】实现应用服务层
     【相关依赖】WorkspaceService, LLMConfigService
     【修改内容】
        - AddToWorkspaceAppService：添加到工作空间
        - RemoveFromWorkspaceAppService：从工作空间移除
        - UpdateModelConfigAppService：更新 LLM 模型配置
        - GetWorkspaceAgentsAppService：查询工作空间 Agent 列表

- [ ] 3.5 实现提示词生成应用服务
     【目标对象】`app/application/agent/prompt_generation_app_service.py`
     【修改目的】AI 辅助生成系统提示词
     【修改方式】调用 LLM 服务生成提示词
     【相关依赖】LLM 服务，AgentRepository
     【修改内容】
        - GeneratePromptAppService：基于 Agent 信息生成结构化提示词
        - 支持中文和英文生成
        - 可编辑和优化生成的提示词

### 阶段四：API 接口层

- [ ] 4.1 创建 Agent 管理 API 路由
     【目标对象】`app/interfaces/api/v1/agents/`
     【修改目的】暴露 Agent 管理的 HTTP API
     【修改方式】使用 FastAPI 创建 RESTful 路由
     【相关依赖】AgentAppService, Pydantic Schemas
     【修改内容】
        - `POST /api/v1/agents` - 创建智能体
        - `GET /api/v1/agents/{agent_id}` - 查询单个智能体
        - `PUT /api/v1/agents/{agent_id}` - 更新智能体
        - `DELETE /api/v1/agents/{agent_id}` - 删除智能体
        - `GET /api/v1/agents` - 查询智能体列表（支持分页和过滤）
        - `PATCH /api/v1/agents/{agent_id}/status` - 切换启用状态
        - `GET /api/v1/agents/market` - 查询已上架的智能体（市场）

- [ ] 4.2 创建版本管理 API 路由
     【目标对象】`app/interfaces/api/v1/agents/{agent_id}/versions/`
     【修改目的】暴露版本管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】VersionAppService
     【修改内容】
        - `POST /api/v1/agents/{agent_id}/versions` - 发布新版本
        - `GET /api/v1/agents/{agent_id}/versions` - 查询版本历史
        - `GET /api/v1/agents/{agent_id}/versions/latest` - 获取最新版本
        - `GET /api/v1/agents/{agent_id}/versions/{version_id}` - 查询特定版本详情
        - `POST /api/v1/agents/{agent_id}/versions/{version_id}/review` - 审核版本（管理员）

- [ ] 4.3 创建 Widget 管理 API 路由
     【目标对象】`app/interfaces/api/v1/agents/{agent_id}/widgets/`
     【修改目的】暴露 Widget 管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】WidgetAppService
     【修改内容】
        - `POST /api/v1/agents/{agent_id}/widgets` - 创建 Widget
        - `GET /api/v1/agents/{agent_id}/widgets` - 查询 Widget 列表
        - `GET /api/v1/agents/{agent_id}/widgets/{widget_id}` - 查询 Widget 详情
        - `PUT /api/v1/agents/{agent_id}/widgets/{widget_id}` - 更新 Widget 配置
        - `DELETE /api/v1/agents/{agent_id}/widgets/{widget_id}` - 删除 Widget
        - `POST /api/v1/agents/{agent_id}/widgets/{widget_id}/embed-code` - 生成嵌入代码

- [ ] 4.4 创建工作空间 API 路由
     【目标对象】`app/interfaces/api/v1/workspace/`
     【修改目的】暴露工作空间管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】WorkspaceAppService
     【修改内容】
        - `POST /api/v1/workspace/agents` - 添加 Agent 到工作空间
        - `GET /api/v1/workspace/agents` - 查询工作空间中的 Agent 列表
        - `DELETE /api/v1/workspace/agents/{agent_id}` - 从工作空间移除 Agent
        - `PUT /api/v1/workspace/agents/{agent_id}/model-config` - 更新 LLM 模型配置

- [ ] 4.5 创建提示词生成 API 路由
     【目标对象】`app/interfaces/api/v1/agents/{agent_id}/prompt/generate`
     【修改目的】暴露 AI 辅助生成提示词的 API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】PromptGenerationAppService
     【修改内容】
        - `POST /api/v1/agents/{agent_id}/prompt/generate` - AI 生成系统提示词
        - 支持语言选择（中文/英文）

- [ ] 4.6 实现 Widget 公开访问端点
     【目标对象】`app/interfaces/api/v1/public/widgets/`
     【修改目的】提供 Widget 的公开访问接口（无需登录）
     【修改方式】使用 FastAPI 创建路由，包含域名验证
     【相关依赖】WidgetService, 缓存服务
     【修改内容】
        - `GET /api/v1/public/widgets/{public_id}/config` - 获取 Widget 配置（域名白名单验证）
        - `POST /api/v1/public/widgets/{public_id}/chat` - Widget 对话接口（调用限额验证）

### 阶段五：安全与认证

- [ ] 5.1 实现 RBAC 权限控制
     【目标对象】`app/infrastructure/security/rbac.py`
     【修改目的】实现细粒度的权限控制
     【修改方式】基于角色的访问控制
     【相关依赖】用户模块，认证中间件
     【修改内容】
        - 定义 Agent 相关权限点（create, edit, delete, publish, review, remove）
        - 实现权限装饰器（@require_permission）
        - 实现角色 - 权限映射
        - 集成到 API 路由

- [ ] 5.2 实现二次验证（2FA）
     【目标对象】`app/infrastructure/security/2fa.py`
     【修改目的】敏感操作的二次验证
     【修改方式】支持多种 2FA 方式
     【相关依赖】通知模块，缓存服务
     【修改内容】
        - 邮箱验证码发送和验证
        - 短信验证码发送和验证
        - TOTP 验证码生成和验证
        - 2FA 状态管理（启用/禁用）

- [ ] 5.3 实现域名白名单校验
     【目标对象】`app/infrastructure/security/domain_validator.py`
     【修改目的】Widget域名访问控制
     【修改方式】HTTP Referer 头校验
     【相关依赖】缓存服务
     【修改内容】
        - 从 HTTP 请求提取 Referer 域名
        - 精确匹配和通配符匹配算法
        - 空表处理（允许所有域名）
        - 校验失败返回 403 Forbidden

- [ ] 5.4 实现调用限额控制
     【目标对象】`app/infrastructure/security/rate_limiter.py`
     【修改目的】Widget 每日调用次数限制
     【修改方式】Redis 计数器 + 过期时间
     【相关依赖】Redis
     【修改内容】
        - 每日零点重置计数器
        - 实时统计调用次数
        - 超限拒绝并返回 429 Too Many Requests
        - 支持动态调整限额

### 阶段六：缓存与性能优化

- [ ] 6.1 实现 Redis 缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升查询性能
     【修改方式】使用 Redis 缓存热点数据
     【相关依赖】Redis
     【修改内容】
        - 热门 Agent 列表缓存（TTL = 5 分钟）
        - Widget 配置缓存（TTL = 10 分钟）
        - 已发布版本快照缓存（TTL = 30 分钟）
        - 缓存失效和更新机制

- [ ] 6.2 实现数据库索引优化
     【目标对象】数据库迁移脚本
     【修改目的】优化查询性能
     【修改方式】Alembic 迁移脚本添加索引
     【相关依赖】Alembic
     【修改内容】
        - agents 表：user_id、name、status 索引
        - agent_versions 表：agent_id、version_number、publish_status 索引
        - agent_widgets 表：agent_id、public_id 索引
        - workspace_agents 表：user_id、agent_id 索引

- [ ] 6.3 实现批量操作
     【目标对象】`app/application/agent/batch_operations.py`
     【修改目的】支持批量操作提升效率
     【修改方式】批量数据库操作
     【相关依赖】AgentRepository
     【修改内容】
        - 批量创建 Agent
        - 批量下架 Agent
        - 批量删除 Agent
        - 事务保证数据一致性

### 阶段七：市场发布与可见性

- [ ] 7.1 实现市场可见性控制
     【目标对象】`app/application/agent/market_visibility.py`
     【修改目的】控制 Agent 在市场的可见性
     【修改方式】基于发布状态过滤
     【相关依赖】VersionService
     【修改内容】
        - 仅 PUBLISHED 状态的 Agent 对市场可见
        - 市场列表查询（支持搜索、分类、排序）
        - 市场详情页展示
        - 添加到工作空间功能

- [ ] 7.2 实现审核拒绝通知
     【目标对象】`app/infrastructure/notification/review_notification.py`
     【修改目的】审核结果通知用户
     【修改方式】邮件 + 站内信
     【相关依赖】通知模块，用户模块
     【修改内容】
        - 审核通过通知
        - 审核拒绝通知（包含拒绝原因模板和自定义说明）
        - 重新提交审核提醒

- [ ] 7.3 实现 Widget调用限额实时校验
     【目标对象】`app/interfaces/api/v1/public/widgets/chat.py`
     【修改目的】对话前校验调用限额
     【修改方式】前置校验中间件
     【相关依赖】RateLimiter, WidgetService
     【修改内容】
        - 检查当日剩余调用次数
        - 未超限才允许对话
        - 对话成功后增加计数

### 阶段八：测试与质量保证

- [ ] 8.1 编写单元测试
     【目标对象】`tests/unit/test_agent_*.py`
     【修改目的】确保各模块功能正确性
     【修改方式】使用 pytest
     【相关依赖】pytest, pytest-mock
     【修改内容】
        - 测试 Agent 创建、更新、删除逻辑
        - 测试版本号自动生成规则
        - 测试版本状态机转换
        - 测试域名白名单匹配算法
        - 测试调用限额控制
        - 测试工具和知识库权限校验

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_agent_api.py`
     【修改目的】确保 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, TestClient
     【修改内容】
        - 测试 Agent CRUD API
        - 测试版本发布和审核 API
        - 测试 Widget 管理和嵌入代码生成
        - 测试工作空间操作 API
        - 测试认证和权限控制
        - 测试并发创建多个版本的场景

- [ ] 8.3 编写性能测试
     【目标对象】`tests/performance/test_agent_performance.py`
     【修改目的】验证性能指标是否达标
     【修改方式】使用 locust 或 pytest-benchmark
     【相关依赖】locust 或 pytest-benchmark
     【修改内容】
        - 压测 Agent 创建接口（目标 < 500ms）
        - 压测 Agent 查询接口（目标 < 200ms）
        - 压测 Widget 对话接口（目标 < 1s）
        - 测试并发 1000 QPS 下的稳定性

- [ ] 8.4 编写安全测试
     【目标对象】`tests/security/test_agent_security.py`
     【修改目的】验证安全机制有效性
     【修改方式】模拟攻击场景
     【相关依赖】pytest
     【修改内容】
        - 测试越权访问（访问其他用户的 Agent）
        - 测试域名白名单绕过攻击
        - 测试调用限额绕过攻击
        - 测试 SQL 注入防护
        - 测试 XSS 攻击防护（Widget 嵌入代码）

### 阶段九：监控与审计

- [ ] 9.1 实现操作日志记录
     【目标对象】`app/infrastructure/logging/audit_log.py`
     【修改目的】记录所有敏感操作
     【修改方式】AOP 切面编程
     【相关依赖】日志模块
     【修改内容】
        - 记录 Agent 创建、删除、发布操作
        - 记录审核操作（审核人、时间、意见）
        - 记录 Widget 配置变更
        - 支持日志查询和导出

- [ ] 9.2 实现 Widget调用日志
     【目标对象】`app/infrastructure/logging/widget_log.py`
     【修改目的】记录 Widget调用详情
     【修改方式】异步日志写入
     【相关依赖】日志模块，消息队列
     【修改内容】
        - 记录调用域名、时间、耗时、状态
        - 统计每日调用次数
        - 支持异常调用分析

- [ ] 9.3 实现监控指标
     【目标对象】`app/infrastructure/monitoring/metrics.py`
     【修改目的】实时监控 API 性能
     【修改方式】Prometheus + Grafana
     【相关依赖】prometheus_client
     【修改内容】
        - API 延迟直方图
        - API 错误率计数器
        - Widget调用量统计
        - 版本发布频率统计

### 阶段十：文档与部署

- [ ] 10.1 编写 API 文档
     【目标对象】API 文档（Swagger/OpenAPI）
     【修改目的】提供完整的 API 使用说明
     【修改方式】FastAPI 自动生成 + 手动补充
     【相关依赖】FastAPI, Swagger UI
     【修改内容】
        - 所有端点的请求/响应示例
        - 错误码说明
        - 认证方式说明
        - 速率限制说明

- [ ] 10.2 编写部署文档
     【目标对象】docs/deployment/agent_management.md
     【修改目的】指导生产环境部署
     【修改方式】Markdown 文档
     【相关依赖】无
     【修改内容】
        - 依赖服务（PostgreSQL, Redis）
        - 环境变量配置
        - Docker 部署方案
        - 性能调优建议

- [ ] 10.3 编写用户使用指南
     【目标对象】docs/user_guide/agent_management.md
     【修改目的】帮助用户快速上手
     【修改方式】Markdown 文档
     【相关依赖】无
     【修改内容】
        - 创建第一个 Agent
        - 配置工具和知识库
        - 发布到市场
        - 创建和嵌入 Widget
        - 工作空间使用
