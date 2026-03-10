# Tool Integration 技术设计

## 概述

工具集成模块采用状态机模式、处理器链模式和事件驱动架构，实现工具从接入、审核、部署到发布、安装的全流程自动化管理。

## 技术架构

系统采用四层架构：Interface Layer（接收外部请求）、Application Layer（业务流程编排、状态机管理）、Domain Layer（领域模型封装）、Infrastructure Layer（外部服务集成、数据持久化）。

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

- **AppWaitingReviewProcessor**：处理等待审核状态
- **AppGithubUrlValidateProcessor**：验证 GitHub URL，存储仓库信息
- **AppDeployingProcessor**：部署工具到审核容器
- **AppFetchingToolsProcessor**：获取并存储工具定义
- **AppManualReviewProcessor**：等待人工审核，不自动流转

### 处理器链执行

ToolStateStateMachineAppService 管理处理器注册和执行，使用 Map 存储状态处理器。提交工具进行状态处理时，异步执行状态转换。如果进入手动审核状态则暂停自动流转，否则递归处理下一个状态。处理失败时更新为 FAILED 状态。

## 核心应用服务

### ToolAppService

负责工具 CRUD 操作、工具市场管理（上架、查询、安装、卸载）、工具版本管理和调用状态机进行状态转换。

### ToolStateStateMachineAppService

管理应用层状态处理器注册、提供状态转换统一入口、协调处理器链执行、处理状态机异常和失败。

## 数据模型设计

### ToolEntity

包含工具 ID、创建者 ID、工具名称、工具描述、GitHub 仓库 URL、工具状态、安装命令、MCP 服务器名称、工具定义列表、仓库信息和失败信息等。

### ToolVersionEntity

包含版本 ID、工具 ID、用户 ID、版本号、公开状态、更新日志、MCP 服务器名称和工具描述等。

### UserToolEntity

包含用户工具 ID、用户 ID、工具 ID、版本号、MCP 服务器名称等。

## 外部集成接口

### GitHubService

验证 GitHub 仓库引用和路径，传递完整仓库名、所有者、仓库名、引用和路径信息。

### MCPGatewayService

部署工具到容器和从容器获取工具列表。

### ReviewContainerService

获取审核容器连接信息，包含 IP 地址和端口。

## 关键设计决策

### 状态机模式

**选择原因**：工具接入流程复杂，涉及多个状态和转换；状态转换逻辑需要可扩展和可维护；失败状态需要清晰定义和处理。**优势**：状态转换逻辑清晰，易于理解和维护；新增状态和处理器无需修改现有代码；失败状态处理统一。

### 处理器链模式

**选择原因**：每个状态的处理逻辑独立且差异较大；需要支持依赖注入和测试；处理顺序需要可配置。**优势**：单一职责，易于测试，支持灵活的状态流转逻辑。

### 异步处理

**选择原因**：长时间运行的操作不应阻塞用户请求；状态转换涉及多个步骤，需要异步执行。**优势**：提升用户体验，提高系统吞吐量，支持并发处理。

### 审核容器隔离

**选择原因**：工具审核需要在隔离环境中进行，避免影响生产环境。**优势**：提升系统安全性，隔离未审核的工具，审核通过后平滑迁移到生产环境。

## 扩展性设计

### 新增状态处理器

新增状态只需三步：在 ToolStatus 中新增状态；实现 AppToolStateProcessor 接口；在 ToolStateStateMachineAppService.init() 中注册处理器。

### 新增工具接入渠道

扩展 installCommand 结构，支持多种配置方式；新增状态处理器，支持私有 Git 仓库验证。

### 新增 MCP 协议版本

在 ToolDefinition 中新增协议版本字段，支持多版本协议解析，在工具渲染层根据协议版本选择不同的展示方式。

## 性能优化策略

- 异步状态处理：避免阻塞用户请求
- 状态处理器缓存：缓存在 Map 中，避免重复实例化
- 分页查询：工具市场采用分页查询，避免一次性加载大量数据
- 批量查询：减少数据库访问

## 安全性设计

- GitHub URL 验证：验证仓库存在性和可访问性、引用有效性和路径有效性
- 审核容器隔离：工具部署到专用的审核容器，与生产环境隔离
- 工具定义获取：仅从审核容器获取，使用标准的 MCP 协议
- 权限控制：用户只能访问和操作自己的工具，管理员拥有工具审核权限

## 监控与日志

- 状态转换日志：记录每个状态转换的详细信息
- 失败原因记录：工具失败时记录详细失败原因
- 操作审计：记录用户的关键操作，支持审计和追溯

## 技术栈

- **语言**：Java 17
- **框架**：Spring Boot 3.x
- **数据库**：MySQL
- **ORM**：MyBatis Plus
- **异步处理**：ThreadPoolExecutor
- **序列化**：Jackson
