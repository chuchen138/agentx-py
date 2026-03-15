# 容器管理技术设计

## 概述

容器管理模块基于 Docker Container API 和领域驱动设计（DDD）架构实现，采用分层设计模式，将 Docker 基础设施操作、领域业务逻辑和应用层用例清晰分离。模块使用 Python 语言和 FastAPI 框架，通过 docker-py 库与 Docker Engine 交互。

## 技术架构

### 架构分层

系统采用四层架构：

**表示层（Presentation Layer）**
- RESTful API：使用 FastAPI 提供外部访问接口
- 管理界面：Web 控制台供管理员使用
- 认证中间件：处理 JWT 认证和权限验证

**应用层（Application Layer）**
- 容器管理服务：协调容器创建、启动、停止、删除等用例
- 监控服务：定时检查容器状态和资源使用情况
- 清理服务：执行容器自动清理策略
- 模板服务：管理容器配置模板

**领域层（Domain Layer）**
- 容器实体：定义容器业务对象和状态机
- 仓储接口：定义数据访问抽象
- 领域服务：封装核心业务逻辑（端口分配、健康检查、智能恢复）
- 类型策略：支持不同容器类型的扩展

**基础设施层（Infrastructure Layer）**
- Docker 客户端：封装 docker-py SDK 操作
- 数据库持久化：使用 SQLAlchemy + SQLite/PostgreSQL
- 端口管理器：管理端口分配和冲突检测
- 日志记录：结构化日志记录

### 设计原则

- **领域驱动设计（DDD）**：以业务领域为核心，分离业务逻辑和技术实现
- **依赖倒置**：高层模块不依赖低层模块，都依赖抽象接口
- **分层清晰**：各层职责明确，单向依赖
- **单一职责**：每个类和服务只负责一项职责
- **开闭原则**：对扩展开放，对修改关闭

## 容器类型策略

### 容器类型定义

系统定义两种容器类型：

**USER 容器（用户容器）**
- 用途：支撑用户的 Agent 对话和工具部署
- 数量：每个用户一个
- 生命周期：与用户账号绑定，长期保留
- 访问权限：仅用户本人和管理员可访问

**REVIEW 容器（审核容器）**
- 用途：支持工具审核流程
- 数量：全系统一个
- 生命周期：按需创建，长期保持就绪
- 访问权限：仅管理员可访问

### 用户容器策略

**命名规则**：`mcp-gateway-user-{userId 的前 8 位}`

**资源配置**：
- 端口范围：30000-40000
- 数据卷路径：`/data/users/{userId}`
- CPU 限制：1.0 核（可配置）
- 内存限制：512 MB（可配置）

**隔离机制**：
- 独立的数据卷挂载
- 独立的端口映射
- 独立的网络命名空间

### 审核容器策略

**命名规则**：`mcp-gateway-review`

**资源配置**：
- 端口范围：30000-40000
- 数据卷路径：`/data/review`
- CPU 限制：1.0 核（可配置）
- 内存限制：512 MB（可配置）

**共享机制**：
- 全局共享单个容器
- 审核环境隔离于用户环境
- 审核完成后不清理，保持就绪状态

## 容器状态管理

### 容器状态枚举

定义以下容器生命周期状态：

- **CREATING（创建中）**：容器正在创建过程中
- **RUNNING（运行中）**：容器正常运行状态
- **STOPPED（已停止）**：容器被用户或系统停止
- **ERROR（错误状态）**：容器发生异常或错误
- **DELETING（删除中）**：容器正在删除过程中
- **DELETED（已删除）**：容器已被删除
- **SUSPENDED（已暂停）**：容器因空闲被暂停

### 状态流转规则

**状态机定义**：

**初始状态 → CREATING**
- 创建成功 → RUNNING
- 创建失败 → ERROR → DELETED

**RUNNING 状态的转换**：
- 用户主动停止 → STOPPED
- 系统检测到空闲（24 小时未访问）→ SUSPENDED
- 检测到异常（Docker 容器崩溃）→ ERROR
- 用户主动删除 → DELETING → DELETED

**STOPPED 状态的转换**：
- 用户手动启动 → RUNNING
- 用户删除 → DELETING → DELETED

**SUSPENDED 状态的转换**：
- 用户访问唤醒 → RUNNING
- 用户删除 → DELETING → DELETED

**ERROR 状态的转换**：
- 智能恢复成功 → RUNNING
- 无法恢复 → DELETING → DELETED

**DELETING 状态**：
- 删除完成 → DELETED

## 监控与恢复

### 监控指标体系

**监控维度**：

1. **容器状态监控**
   - 生命周期状态（CREATING/RUNNING/STOPPED 等）
   - Docker 实际运行状态
   - 最后更新时间

2. **资源使用监控**
   - CPU 使用率（百分比）
   - 内存使用率（百分比）
   - 磁盘使用量（MB/GB）

3. **网络状态监控**
   - IP 地址
   - 外部端口
   - 网络连通性

4. **访问记录监控**
   - 最后访问时间
   - 访问频率统计

**数据采集频率**：
- 实时采集：容器状态变化
- 每 2 分钟：CPU/内存使用率
- 每 5 分钟：全面状态检查

### 定时任务设计

**容器状态检查任务**
- 执行频率：每 5 分钟执行一次
- 职责：
  - 检查 Docker 容器是否真实存在
  - 检查容器实际运行状态
  - 同步数据库状态与实际状态
  - 检测异常容器并触发恢复

**资源监控任务**
- 执行频率：每 2 分钟执行一次
- 职责：
  - 采集 CPU/内存使用率
  - 更新数据库统计信息
  - 记录资源使用趋势

**容器清理任务**
- 执行频率：每小时执行一次
- 职责：
  - 暂停 24 小时未访问的运行中容器
  - 删除 5 天未访问的暂停/停止容器
  - 清理已标记为 DELETED 的 Docker 容器

### 智能恢复机制

**恢复策略选择**：

**策略 1：Docker 容器重启**
- 适用场景：Docker 容器存在但未运行（stopped/exited 状态）
- 处理方式：强制启动已存在的 Docker 容器
- 后续操作：更新数据库状态为 RUNNING

**策略 2：容器信息修正**
- 适用场景：Docker 容器运行正常，但数据库状态不同步
- 处理方式：重新获取容器网络信息（IP、端口）
- 后续操作：更新数据库中的容器信息并同步状态

**策略 3：完全重建容器**
- 适用场景：Docker 容器已不存在或无法恢复
- 处理方式：
  - 标记旧容器为 DELETED 状态
  - 基于模板创建新容器
  - 重新分配端口和数据卷
- 后续操作：启动新容器并更新状态

**恢复流程**：
1. 检查 Docker 容器是否存在
   - 若存在但未运行 → 策略 1（重启）
2. 检查容器运行状态是否正常
   - 若运行但信息不同步 → 策略 2（修正）
3. 检查容器是否已不存在
   - 若不存在 → 策略 3（重建）
4. 记录恢复日志和指标

**优化策略**：
- 快速失败检测：设置超时时间（默认 60 秒）
- 增量恢复：按重启 > 修正 > 重建的优先级尝试
- 恢复重试：失败时最多重试 3 次
- 缓存利用：优先使用缓存的容器信息

## 端口与网络设计

### 端口分配算法

**端口范围**：30000-40000（共 10000 个端口）

**分配流程**：
1. 在指定范围内随机生成端口号
2. 检查数据库中是否已被占用
3. 检查宿主机端口是否已被占用
4. 若冲突，重新生成直到找到可用端口
5. 返回分配的端口号

**冲突避免**：
- 数据库层面：唯一索引约束
- 系统层面：启动前检测端口占用
- 恢复层面：端口冲突时重新分配

### Docker 网络配置

**网络模式**：bridge（桥接模式）

**配置参数**：
- 网络驱动：bridge
- 端口映射：内部端口 8080 → 外部随机端口
- DNS 解析：启用 Docker 内置 DNS
- 网络隔离：每个容器独立网络命名空间

**网络连通性检测**：
- Socket 连接测试：尝试连接容器 IP:端口
- HTTP 健康检查：发送 GET 请求到健康检查端点
- 超时控制：连接超时 3 秒

## 容器模板设计

### 模板配置规范

容器模板包含以下配置项：

**基础配置**：
- 镜像名称：Docker 镜像仓库地址
- 内部端口：容器内部服务端口
- CPU 限制：容器可用的 CPU 核心数
- 内存限制：容器可用的最大内存

**高级配置**：
- 环境变量：JSON 格式的环境变量配置
- 数据卷挂载：宿主机路径到容器路径的映射
- 启动命令：自定义容器启动命令
- 网络模式：bridge/host/none
- 重启策略：always/on-failure/unless-stopped/no

### 默认模板（MCP 网关）

**模板名称**：mcp-gateway-default

**配置说明**：
- 镜像：ghcr.io/lucky-aeon/mcp-gateway:latest
- 内部端口：8080
- CPU 限制：1.0 核
- 内存限制：512 MB
- 环境变量：{}
- 数据卷：/data/users/{userId}:/data/user
- 网络模式：bridge
- 重启策略：unless-stopped

## 数据模型设计

### 容器实体（Container）

**表名**：user_containers

**字段定义**：
- id：主键（UUID）
- user_id：用户 ID（外键）
- name：容器名称
- type：容器类型（USER/REVIEW）
- status：容器状态（枚举）
- docker_container_id：Docker 容器 ID
- image：使用的镜像名称
- internal_port：内部端口号
- external_port：外部端口号
- ip_address：容器 IP 地址
- cpu_usage：CPU 使用率（百分比）
- memory_usage：内存使用率（百分比）
- volume_path：数据卷路径
- env_config：环境配置（JSON）
- container_config：容器配置（JSON）
- error_message：错误信息
- last_accessed_at：最后访问时间
- created_at：创建时间
- updated_at：更新时间

**索引设计**：
- PRIMARY KEY (id)
- UNIQUE KEY (user_id, type) - 每个用户每种类型只有一个容器
- INDEX (status) - 按状态查询
- INDEX (type) - 按类型查询
- INDEX (user_id) - 按用户查询

### 容器模板实体（ContainerTemplate）

**表名**：container_templates

**字段定义**：
- id：主键（UUID）
- name：模板名称
- description：模板描述
- image：镜像名称
- internal_port：内部端口
- cpu_limit：CPU 限制
- memory_limit：内存限制
- env_config：环境配置（JSON）
- volume_config：数据卷配置（JSON）
- command：启动命令
- network_mode：网络模式
- restart_policy：重启策略
- is_default：是否为默认模板
- is_active：是否启用
- created_at：创建时间
- updated_at：更新时间

## 应用服务设计

### ContainerAppService（容器应用服务）

**职责**：编排容器管理的用例

**主要方法**：
- create_container(user_id, template_id, config) - 创建容器
- start_container(container_id) - 启动容器
- stop_container(container_id) - 停止容器
- delete_container(container_id) - 删除容器
- get_container(container_id) - 获取容器详情
- list_containers(filters, pagination) - 获取容器列表
- get_container_logs(container_id, follow) - 获取容器日志
- get_container_statistics() - 获取统计信息

### ContainerMonitorService（容器监控服务）

**职责**：实现容器监控功能

**主要方法**：
- check_container_status() - 定时检查容器状态
- collect_resource_metrics() - 采集资源使用数据
- health_check(container_id) - 执行健康检查
- handle_abnormal_container(container_id) - 处理异常容器

### ContainerCleanupService（容器清理服务）

**职责**：清理过期或异常容器

**主要方法**：
- cleanup_idle_containers() - 清理空闲容器
- cleanup_deleted_containers() - 清理已删除容器
- cleanup_error_containers() - 清理错误容器
- cleanup_data_volumes() - 清理数据卷

### ReviewContainerService（审核容器服务）

**职责**：管理审核容器的生命周期

**主要方法**：
- get_or_create_review_container() - 获取或创建审核容器
- start_review_container() - 启动审核容器
- stop_review_container() - 停止审核容器
- cleanup_review_environment() - 清理审核环境

## 异常处理设计

### 异常类型定义

**容器操作异常**：
- ContainerNotFoundException：容器不存在异常
- ContainerAlreadyExistsException：容器已存在异常
- ContainerStateException：容器状态异常（如在 STOPPED 状态下启动）
- ContainerOperationException：容器操作失败异常

**Docker 相关异常**：
- DockerConnectionException：Docker 守护进程连接失败
- DockerAPIException：Docker API 调用失败
- ContainerStartFailedException：容器启动失败
- ContainerCreateFailedException：容器创建失败

**资源管理异常**：
- PortAllocationFailedException：端口分配失败
- ResourceQuotaExceededException：资源配额超出限制
- VolumeMountFailedException：数据卷挂载失败

### 全局异常处理

**异常处理器**：
- 捕获所有未处理的异常
- 记录详细的错误日志
- 返回统一的错误响应格式
- 根据异常类型返回合适的 HTTP 状态码

**错误响应格式**：
```json
{
  "error": {
    "code": "CONTAINER_NOT_FOUND",
    "message": "容器不存在或已被删除",
    "details": {
      "container_id": "xxx"
    }
  }
}
```

## 性能优化设计

### Docker 客户端优化

**连接池管理**：
- 使用单例 Docker 客户端实例
- 复用 Docker Socket 连接
- 避免频繁创建和销毁客户端

**批量操作**：
- 批量获取容器列表时使用分页
- 批量查询容器状态时并行执行
- 批量删除容器时异步处理

### 缓存策略

**容器信息缓存**：
- 缓存容器详细信息（TTL: 5 分钟）
- 缓存容器统计数据（TTL: 2 分钟）
- 缓存失效时主动更新

**端口分配缓存**：
- 缓存已分配端口集合
- 减少数据库查询次数

### 异步处理

**异步任务**：
- 容器创建：异步执行，返回任务 ID
- 容器删除：异步执行，避免阻塞
- 镜像拉取：异步执行，支持进度查询

**实现方式**：
- 使用 Celery 作为任务队列
- Redis 作为消息代理
- 支持任务状态查询

## 监控与日志设计

### 日志规范

**日志级别**：
- ERROR：系统错误、操作失败（如 Docker 连接失败、容器创建失败）
- WARN：潜在问题、恢复信息（如容器异常 detected、自动恢复尝试）
- INFO：重要业务操作（如容器创建成功、状态变更）
- DEBUG：调试信息（如 API 请求参数、数据库查询）

**日志格式**：
```
{timestamp} | {level} | {module} | {message} | {context}
```

**示例**：
```
2026-03-14 10:30:15 | INFO | container_service | Container created successfully | {"container_id": "xxx", "user_id": "yyy"}
```

### 关键监控指标

**业务指标**：
- 容器创建成功率：目标 > 98%
- 容器恢复成功率：目标 > 95%
- 平均恢复时间：目标 < 60 秒

**运行指标**：
- 运行中容器数量
- 暂停中容器数量
- 错误状态容器数量
- 平均 CPU/内存使用率

**性能指标**：
- API 响应时间（P95 < 500ms）
- Docker API 调用成功率
- 端口分配耗时（P95 < 1 秒）

### 告警规则

**严重告警**（立即通知）：
- Docker 守护进程不可用
- 容器创建连续失败 10 次
- 系统资源不足（内存 < 10%）

**警告告警**（工作时间内处理）：
- 单容器 CPU 使用率持续 > 90%
- 错误状态容器数量 > 5
- 可用端口数量 < 100

## 安全设计

### 权限控制

**认证机制**：
- 所有 API 端点需要 JWT 认证
- Token 中包含用户 ID 和角色信息
- Token 有效期 24 小时，支持刷新

**授权策略**：
- 用户只能操作自己的容器（USER 类型）
- 管理员可以操作所有容器
- 审核容器仅管理员可访问

### 资源防滥用

**数量限制**：
- 单用户最多 1 个 USER 容器
- 全系统最多 1 个 REVIEW 容器

**资源限制**：
- 单容器 CPU 不超过 2 核
- 单容器内存不超过 2GB
- 总容器数量不超过 1000 个

### 审计日志

**记录内容**：
- 操作人（用户 ID）
- 操作类型（创建/启动/停止/删除）
- 操作对象（容器 ID）
- 操作时间
- 操作结果（成功/失败）

**保留策略**：
- 审计日志保留至少 90 天
- 支持按用户、时间、操作类型查询

## 扩展性设计

### 容器类型扩展

**类型接口**：
- 定义容器类型基类
- 实现自定义容器类型的名称生成规则
- 实现自定义容器类型的模板获取逻辑
- 实现自定义容器类型的验证逻辑

**注册机制**：
- 通过配置文件注册新的容器类型
- 支持运行时动态加载类型插件

### 资源采集器扩展

**采集器接口**：
- 定义资源采集器基类
- 实现不同类型资源的采集逻辑（CPU、内存、GPU、磁盘等）
- 返回标准化的资源使用数据

**注册机制**：
- 通过依赖注入注册采集器
- 支持按资源类型路由到对应采集器

### 存储驱动扩展

**支持的存储驱动**：
- overlay2（默认）
- aufs
- zfs
- btrfs

**配置方式**：
- 通过 Docker 配置文件指定存储驱动
- 应用层适配不同驱动的特性差异

### 网络插件扩展

**支持的网络模式**：
- bridge（默认）
- macvlan
- ipvlan
- none
- host

**扩展能力**：
- 支持自定义网络插件
- 支持多网络接口配置

## 技术栈选型

### 核心技术栈

**编程语言**：
- Python 3.10+

**Web 框架**：
- FastAPI 0.100+
- Uvicorn（ASGI 服务器）
- Pydantic（数据验证）

**Docker 交互**：
- docker-py 6.0+（Docker SDK for Python）

**数据持久化**：
- SQLAlchemy 2.0+（ORM 框架）
- Alembic（数据库迁移）
- SQLite/PostgreSQL（数据库）

**异步任务**：
- Celery 5.3+（任务队列）
- Redis（消息代理）

### 辅助工具

**认证授权**：
- PyJWT（JWT 实现）
- python-jose（JWS/JWE）

**日志管理**：
- structlog（结构化日志）
- logging（Python 标准日志）

**指标监控**：
- Prometheus Client（指标采集）
- Grafana（可视化看板）

**测试工具**：
- pytest（单元测试框架）
- pytest-asyncio（异步测试支持）
- TestClient（FastAPI 测试工具）
- unittest.mock（Mock 对象）

### 开发环境

**代码质量**：
- Black（代码格式化）
- Flake8（代码检查）
- MyPy（类型检查）

**开发工具**：
- VS Code / PyCharm
- Docker Desktop
- Postman（API 测试）
