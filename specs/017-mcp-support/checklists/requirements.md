# MCP 支持实施清单

## 概述

本实施清单基于 spec.md 和 design.md，定义 MCP(模型上下文协议) 支持模块的具体实施步骤，包括 MCP 协议适配、服务器 URL 管理、容器集成、工具参数预设和 SSE 连接管理等功能。

## 实施

### 1. 数据模型层

- [ ] 1.1 定义 MCP 实体和数据模型
     【目标对象】`app/domain/mcp/model/`
     【修改目的】定义 MCP 相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 MCPServer 模型 (mcp_servers 表)
          * 字段:id, server_id, server_name, server_url, server_type, status, protocol_version, health_check_url, created_at, updated_at
          * 索引:idx_server_name, idx_server_type, idx_status
        - 创建 MCPTool 模型 (mcp_tools 表)
          * 字段:id, tool_id, server_id, tool_name, tool_description, parameters_schema, output_schema, is_global, container_template, created_at, updated_at
          * 索引:idx_tool_name, idx_server_id, idx_is_global
        - 创建 MCPConnection 模型 (mcp_connections 表)
          * 字段:id, connection_id, user_id, server_id, container_id, sse_url, status, created_at, last_active_at
          * 索引:idx_user_id, idx_server_id, idx_container_id
        - 创建 ToolParameterPreset 模型 (tool_parameter_presets 表)
          * 字段:id, preset_id, tool_id, preset_name, parameter_values, description, created_by, created_at
          * 索引:idx_tool_id, idx_created_by
        - 实现 Pydantic Schema
          * MCPServerDTO, MCPServerCreateRequest, MCPServerUpdateRequest
          * MCPToolDTO, MCPToolListRequest
          * MCPConnectionDTO
          * ToolParameterPresetDTO, ParameterPresetCreateRequest

- [ ] 1.2 实现 MCP 枚举和常量
     【目标对象】`app/domain/mcp/constant/`
     【修改目的】定义 MCP 相关枚举和常量
     【修改方式】使用 Python Enum 和常量类
     【相关依赖】无
     【修改内容】
        - 创建 MCPServerType 枚举
          * GLOBAL - 全局服务器
          * USER - 用户专用服务器
          * EXTERNAL - 外部服务器
        - 创建 MCPProtocolVersion 枚举
          * V1_0 - MCP 协议 1.0
          * V2_0 - MCP 协议 2.0
          * CUSTOM - 自定义版本
        - 创建 ConnectionStatus 枚举
          * CONNECTING - 连接中
          * CONNECTED - 已连接
          * DISCONNECTED - 已断开
          * FAILED - 失败
        - 创建 ContainerType 常量类
          * AUDIT_CONTAINER - 审核容器
          * USER_CONTAINER - 用户容器
          * TEMPORARY_CONTAINER - 临时容器

### 2. 仓储层

- [ ] 2.1 实现 MCP 服务器仓储模式
     【目标对象】`app/domain/mcp/repository.py`
     【修改目的】定义 MCP 服务器数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 MCPServerRepository 接口
        - 实现 SQLAlchemyMCPServerRepository
          * create(server_data) -> MCPServer
          * get_by_id(server_id) -> MCPServer
          * get_by_name(server_name) -> MCPServer
          * get_all_servers() -> List[MCPServer]
          * get_servers_by_type(server_type) -> List[MCPServer]
          * get_healthy_servers() -> List[MCPServer]
          * update_status(server_id, status)
          * delete(server_id)

- [ ] 2.2 实现 MCP 工具仓储模式
     【目标对象】`app/domain/mcp/repository.py`
     【修改目的】定义 MCP 工具数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 MCPToolRepository 接口
        - 实现 SQLAlchemyMCPToolRepository
          * create(tool_data) -> MCPTool
          * get_by_id(tool_id) -> MCPTool
          * get_by_name(tool_name) -> MCPTool
          * get_tools_by_server(server_id) -> List[MCPTool]
          * get_global_tools() -> List[MCPTool]
          * get_user_tools(user_id) -> List[MCPTool]
          * search_tools(keyword) -> List[MCPTool]
          * update_tool(tool_id, tool_data)
          * delete(tool_id)

- [ ] 2.3 实现连接仓储模式
     【目标对象】`app/domain/mcp/repository.py`
     【修改目的】定义 MCP 连接数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 MCPConnectionRepository 接口
        - 实现 SQLAlchemyMCPConnectionRepository
          * create(connection_data) -> MCPConnection
          * get_by_id(connection_id) -> MCPConnection
          * get_by_user_and_server(user_id, server_id) -> MCPConnection
          * get_active_connections(user_id) -> List[MCPConnection]
          * update_status(connection_id, status)
          * delete(connection_id)
          * cleanup_inactive_connections(timeout_seconds)

- [ ] 2.4 实现参数预设仓储模式
     【目标对象】`app/domain/mcp/repository.py`
     【修改目的】定义工具参数预设数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ToolParameterPresetRepository 接口
        - 实现 SQLAlchemyToolParameterPresetRepository
          * create(preset_data) -> ToolParameterPreset
          * get_by_id(preset_id) -> ToolParameterPreset
          * get_by_tool_id(tool_id) -> List[ToolParameterPreset]
          * get_by_user(user_id) -> List[ToolParameterPreset]
          * delete(preset_id)

### 3. 领域服务层

- [ ] 3.1 实现 MCP 协议适配器
     【目标对象】`app/domain/mcp/protocol_adapter.py`
     【修改目的】适配 MCP 协议标准，实现与 MCP 服务器的互操作
     【修改方式】使用策略模式处理不同协议版本
     【相关依赖】httpx, SSE Client
     【修改内容】
        - 创建 MCPProtocolAdapter 接口
          * connect(server_url) -> Connection
          * discover_tools() -> List[ToolDefinition]
          * call_tool(tool_name, arguments) -> ToolResult
          * disconnect()
        - 实现 MCPProtocolV1Adapter
          * 遵循 MCP 协议 1.0 规范
          * 实现工具发现
          * 实现工具调用
          * 实现事件处理
        - 实现 MCPProtocolV2Adapter
          * 遵循 MCP 协议 2.0 规范
          * 支持新特性
        - 实现 CustomMCPAdapter
          * 支持自定义 MCP 协议
        - 错误处理和异常转换:
          * MCPProtocolException
          * MCPTimeoutException
          * MCPConnectionException

- [ ] 3.2 实现 MCP 服务器管理器
     【目标对象】`app/domain/mcp/server_manager.py`
     【修改目的】管理 MCP 服务器的连接和状态
     【修改方式】使用单例模式
     【相关依赖】MCPServerRepository, HealthCheckService
     【修改内容】
        - 创建 MCPServerManager 类 (单例)
          * _servers: Dict[str, ServerInfo]
          * _health_checker: HealthCheckService
        - 实现方法:
          * register_server(server_config)
          * unregister_server(server_id)
          * get_server(server_id) -> ServerInfo
          * list_servers() -> List[ServerInfo]
          * get_healthy_server() -> ServerInfo
          * check_server_health(server_id) -> bool
          * get_server_url(server_id) -> str
        - 健康检查:
          * 定期检查服务器健康状态
          * 更新服务器状态
          * 故障告警

- [ ] 3.3 实现工具类型判断器
     【目标对象】`app/domain/mcp/tool_classifier.py`
     【修改目的】自动判断工具类型并选择连接策略
     【修改方式】使用规则引擎
     【相关依赖】MCPToolRepository
     【修改内容】
        - 创建 ToolClassifier 类
          * _tool_registry: MCPToolRepository
        - 实现方法:
          * classify_tool(tool_name) -> ToolType
            - 查询工具信息
            - 根据 isGlobal 标记判断
            - 无法判断时默认为 USER
          * get_connection_strategy(tool_type) -> ConnectionStrategy
            - GLOBAL -> AUDIT_CONTAINER
            - USER -> USER_CONTAINER
            - EXTERNAL -> DIRECT_CONNECTION
        - 容错处理:
          * 工具不存在时的降级策略
          * 日志记录

- [ ] 3.4 实现容器集成服务
     【目标对象】`app/domain/mcp/container_integration.py`
     【修改目的】与容器管理模块集成，为 MCP 工具提供容器化环境
     【修改方式】使用 Docker SDK
     【相关依赖】Docker SDK, ContainerManager
     【修改内容】
        - 创建 ContainerIntegrationService 类
          * _container_manager: ContainerManager
          * _active_containers: Dict[str, ContainerInfo]
        - 实现方法:
          * get_or_create_container(tool_id, user_id, container_type) -> ContainerInfo
            - 检查是否存在可用容器
            - 不存在则创建并启动
            - 等待容器就绪
          * check_container_status(container_id) -> ContainerStatus
          * build_sse_url(container_info) -> str
            - 获取容器 IP 和端口
            - 构建 SSE 连接 URL
          * release_container(container_id)
            - 停止容器
            - 删除容器
          * cleanup_temporary_containers()
        - 容器类型支持:
          * 审核容器 (全局工具)
          * 用户容器 (用户工具)
          * 临时容器 (一次性使用)
        - 自动恢复:
          * 容器失败时自动重启
          * 状态持久化

- [ ] 3.5 实现工具参数预设服务
     【目标对象】`app/domain/mcp/parameter_service.py`
     【修改目的】管理工具参数的预设配置
     【修改方式】使用 JSON Schema 验证
     【相关依赖】jsonschema, ToolParameterPresetRepository
     【修改内容】
        - 创建 ParameterPresetService 类
          * _preset_repository: ToolParameterPresetRepository
        - 实现方法:
          * create_preset(tool_id, preset_name, parameter_values, description, user_id) -> ParameterPreset
          * get_presets(tool_id) -> List[ParameterPreset]
          * get_preset(preset_id) -> ParameterPreset
          * apply_preset(preset_id, override_params) -> ValidatedParameters
          * validate_parameters(tool_id, parameters) -> ValidationResult
            - 类型校验
            - 范围校验
            - 必填项校验
          * serialize_parameters(parameters) -> MCPFormat
            - 转换为 MCP 协议格式
        - 参数模板:
          * 提供常用参数模板
          * 支持用户自定义模板

- [ ] 3.6 实现 SSE 连接管理器
     【目标对象】`app/domain/mcp/sse_manager.py`
     【修改目的】管理到 MCP 服务器的 SSE 实时连接
     【修改方式】使用 asyncio 和 SSE 客户端
     【相关依赖】httpx, asyncio, aiofiles
     【修改内容】
        - 创建 SSEConnectionManager 类
          * _connections: Dict[str, SSEConnection]
          * _event_handlers: Dict[event_type, EventHandler]
        - 实现方法:
          * connect(server_url, connection_id) -> SSEConnection
            - 建立 SSE 连接
            - 设置事件处理器
            - 启动心跳维护
          * disconnect(connection_id)
            - 关闭连接
            - 清理资源
          * send_event(connection_id, event_type, event_data)
          * receive_events(connection_id) -> AsyncIterator[Event]
          * rebuild_connection(connection_id)
            - 连接断开自动重连
            - 指数退避策略
        - 事件类型处理:
          * TOOL_LIST_EVENT - 工具列表
          * TOOL_CALL_EVENT - 工具调用
          * RESULT_RETURN_EVENT - 结果返回
          * ERROR_EVENT - 错误事件
          * STATUS_EVENT - 状态事件
        - 连接维护:
          * 心跳检测
          * 超时处理
          * 连接池管理

- [ ] 3.7 实现 URL 构建服务
     【目标对象】`app/domain/mcp/url_builder.py`
     【修改目的】构建标准的 MCP 服务器连接 URL
     【修改方式】使用 URL 构建库
     【相关依赖】urllib.parse
     【修改内容】
        - 创建 URLBuilderService 类
        - 实现方法:
          * build_server_url(server_host, server_port, path) -> str
          * build_sse_url(container_ip, container_port, endpoint) -> str
          * build_tool_call_url(base_url, tool_name) -> str
          * validate_url(url) -> ValidationResult
            - URL 格式验证
            - 协议验证 (http/https)
            - 可达性检查
          * normalize_url(url) -> str
        - URL 智能判断:
          * 根据工具类型选择 URL 前缀
          * 自动添加协议头

### 4. 应用服务层

- [ ] 4.1 实现 MCP 服务器应用服务
     【目标对象】`app/application/mcp/`
     【修改目的】编排 MCP 服务器管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】MCPServerRepository, MCPServerManager
     【修改内容】
        - 实现 MCPServerAppService
          * register_server(server_config) -> MCPServerDTO
          * unregister_server(server_id)
          * get_server(server_id) -> MCPServerDTO
          * list_servers(server_type) -> List[MCPServerDTO]
          * update_server(server_id, server_config) -> MCPServerDTO
          * check_server_health(server_id) -> HealthStatusDTO
          * get_server_url(server_id) -> str

- [ ] 4.2 实现 MCP 工具应用服务
     【目标对象】`app/application/mcp/`
     【修改目的】编排 MCP 工具管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】MCPToolRepository, ToolClassifier
     【修改内容】
        - 实现 MCPToolAppService
          * get_tool(tool_id) -> MCPToolDTO
          * get_tool_by_name(tool_name) -> MCPToolDTO
          * list_tools(server_id, is_global) -> List[MCPToolDTO]
          * search_tools(keyword) -> List[MCPToolDTO]
          * classify_tool(tool_name) -> ToolTypeDTO
          * get_tool_url(tool_name, user_id) -> str

- [ ] 4.3 实现 MCP 连接应用服务
     【目标对象】`app/application/mcp/`
     【修改目的】编排 MCP 连接管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】MCPConnectionRepository, SSEConnectionManager
     【修改内容】
        - 实现 MCPConnectionAppService
          * create_connection(user_id, server_id) -> MCPConnectionDTO
          * get_connection(connection_id) -> MCPConnectionDTO
          * list_user_connections(user_id) -> List[MCPConnectionDTO]
          * close_connection(connection_id)
          * rebuild_connection(connection_id) -> MCPConnectionDTO
          * cleanup_inactive_connections()

- [ ] 4.4 实现工具参数预设应用服务
     【目标对象】`app/application/mcp/`
     【修改目的】编排工具参数预设管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】ToolParameterPresetRepository, ParameterPresetService
     【修改内容】
        - 实现 ParameterPresetAppService
          * create_preset(tool_id, preset_config) -> ToolParameterPresetDTO
          * get_presets(tool_id) -> List[ToolParameterPresetDTO]
          * get_preset(preset_id) -> ToolParameterPresetDTO
          * apply_preset(preset_id, override_params) -> ValidatedParametersDTO
          * delete_preset(preset_id)

- [ ] 4.5 实现工具调用应用服务
     【目标对象】`app/application/mcp/`
     【修改目的】编排 MCP 工具调用相关的用例
     【修改方式】实现应用服务
     【相关依赖】MCPProtocolAdapter, ContainerIntegrationService, SSEConnectionManager
     【修改内容】
        - 实现 MCPToolCallAppService
          * call_tool(tool_name, arguments, user_id) -> ToolCallResultDTO
            - 判断工具类型
            - 获取或创建容器
            - 建立 SSE 连接
            - 调用工具
            - 返回结果
            - 清理容器 (如果是临时容器)
          * batch_call_tools(tool_calls) -> List[ToolCallResultDTO]
          * cancel_tool_call(call_id)

### 5. API 路由层

- [ ] 5.1 创建 MCP 服务器管理 API 路由
     【目标对象】`app/api/v1/mcp/servers/`
     【修改目的】暴露 MCP 服务器管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MCPServerAppService
     【修改内容】
        - `POST /api/v1/mcp/servers` - 注册 MCP 服务器
          * 请求:MCPServerCreateRequest
          * 响应:MCPServerDTO
        - `GET /api/v1/mcp/servers` - 获取服务器列表
          * 参数:server_type
          * 响应:List[MCPServerDTO]
        - `GET /api/v1/mcp/servers/{server_id}` - 获取服务器详情
          * 响应:MCPServerDTO
        - `PUT /api/v1/mcp/servers/{server_id}` - 更新服务器配置
          * 请求:MCPServerUpdateRequest
          * 响应:MCPServerDTO
        - `DELETE /api/v1/mcp/servers/{server_id}` - 注销服务器
        - `GET /api/v1/mcp/servers/{server_id}/health` - 检查服务器健康
          * 响应:HealthStatusDTO
        - `GET /api/v1/mcp/servers/{server_id}/url` - 获取服务器 URL
          * 响应:{url: str}

- [ ] 5.2 创建 MCP 工具管理 API 路由
     【目标对象】`app/api/v1/mcp/tools/`
     【修改目的】暴露 MCP 工具管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MCPToolAppService
     【修改内容】
        - `GET /api/v1/mcp/tools` - 获取工具列表
          * 参数:server_id, is_global
          * 响应:List[MCPToolDTO]
        - `GET /api/v1/mcp/tools/search` - 搜索工具
          * 参数:keyword
          * 响应:List[MCPToolDTO]
        - `GET /api/v1/mcp/tools/{tool_id}` - 获取工具详情
          * 响应:MCPToolDTO
        - `GET /api/v1/mcp/tools/{tool_name}/classify` - 判断工具类型
          * 响应:ToolTypeDTO
        - `GET /api/v1/mcp/tools/{tool_name}/url` - 获取工具调用 URL
          * 参数:user_id
          * 响应:{url: str}

- [ ] 5.3 创建 MCP 连接管理 API 路由
     【目标对象】`app/api/v1/mcp/connections/`
     【修改目的】暴露 MCP 连接管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MCPConnectionAppService
     【修改内容】
        - `POST /api/v1/mcp/connections` - 创建 MCP 连接
          * 请求:{user_id, server_id}
          * 响应:MCPConnectionDTO
        - `GET /api/v1/mcp/connections` - 获取用户连接列表
          * 参数:user_id
          * 响应:List[MCPConnectionDTO]
        - `GET /api/v1/mcp/connections/{connection_id}` - 获取连接详情
          * 响应:MCPConnectionDTO
        - `POST /api/v1/mcp/connections/{connection_id}/rebuild` - 重建连接
          * 响应:MCPConnectionDTO
        - `DELETE /api/v1/mcp/connections/{connection_id}` - 关闭连接

- [ ] 5.4 创建工具参数预设 API 路由
     【目标对象】`app/api/v1/mcp/tools/{tool_id}/presets/`
     【修改目的】暴露工具参数预设管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ParameterPresetAppService
     【修改内容】
        - `POST /api/v1/mcp/tools/{tool_id}/presets` - 创建参数预设
          * 请求:ParameterPresetCreateRequest
          * 响应:ToolParameterPresetDTO
        - `GET /api/v1/mcp/tools/{tool_id}/presets` - 获取参数预设列表
          * 响应:List[ToolParameterPresetDTO]
        - `GET /api/v1/mcp/tools/{tool_id}/presets/{preset_id}` - 获取预设详情
          * 响应:ToolParameterPresetDTO
        - `POST /api/v1/mcp/tools/{tool_id}/presets/{preset_id}/apply` - 应用预设
          * 请求:{override_params}
          * 响应:ValidatedParametersDTO
        - `DELETE /api/v1/mcp/tools/{tool_id}/presets/{preset_id}` - 删除预设

- [ ] 5.5 创建 MCP 工具调用 API 路由
     【目标对象】`app/api/v1/mcp/call/`
     【修改目的】暴露 MCP 工具调用的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MCPToolCallAppService
     【修改内容】
        - `POST /api/v1/mcp/call` - 调用 MCP 工具
          * 请求:{tool_name, arguments, user_id}
          * 响应:ToolCallResultDTO
        - `POST /api/v1/mcp/call/batch` - 批量调用工具
          * 请求:List[ToolCallRequest]
          * 响应:List[ToolCallResultDTO]
        - `POST /api/v1/mcp/call/{call_id}/cancel` - 取消工具调用

- [ ] 5.6 创建 SSE 流式 API 路由
     【目标对象】`app/api/v1/mcp/stream/`
     【修改目的】提供 MCP 工具的 SSE 实时事件流
     【修改方式】使用 FastAPI StreamingResponse
     【相关依赖】SSEConnectionManager
     【修改内容】
        - `GET /api/v1/mcp/stream/{connection_id}` - SSE 事件流
          * 建立 SSE 连接
          * 监听并推送 MCP 事件
          * 处理连接断开
          * 心跳维护

### 6. 基础设施层

- [ ] 6.1 实现 MCP 配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置 MCP 运行参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - mcp.enabled - 是否启用 MCP 支持
        - mcp.protocol.supported_versions - 支持的协议版本列表
        - mcp.server.health_check_interval - 健康检查间隔 (秒)
        - mcp.server.health_check_timeout - 健康检查超时 (秒)
        - mcp.connection.max_idle_time - 最大空闲时间 (秒)
        - mcp.connection.reconnect.max_retries - 最大重连次数
        - mcp.connection.reconnect.backoff - 重连退避时间 (毫秒)
        - mcp.container.auto_cleanup - 是否自动清理容器
        - mcp.container.cleanup_interval - 容器清理间隔 (秒)
        - mcp.sse.heartbeat_interval - SSE 心跳间隔 (毫秒)
        - mcp.sse.timeout - SSE 超时时间 (秒)

- [ ] 6.2 实现健康检查服务
     【目标对象】`app/infrastructure/health_check/`
     【修改目的】定期检查 MCP 服务器健康状态
     【修改方式】使用 httpx 进行 HTTP 健康检查
     【相关依赖】httpx, APScheduler
     【修改内容】
        - 创建 MCPHealthChecker 类
          * _server_repository: MCPServerRepository
        - 实现方法:
          * check_health(server_url, timeout) -> HealthStatus
            - 发送 HTTP GET 请求
            - 检查响应状态码
            - 记录响应时间
          * schedule_health_checks()
            - 定时检查所有服务器
            - 更新服务器状态
          * on_health_check_failed(server_id, error)
            - 记录错误日志
            - 触发告警

- [ ] 6.3 实现定时任务清理
     【目标对象】`app/infrastructure/scheduler/`
     【修改目的】定期清理不活跃的 MCP 连接和容器
     【修改方式】使用 APScheduler
     【相关依赖】APScheduler, MCPConnectionRepository, ContainerIntegrationService
     【修改内容】
        - 创建定时任务
          * 每 10 分钟执行一次
          * 清理超时的 MCP 连接
          * 清理临时容器
        - 配置任务参数:
          * misfire_grace_time
          * coalesce

### 7. 事件监听器

- [ ] 7.1 实现 MCP 连接事件监听器
     【目标对象】`app/application/mcp/listener.py`
     【修改目的】监听 MCP 连接事件
     【修改方式】实现事件监听器
     【相关依赖】SSEConnectionManager
     【修改内容】
        - on_sse_connect(connection_id, user_id, server_id)
          * 记录连接日志
          * 更新连接状态
        - on_sse_disconnect(connection_id, reason)
          * 清理连接资源
          * 记录断开原因
          * 触发自动重连 (如果需要)

- [ ] 7.2 实现容器生命周期事件监听器
     【目标对象】`app/application/mcp/listener.py`
     【修改目的】监听容器生命周期事件
     【修改方式】实现事件监听器
     【相关依赖】ContainerIntegrationService
     【修改内容】
        - on_container_created(container_id, tool_id, user_id)
          * 记录容器创建日志
          * 更新容器状态
        - on_container_failed(container_id, error)
          * 记录错误信息
          * 尝试自动重启
          * 触发告警
        - on_container_released(container_id)
          * 清理关联的连接
          * 记录日志

- [ ] 7.3 实现工具调用事件监听器
     【目标对象】`app/application/mcp/listener.py`
     【修改目的】监听工具调用事件
     【修改方式】实现事件监听器
     【相关依赖】MCPToolCallAppService
     【修改内容】
        - on_tool_call_started(call_id, tool_name)
          * 记录调用开始日志
          * 更新调用状态
        - on_tool_call_completed(call_id, result)
          * 记录调用结果
          * 统计调用时长
        - on_tool_call_failed(call_id, error)
          * 记录错误信息
          * 判断是否重试

### 8. 测试

- [ ] 8.1 编写单元测试
     【目标对象】`tests/test_mcp_service.py`
     【修改目的】确保 MCP 功能正确性
     【修改方式】使用 pytest
     【相关依赖】MCPServerAppService, MCPToolCallAppService
     【修改内容】
        - 测试服务器注册和注销
        - 测试工具发现和分类
        - 测试容器集成
        - 测试参数预设
        - 测试 SSE 连接管理
        - 测试 URL 构建
        - 测试工具调用流程
        - 测试错误处理

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_mcp_api.py`
     【修改目的】确保 MCP API 端到端正常工作
     【修改方式】使用 FastAPI TestClient 和真实的 MCP 服务器
     【相关依赖】FastAPI, MCPServerAppService
     【修改内容】
        - 测试服务器管理 API
        - 测试工具列表 API
        - 测试工具调用 API
        - 测试 SSE 连接
        - 测试容器集成
        - 测试参数预设 API

- [ ] 8.3 编写性能测试
     【目标对象】`tests/performance/test_mcp_performance.py`
     【修改目的】测试 MCP 性能
     【修改方式】使用 pytest-benchmark
     【相关依赖】MCPToolCallAppService
     【修改内容】
        - 测试高并发工具调用
        - 测试 SSE 连接吞吐量
        - 测试容器启动时间
        - 测试 URL 获取延迟
        - 测试内存使用情况

### 9. 监控和日志

- [ ] 9.1 实现 MCP 监控指标
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控 MCP 运行状态
     【修改方式】使用 Prometheus 指标
     【相关依赖】prometheus_client
     【修改内容】
        - 定义服务器健康指标 Gauge
          * mcp_server_health - 服务器健康状态
          * mcp_server_response_time_seconds - 响应时间
        - 定义工具调用指标 Counter/Histogram
          * tool_calls_total - 工具调用总次数
          * tool_call_duration_seconds - 调用时长
          * tool_call_failures_total - 失败次数
        - 定义连接指标 Gauge
          * mcp_active_connections - 活跃连接数
          * mcp_sse_connection_duration_seconds - 连接持续时间
        - 定义容器指标
          * mcp_containers_created_total - 容器创建总数
          * mcp_containers_active - 活跃容器数

- [ ] 9.2 实现 MCP 日志记录
     【目标对象】`app/infrastructure/logging/`
     【修改目的】记录 MCP 运行日志
     【修改方式】使用结构化日志
     【相关依赖】loguru
     【修改内容】
        - 服务器注册/注销日志
        - 工具发现和调用日志
        - SSE 连接/断开日志
        - 容器生命周期日志
        - 错误日志
        - 性能日志

### 10. 错误处理

- [ ] 10.1 定义 MCP 异常
     【目标对象】`app/core/exceptions/`
     【修改目的】定义 MCP 相关异常
     【修改方式】自定义异常类
     【相关依赖】无
     【修改内容】
        - MCPServerNotFoundException (404)
          * 服务器不存在时抛出
        - MCPToolNotFoundException (404)
          * 工具不存在时抛出
        - MCPConnectionException (500)
          * 连接失败时抛出
        - MCPProtocolException (400)
          * 协议错误时抛出
        - MCPTimeoutException (408)
          * 超时时抛出
        - ContainerCreationFailedException (500)
          * 容器创建失败时抛出
        - InvalidParameterException (400)
          * 参数无效时抛出

- [ ] 10.2 实现错误处理中间件
     【目标对象】`app/api/middleware/`
     【修改目的】统一处理 MCP 错误
     【修改方式】实现 FastAPI 中间件
     【相关依赖】FastAPI
     【修改内容】
        - 捕获 MCPServerNotFoundException
          * 返回 404 错误响应
        - 捕获 MCPToolNotFoundException
          * 返回 404 错误响应和建议
        - 捕获 MCPConnectionException
          * 尝试重连或返回 500
        - 捕获 MCPTimeoutException
          * 返回 408 错误响应
        - 记录所有 MCP 错误日志

### 11. 性能优化

- [ ] 11.1 实现连接池
     【目标对象】`app/infrastructure/connection_pool/`
     【修改目的】复用 MCP 连接，提升性能
     【修改方式】使用连接池模式
     【相关依赖】asyncio
     【修改内容】
        - 创建 MCPConnectionPool 类
          * _connections: Dict[server_id, Pool]
          * _max_connections_per_server: int
        - 实现方法:
          * acquire(server_id) -> SSEConnection
          * release(connection)
          * close_all()
        - 配置参数:
          * max_size
          * min_idle
          * max_lifetime

- [ ] 11.2 实现缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升 MCP 查询性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 缓存工具定义
        - 缓存服务器 URL
        - 缓存参数预设
        - 实现缓存预热
        - 实现缓存过期和淘汰

- [ ] 11.3 实现负载均衡
     【目标对象】`app/infrastructure/load_balancer/`
     【修改目的】在多个 MCP 服务器间负载均衡
     【修改方式】使用轮询或加权轮询
     【相关依赖】MCPServerManager
     【修改内容】
        - 创建 MCPLoadBalancer 类
          * 轮询策略
          * 加权轮询策略 (基于健康度)
          * 最少连接策略
        - 实现方法:
          * select_server(tool_name) -> MCPServer
          * update_server_weight(server_id, weight)