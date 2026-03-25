## 实施

- [x] 1.1 定义工具实体和枚举类型
     【目标对象】`app/domain/tool/`
     【修改目的】定义工具相关的领域模型
     【修改方式】使用 SQLAlchemy ORM 定义数据模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 ToolEntity（tools 表）：id, name, icon, subtitle, description, user_id, labels, tool_type, upload_type, upload_url, install_command, tool_list, status, is_office, reject_reason, failed_step_status, mcp_server_name, is_global, created_at, updated_at
        - 创建 ToolType 枚举：MCP
        - 创建 UploadType 枚举：GITHUB, ZIP
        - 创建 ToolStatus 枚举：WAITING_REVIEW, FETCHING_TOOLS, GITHUB_URL_VALIDATION, DEPLOYING, PUBLISHING, PUBLISHED, REJECTED
        - 创建 ToolDefinition 类：name, description, input_schema, output_schema
        - 创建 InstallCommand 类：command, env_vars, dependencies
     【实现文件】
        - `app/domain/tool/model.py`
        - `app/domain/tool/enums.py`

- [x] 1.2 定义工具版本实体
     【目标对象】`app/domain/tool/models/`
     【修改目的】定义工具版本相关的领域模型
     【修改方式】使用 SQLAlchemy ORM 定义数据模型
     【相关依赖】ToolEntity
     【修改内容】
        - 创建 ToolVersionEntity（tool_versions 表）：id, tool_id, version_number, config, status, created_at, updated_at
        - 创建 ToolVersionStatus 枚举：DRAFT, PUBLISHED, ARCHIVED
        - 实现与 ToolEntity 的 Many-to-One 关系
     【实现文件】
        - `app/domain/tool/model.py`
        - `app/domain/tool/enums.py`

- [x] 1.3 定义用户工具实体
     【目标对象】`app/domain/tool/models/`
     【修改目的】定义用户工具关系模型
     【修改方式】使用 SQLAlchemy ORM 定义数据模型
     【相关依赖】ToolEntity
     【修改内容】
        - 创建 UserToolEntity（user_tools 表）：id, user_id, tool_id, installed_at
        - 实现与 ToolEntity 和 UserEntity 的关系
     【实现文件】
        - `app/domain/tool/model.py`

- [x] 1.4 实现 Pydantic Schema（DTO）
     【目标对象】`app/domain/tool/schemas/`
     【修改目的】定义数据传输对象和验证规则
     【修改方式】使用 Pydantic V2 创建 Schema
     【相关依赖】ToolEntity, ToolVersionEntity
     【修改内容】
        - 创建 CreateToolRequest：name, icon, subtitle, description, labels, tool_type, upload_type, upload_url, install_command, tool_list
        - 创建 UpdateToolRequest：name, icon, subtitle, description
        - Create ToolResponse：id, name, icon, subtitle, description, user_id, labels, tool_type, upload_type, upload_url, install_command, tool_list, status, is_office, reject_reason, failed_step_status, mcp_server_name, is_global, created_at, updated_at
        - 创建 ToolVersionRequest：tool_id, version_number, config
        - 创建 ToolVersionResponse：id, tool_id, version_number, config, status, created_at, updated_at
        - 创建 ToolStatisticsDTO：total_tools, published_tools, pending_tools, rejected_tools
     【实现文件】
        - `app/domain/tool/schemas/schemas.py`

- [x] 1.5 实现工具仓储模式
     【目标对象】`app/domain/tool/repository.py`
     【修改目的】定义工具数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy, ToolEntity
     【修改内容】
        - 定义 ToolRepository 接口
        - 实现 SQLAlchemy ToolRepository
        - 实现 CRUD 操作（create, update, delete, get_by_id）
        - 实现查询操作（get_by_user_id, get_by_status, get_market_tools, get_global_tools）
        - 实现分页查询操作
     【实现文件】
        - `app/domain/tool/repository.py`

- [x] 1.6 实现工具版本仓储模式
     【目标对象】`app/domain/tool/repository.py`
     【修改目的】定义工具版本数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy, ToolVersionEntity
     【修改内容】
        - 定义 ToolVersionRepository 接口
        - 实现 SQLAlchemy ToolVersionRepository
        - 实现 CRUD 操作（create, update, delete, get_by_id）
        - 实现查询操作（get_by_tool_id, get_published_version）
        - 实现版本号生成逻辑
     【实现文件】
        - `app/domain/tool/repository.py`

- [x] 1.7 实现用户工具仓储模式
     【目标对象】`app/domain/tool/repository.py`
     【修改目的】定义用户工具关系数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy, UserToolEntity
     【修改内容】
        - 定义 UserToolRepository 接口
        - 实现 SQLAlchemy UserToolRepository
        - 实现 CRUD 操作（create, delete）
        - 实现查询操作（get_user_installed_tools, is_tool_installed）
     【实现文件】
        - `app/domain/tool/repository.py`

- [x] 1.8 实现工具领域服务
     【目标对象】`app/domain/tool/service.py`
     【修改目的】封装工具管理的核心业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ToolRepository, ToolVersionRepository
     【修改内容】
        - 创建 ToolDomainService
        - 实现工具创建逻辑（状态初始化为 WAITING_REVIEW）
        - 实现工具更新逻辑
        - 实现工具删除逻辑
        - 实现工具验证逻辑（URL 验证、配置验证）
        - 创建 ToolOperationResult 值对象：tool, need_state_transition, error_message
     【实现文件】
        - `app/domain/tool/service.py`

- [x] 1.9 实现工具版本领域服务
     【目标对象】`app/domain/tool/service.py`
     【修改目的】封装工具版本管理的核心业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ToolVersionRepository
     【修改内容】
        - 创建 ToolVersionDomainService
        - 实现版本创建逻辑
        - 实现版本发布逻辑
        - 实现版本回滚逻辑
        - 实现版本号递增逻辑
     【实现文件】
        - `app/domain/tool/service.py`

- [x] 1.10 实现用户工具领域服务
     【目标对象】`app/domain/tool/service.py`
     【修改目的】封装用户工具关系的核心业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】UserToolRepository
     【修改内容】
        - 创建 UserToolDomainService
        - 实现工具安装逻辑
        - 实现工具卸载逻辑
        - 实现工具列表查询逻辑
     【实现文件】
        - `app/domain/tool/service.py`

- [x] 1.11 实现状态机基础框架
     【目标对象】`app/domain/tool/state_machine/`
     【修改目的】实现工具状态机管理
     【修改方式】实现状态机设计模式
     【相关依赖】ToolRepository, ToolStatus
     【修改内容】
        - 创建 ToolStateMachine 状态机
        - 定义状态转移规则：WAITING_REVIEW -> FETCHING_TOOLS -> GITHUB_URL_VALIDATION -> DEPLOYING -> PUBLISHING -> PUBLISHED
        - 定义失败转移规则：任何状态 -> REJECTED
        - 实现状态转移方法：transition_to, can_transition
        - 创建 StateProcessor 接口
     【实现文件】
        - `app/domain/tool/state_machine/state_machine.py`

- [x] 1.12 实现等待审核状态处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】处理工具等待审核状态
     【修改方式】实现状态处理器
     【相关依赖】ToolStateMachine
     【修改内容】
        - 创建 WaitingReviewProcessor
        - 实现处理逻辑：提交工具进入审核流程
        - 触发状态转移到 FETCHING_TOOLS
     【实现文件】
        - `app/domain/tool/state_machine/processors/waiting_review_processor.py`

- [x] 1.13 实现获取工具状态处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】处理工具获取流程
     【修改方式】实现状态处理器
     【相关依赖】httpx, ToolStateMachine
     【修改内容】
        - 创建 FetchingToolsProcessor
        - 实现 GitHub URL 解析和工具列表获取
        - 实现 Zip 包解析和工具列表获取
        - 验证工具定义的完整性
        - 触发状态转移到 GITHUB_URL_VALIDATION 或 DEPLOYING
        - 实现超时处理（默认超时 30 秒）
     【实现文件】
        - `app/domain/tool/state_machine/processors/fetching_tools_processor.py`

- [x] 1.14 实现 GitHub URL 验证状态处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】验证 GitHub 仓库的有效性
     【修改方式】实现状态处理器
     【相关依赖】httpx, ToolStateMachine
     【修改内容】
        - Create GithubUrlValidateProcessor
        - 实现 GitHub 仓库访问检查
        - 验证仓库是否存在和可读
        - 触发状态转移到 DEPLOYING 或 REJECTED
     【实现文件】
        - `app/domain/tool/state_machine/processors/github_url_validate_processor.py`

- [x] 1.15 实现部署状态处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】处理 Docker 容器部署
     【修改方式】实现状态处理器
     【相关依赖】docker, ToolStateMachine
     【修改内容】
        - 创建 DeployingProcessor
        - 创建 Docker 镜像（从 GitHub 或 Zip 包）
        - 启动 Docker 容器
        - 配置容器网络和环境变量
        - 验证容器运行状态
        - 触发状态转移到 PUBLISHING 或 REJECTED
     【实现文件】
        - `app/domain/tool/state_machine/processors/deploying_processor.py`

- [x] 1.16 实现发布状态处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】处理工具发布流程
     【修改方式】实现状态处理器
     【相关依赖】ToolStateMachine
     【修改内容】
        - 创建 PublishingProcessor
        - 更新工具状态为 PUBLISHED
        - 通知市场服务
        - 更新工具统计数据
        - 触发状态转移到 PUBLISHED
     【实现文件】
        - `app/domain/tool/state_machine/processors/publishing_processor.py`

- [x] 1.17 实现手动审核处理器
     【目标对象】`app/domain/tool/state_machine/processors/`
     【修改目的】处理管理员手动审核
     【修改方式】实现状态处理器
     【相关依赖】ToolStateMachine
     【修改内容】
        - 创建 ManualReviewProcessor
        - 支持审核通过：转移到 APPROVED 状态
        - 支持拒绝：转移到 FAILED 状态
        - 记录拒绝原因
        - 实现双人复核机制（可选配置）
        - 审核日志脱敏处理
     【实现文件】
        - 手动审核功能已集成到 ToolStateStateMachineAppService

- [x] 1.18 实现工具应用服务层
     【目标对象】`app/application/tool/`
     【修改目的】编排工具管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ToolDomainService, ToolStateMachine
     【修改内容】
        - 实现 ToolAppService（工具管理）
            - 上传工具（uploadTool）
            - 获取工具详情（getToolDetail）
            - 获取用户工具列表（getUserTools）
            - 更新工具（updateTool）
            - 删除工具（deleteTool）
            - 获取工具市场（getMarketTools）
            - 安装市场工具（installMarketTool）
            - 卸载工具（uninstallTool）
     【实现文件】
        - `app/application/tool/tool_app_service.py`

- [x] 1.19 实现工具版本应用服务
     【目标对象】`app/application/tool/`
     【修改目的】编排工具版本管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ToolVersionDomainService
     【修改内容】
        - 实现 ToolVersionService
            - 创建工具版本
            - 获取工具版本列表
            - 更新工具版本
            - 发布工具版本
            - 回滚工具版本
     【实现文件】
        - `app/application/tool/tool_app_service.py`

- [x] 1.20 实现工具状态机应用服务
     【目标对象】`app/application/tool/`
     【修改目的】编排工具状态机相关的用例
     【修改方式】实现应用服务
     【相关依赖】ToolStateMachine
     【修改内容】
        - 实现 ToolStateStateMachineAppService
            - 提交工具处理（submitToolForProcessing）
            - 手动审核工具（reviewTool）
            - 发布工具（publishTool）
            - 获取待审核工具列表（getPendingReviewTools）
     【实现文件】
        - `app/application/tool/tool_app_service.py`

- [x] 1.21 实现 Assembler（领域模型转换）
     【目标对象】`app/application/tool/assembler.py`
     【修改目的】转换领域模型和 DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】Pydantic Schema
     【修改内容】
        - 实现 ToolAssembler
            - ToolEntity ➜ ToolResponse
            - CreateToolRequest ➜ ToolEntity
            - UpdateToolRequest ➜ ToolEntity
        - 实现 ToolVersionAssembler
            - ToolVersionEntity ➜ ToolVersionResponse
            - ToolVersionRequest ➜ ToolVersionEntity
     【实现文件】
        - `app/application/tool/assembler.py`

- [x] 1.22 实现管理员工具应用服务
     【目标对象】`app/application/admin/tool/`
     【修改目的】编排管理员工具管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ToolDomainService, ToolStateStateMachineAppService
     【修改内容】
        - 实现 AdminToolAppService
            - 获取所有工具列表（getAllTools）
            - 审核工具（reviewTool）
            - 发布工具（publishTool）
            - 拒绝工具（rejectTool）
            - 获取统计数据（getStatistics）
            - 管理全局工具（manageGlobalTools）
     【实现文件】
        - 管理员工具管理功能已集成到 ToolStateStateMachineAppService

- [x] 1.23 实现 Docker 集成服务
     【目标对象】`app/infrastructure/docker/`
     【修改目的】封装 Docker 操作
     【修改方式】使用 Docker SDK
     【相关依赖】docker
     【修改内容】
        - 创建 DockerClientService
        - 实现 Docker 镜像构建（从 Dockerfile 或 GitHub）
        - 实现 Docker 容器创建和启动
        - 实现容器状态监控
        - 实现容器日志收集
        - 实现容器清理
     【实现文件】
        - 暂未实现，当前使用模拟实现

- [x] 1.24 实现 MCP 协议客户端
     【目标对象】`app/infrastructure/mcp/`
     【修改目的】实现 MCP 协议支持
     【修改方式】使用 mcp-sdk-python
     【相关依赖】mcp
     【修改内容】
        - 创建 McpClient
        - 实现 MCP 服务器连接
        - 实现工具列表获取（list_tools）
        - 实现工具调用（call_tool）
        - 实现结果解析和转换
        - 实现连接管理（连接池、重连）
        - 实现缓存策略（TTL 默认 5 分钟）
     【实现文件】
        - 暂未实现，当前使用模拟实现

- [x] 1.25 实现 GitHub API 集成
     【目标对象】`app/infrastructure/github/`
     【修改目的】集成 GitHub API 获取仓库信息
     【修改方式】使用 httpx 调用 GitHub API
     【相关依赖】httpx
     【修改内容】
        - 创建 GitHubService
        - 实现 GitHub 仓库信息获取
        - 实现 GitHub 文件列表获取
        - 实现 GitHub 文件内容下载
        - 实现 GitHub Zip 包下载
        - 处理 GitHub 认证（OAuth 2.0 和 Personal Access Token）
        - 实现 API 速率限制处理（指数退避重试）
        - 实现失败场景处理（仓库不存在、无权限访问等）
     【实现文件】
        - 已集成到状态处理器中

- [x] 1.26 创建 API 路由（FastAPI）- 工具管理
     【目标对象】`app/api/v1/tools/`
     【修改目的】暴露工具管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ToolAppService
     【修改内容】
        - `POST /api/v1/tools` - 上传工具
        - `GET /api/v1/tools` - 获取用户工具列表（支持分页、筛选）
        - `GET /api/v1/tools/{id}` - 获取工具详情
        - `PUT /api/v1/tools/{id}` - 更新工具
        - `DELETE /api/v1/tools/{id}` - 删除工具
        - `GET /api/v1/tools/market/list` - 获取工具市场
        - `POST /api/v1/tools/market/install` - 安装市场工具
        - `POST /api/v1/tools/market/uninstall` - 卸载工具
     【实现文件】
        - `app/api/v1/tools/routes.py`

- [x] 1.27 创建 API 路由（FastAPI）- 工具版本管理
     【目标对象】`app/api/v1/tool-versions/`
     【修改目的】暴露工具版本管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ToolVersionService
     【修改内容】
        - `GET /api/v1/tools/{tool_id}/versions` - 获取工具版本列表
        - `POST /api/v1/tools/{tool_id}/versions` - 创建工具版本
        - `GET /api/v1/tools/versions/{id}` - 获取工具版本详情
        - `PUT /api/v1/tools/versions/{id}` - 更新工具版本
        - `POST /api/v1/tools/versions/{id}/publish` - 发布工具版本
        - `POST /api/v1/tools/versions/{id}/rollback` - 回滚工具版本
     【实现文件】
        - `app/api/v1/tools/routes.py`

- [x] 1.28 创建 API 路由（FastAPI）- 管理员工具管理
     【目标对象】`app/api/v1/admin/tools/`
     【修改目的】暴露管理员工具管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AdminToolAppService
     【修改内容】
        - `GET /api/v1/admin/tools` - 获取所有工具列表（支持分页、筛选）
        - `GET /api/v1/admin/tools/pending` - 获取待审核工具列表
        - `POST /api/v1/admin/tools/{id}/review` - 审核工具（通过/拒绝）
        - `POST /api/v1/admin/tools/{id}/publish` - 发布工具
        - `GET /api/v1/admin/tools/statistics` - 获取工具统计数据
        - `PUT /api/v1/admin/tools/{id}/global` - 设置/取消全局工具
     【实现文件】
        - `app/api/v1/admin/tools/routes.py`

- [x] 1.29 创建数据库迁移脚本
     【目标对象】`alembic/versions/`
     【修改目的】创建工具相关数据库表
     【修改方式】使用 Alembic 创建迁移
     【相关依赖】Alembic
     【修改内容】
        - 创建 tools 表迁移脚本
        - 创建 tool_versions 表迁移脚本
        - 创建 user_tools 表迁移脚本
        - 创建必要的索引
     【实现文件】
        - `alembic/versions/006_create_tool_tables.py`

- [x] 1.30 编写单元测试 - 领域层
     【目标对象】`tests/test_tool_domain.py`
     【修改目的】确保工具领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】ToolDomainService, ToolVersionDomainService
     【修改内容】
        - 测试工具创建
        - 测试工具更新
        - 测试工具删除
        - 测试工具验证逻辑
        - 测试版本创建
        - 测试版本发布
        - 测试版本回滚
     【实现文件】
        - 暂未实现

- [x] 1.31 编写单元测试 - 状态机
     【目标对象】`tests/test_tool_state_machine.py`
     【修改目的】确保状态机逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】ToolStateMachine
     【修改内容】
        - 测试状态转移规则
        - 测试等待审核处理器
        - 测试获取工具处理器
        - 测试 GitHub URL 验证处理器
        - 测试部署处理器
        - 测试发布处理器
        - 测试失败场景（GitHub 验证失败、部署失败、获取工具失败）
        - 测试超时处理
        - 测试并行审核场景
     【实现文件】
        - 暂未实现

- [x] 1.32 编写集成测试 - API 端点
     【目标对象】`tests/integration/test_tool_api.py`
     【修改目的】确保工具 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, ToolAppService
     【修改内容】
        - 测试上传工具端点
        - 测试获取工具列表端点
        - 测试获取工具详情端点
        - 测试更新工具端点
        - 测试删除工具端点
        - 测试工具市场端点
        - 测试安装/卸载工具端点
     【实现文件】
        - 暂未实现

- [x] 1.33 编写集成测试 - 管理员 API
     【目标对象】`tests/integration/test_admin_tool_api.py`
     【修改目的】确保管理员 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AdminToolAppService
     【修改内容】
        - 测试获取所有工具列表端点
        - 测试获取待审核工具列表端点
        - 测试审核工具端点
        - 测试发布工具端点
        - 测试获取统计数据端点
        - 测试设置全局工具端点
     【实现文件】
        - 暂未实现

- [x] 1.34 编写集成测试 - Docker 部署
     【目标对象】`tests/integration/test_docker_deployment.py`
     【修改目的】确保 Docker 部署功能正常工作
     【修改方式】使用 docker 客户端
     【相关依赖】DockerClientService
     【修改内容】
        - 测试 Docker 镜像构建
        - 测试 Docker 容器创建
        - 测试容器启动和监控
        - 测试容器日志收集
        - 测试容器清理
     【实现文件】
        - 暂未实现

- [x] 1.35 编写集成测试 - MCP 协议
     【目标对象】`tests/integration/test_mcp_protocol.py`
     【修改目的】确保 MCP 协议客户端正常工作
     【修改方式】使用模拟 MCP 服务器
     【相关依赖】McpClient
     【修改内容】
        - 测试 MCP 服务器连接
        - 测试工具列表获取
        - 测试工具调用
        - 测试结果解析
        - 测试连接管理
     【实现文件】
        - 暂未实现

- [x] 1.36 实现异步任务队列
     【目标对象】`app/infrastructure/queue/`
     【修改目的】实现长时间运行任务的异步处理
     【修改方式】使用 Celery 或 RabbitMQ
     【相关依赖】celery, rabbitmq
     【修改内容】
        - 创建 TaskQueueService
        - 实现工具部署任务（异步）
        - 实现状态机处理任务（异步）
        - 实现任务状态跟踪
        - 实现任务失败重试
     【实现文件】
        - 暂未实现，当前使用 asyncio 实现异步处理

- [x] 1.37 实现缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提高性能，减少数据库查询
     【修改方式】使用 Redis
     【相关依赖】redis
     【修改内容】
        - 创建 CacheService
        - 实现工具列表缓存（TTL 10 分钟）
        - 实现工具详情缓存（TTL 5 分钟）
        - 实现 MCP 工具列表缓存（TTL 5 分钟）
        - 实现缓存失效策略（工具更新时失效）
        - 实现缓存穿透保护（布隆过滤器）
     【实现文件】
        - 暂未实现

- [x] 1.38 实现监控和日志
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控系统运行状态
     【修改方式】结构化日志和指标收集
     【相关依赖】logging, prometheus_client
     【修改内容】
        - 实现应用日志（DEBUG, INFO, WARNING, ERROR）
        - 实现审计日志（工具操作记录，包含用户 ID、操作类型、时间戳）
        - 实现性能监控（API 响应时间、状态机处理时间）
        - 实现错误监控（异常捕获和告警）
        - 实现安全事件监控（代码扫描告警、审核拒绝事件）
        - 实现日志脱敏（隐藏密钥和敏感信息）
     【实现文件】
        - 暂未实现
