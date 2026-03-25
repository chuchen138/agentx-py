# Tool Integration 技术设计

## 概述

工具集成模块采用状态机模式、处理器链模式和事件驱动架构，实现工具从接入、审核、部署到发布、安装的全流程自动化管理。基于 Python FastAPI 框架实现，使用 asyncio 进行异步处理。

## 技术架构

系统采用四层架构：
- **Interface Layer（接口层）**：FastAPI 路由，接收外部 HTTP 请求
  - 路径：`app/api/v1/tools/` - 工具管理 API
  - 路径：`app/api/v1/admin/tools/` - 管理员工具管理 API
- **Application Layer（应用层）**：用例编排、业务流程、状态机管理
  - 路径：`app/application/tool/` - 工具应用服务
- **Domain Layer（领域层）**：领域模型、业务规则、状态处理器
  - 路径：`app/domain/tool/` - 领域模型和服务
  - 路径：`app/domain/tool/state_machine/` - 状态机和处理器
- **Infrastructure Layer（基础设施层）**：数据库持久化、外部服务集成（Docker、GitHub、MCP）
  - 路径：`app/infrastructure/dependency_injection.py` - 依赖注入配置

## 状态机模式设计

### 状态定义

工具采用状态机模式管理接入生命周期：WAITING_REVIEW（等待审核）、GITHUB_URL_VALIDATE（GitHub URL 验证中）、DEPLOYING（工具部署中）、FETCHING_TOOLS（获取工具列表中）、MANUAL_REVIEW（人工审核中）、APPROVED（审核通过）、FAILED（审核失败）。

### 状态流转规则

- WAITING_REVIEW：→ GITHUB_URL_VALIDATE（自动触发）
- GITHUB_URL_VALIDATE：验证成功 → DEPLOYING；失败 → FAILED
- DEPLOYING：成功 → FETCHING_TOOLS；失败 → FAILED
- FETCHING_TOOLS：成功 → MANUAL_REVIEW；失败 → FAILED
- MANUAL_REVIEW：通过 → APPROVED；拒绝 → FAILED
- APPROVED：审核通过后自动为创建者安装工具

## 处理器链模式

### 状态处理器实现

- **WaitingReviewProcessor**：处理等待审核状态，自动触发进入审核流程
  - 路径：`app/domain/tool/state_machine/processors/waiting_review_processor.py`
- **FetchingToolsProcessor**：处理获取工具状态，解析 GitHub URL 或 Zip 包
  - 路径：`app/domain/tool/state_machine/processors/fetching_tools_processor.py`
- **GithubUrlValidateProcessor**：验证 GitHub URL，存储仓库信息，失败时记录原因
  - 路径：`app/domain/tool/state_machine/processors/github_url_validate_processor.py`
- **DeployingProcessor**：部署工具到审核容器，配置网络和环境变量
  - 路径：`app/domain/tool/state_machine/processors/deploying_processor.py`
- **PublishingProcessor**：处理工具发布流程，更新工具状态为已发布
  - 路径：`app/domain/tool/state_machine/processors/publishing_processor.py`

### 处理器链执行

ToolStateStateMachineAppService 管理处理器注册和执行，使用字典存储状态处理器。提交工具进行状态处理时，异步执行状态转换（使用 asyncio.create_task）。如果进入手动审核状态则暂停自动流转，否则递归处理下一个状态。处理失败时更新为 FAILED 状态并记录错误堆栈。

## 核心应用服务

### ToolAppService

负责工具 CRUD 操作、工具市场管理（上架、查询、安装、卸载）、工具版本管理和调用状态机进行状态转换。使用依赖注入获取仓储和服务。
- 路径：`app/application/tool/tool_app_service.py`

### ToolVersionService

负责工具版本管理，包括创建版本、发布版本、回滚版本等操作。
- 路径：`app/application/tool/tool_app_service.py`

### ToolStateStateMachineAppService

管理应用层状态处理器注册、提供状态转换统一入口、协调处理器链执行、处理状态机异常和失败。使用 asyncio.Lock 确保并发安全。
- 路径：`app/application/tool/tool_app_service.py`

### ToolAssembler

负责领域模型和 DTO 之间的转换。
- 路径：`app/application/tool/assembler.py`

## 数据模型设计

### ToolEntity

包含工具 ID、创建者 ID、工具名称、工具描述、GitHub 仓库 URL、工具状态、安装命令、MCP 服务器名称、工具定义列表、仓库信息和失败信息等。
- 路径：`app/domain/tool/model.py`

### ToolVersionEntity

包含版本 ID、工具 ID、用户 ID、版本号、公开状态、更新日志、MCP 服务器名称和工具描述等。
- 路径：`app/domain/tool/model.py`

### UserToolEntity

包含用户工具 ID、用户 ID、工具 ID、版本号、MCP 服务器名称等。
- 路径：`app/domain/tool/model.py`

### 枚举类型

- **ToolType**：工具类型，如 MCP
- **UploadType**：上传类型，如 GITHUB、ZIP
- **ToolStatus**：工具状态，如 WAITING_REVIEW、FETCHING_TOOLS、GITHUB_URL_VALIDATION、DEPLOYING、PUBLISHING、PUBLISHED、REJECTED
- **ToolVersionStatus**：版本状态，如 DRAFT、PUBLISHED、ARCHIVED
- 路径：`app/domain/tool/enums.py`

## 外部集成接口

### GitHubService

验证 GitHub 仓库引用和路径，传递完整仓库名、所有者、仓库名、引用和路径信息。使用 httpx 异步客户端，实现指数退避重试和速率限制处理。

### MCPGatewayService

部署工具到容器和从容器获取工具列表。使用 mcp Python 库作为 MCP 协议客户端，支持连接池和自动重连。

### ReviewContainerService

获取审核容器连接信息，包含 IP 地址和端口。与容器管理模块集成，动态分配和回收容器资源。

### DockerClientService

封装 Docker SDK for Python，实现镜像构建、容器创建启动、状态监控、日志收集和资源清理。

## 关键设计决策

### 状态机模式

**选择原因**：工具接入流程复杂，涉及多个状态和转换；状态转换逻辑需要可扩展和可维护；失败状态需要清晰定义和处理。
**优势**：状态转换逻辑清晰，易于理解和维护；新增状态和处理器无需修改现有代码；失败状态处理统一。

### 处理器链模式

**选择原因**：每个状态的处理逻辑独立且差异较大；需要支持依赖注入和测试；处理顺序需要可配置。
**优势**：单一职责，易于测试，支持灵活的状态流转逻辑。

### 异步处理

**选择原因**：长时间运行的操作不应阻塞用户请求；状态转换涉及多个步骤，需要异步执行；提高系统吞吐量。
**优势**：提升用户体验，提高系统吞吐量，支持并发处理。使用 asyncio 实现轻量级异步。

### 审核容器隔离

**选择原因**：工具审核需要在隔离环境中进行，避免影响生产环境；确保安全扫描和验证的可靠性。
**优势**：提升系统安全性，隔离未审核的工具，审核通过后平滑迁移到生产环境。

## 扩展性设计

### 新增状态处理器

新增状态只需三步：在 ToolStatus 中新增状态枚举；实现 AppToolStateProcessor 接口（定义 process 异步方法）；在 ToolStateStateMachineAppService.init() 中注册处理器到字典。

### 新增工具接入渠道

扩展 installCommand 结构，支持多种配置方式；新增状态处理器，支持私有 Git 仓库验证（如 GitLab、Gitee）；实现对应的 RepositoryService 接口。

### 新增 MCP 协议版本

在 ToolDefinition 中新增 protocol_version 字段，支持多版本协议解析；在 McpClient 中实现版本协商机制；在工具渲染层根据协议版本选择不同的展示方式。

### RAG 集成扩展

工具可声明需要 RAG 增强，平台自动为工具配置向量数据库连接；工具定义中包含知识库索引配置；RAG 服务为工具提供文档检索和知识增强能力。

## 性能优化策略

- **异步状态处理**：使用 asyncio 避免阻塞用户请求，状态处理任务后台执行
- **状态处理器缓存**：缓存在字典中，避免重复实例化，单例模式
- **分页查询**：工具市场采用分页查询（默认每页 20 条），避免一次性加载大量数据
- **批量查询**：减少数据库访问次数，使用 SQLAlchemy 的 joinedload 预加载关联数据
- **Redis 缓存**：工具列表和详情缓存（TTL 5-10 分钟），MCP 工具列表缓存
- **连接池**：数据库连接池（最大 20 连接）、MCP 连接池、HTTP 连接池
- **负载量化**：监控系统负载，超过阈值时限制新工具提交速率

## 安全性设计

- **GitHub URL 验证**：验证仓库存在性和可访问性、引用有效性和路径有效性、URL 白名单防止 SSRF
- **代码安全扫描**：部署前使用 bandit 进行静态代码分析，检测安全漏洞和硬编码密钥
- **沙箱执行**：工具在隔离容器中运行，限制文件系统、网络和系统调用
- **审核容器隔离**：工具部署到专用的审核容器，与生产环境隔离
- **工具定义获取**：仅从审核容器获取，使用标准的 MCP 协议，参数严格验证
- **权限控制**：用户只能访问和操作自己的工具，管理员拥有工具审核权限
- **日志脱敏**：审核日志隐藏密钥和敏感信息，双人复核机制
- **注入攻击防护**：防止命令注入、SQL 注入、路径遍历攻击

## 监控与日志

- **状态转换日志**：记录每个状态转换的详细信息（工具 ID、旧状态、新状态、时间戳、耗时）
- **失败原因记录**：工具失败时记录详细失败原因和错误堆栈，支持追溯
- **操作审计**：记录用户的关键操作（创建、更新、删除、安装、卸载），包含用户 ID、IP 地址、时间戳
- **性能指标**：收集 API 响应时间、状态机处理时间、数据库查询延迟，使用 Prometheus 导出
- **错误监控**：异常捕获和分类，错误率超过阈值时告警（集成 Sentry 或类似服务）
- **安全事件监控**：代码扫描告警、审核拒绝事件、认证失败事件记录和通知

## 技术栈

- **语言**：Python 3.10+
- **框架**：FastAPI 0.100+
- **数据库**：MySQL 8.0+
- **ORM**：SQLAlchemy 2.0+ with AsyncIO
- **异步处理**：asyncio, aiohttp
- **序列化**：Pydantic V2
- **缓存**：Redis 7.0+
- **容器**：Docker SDK for Python
- **MCP 协议**：mcp Python 库
- **HTTP 客户端**：httpx
- **消息队列**：Celery + RabbitMQ（可选，用于异步任务）
- **监控**：Prometheus + Grafana
- **日志**：structlog（结构化日志）
