## 实施
- [ ] 1.1 定义容器状态和类型枚举
     【目标对象】`app/domain/container/constants.py`
     【修改目的】定义容器状态和类型的常量
     【修改方式】使用 Python Enum 定义枚举类型
     【相关依赖】无
     【修改内容】
        - 创建 ContainerStatus 枚举（CREATING, RUNNING, STOPPED, ERROR, DELETING, DELETED, SUSPENDED）
        - 创建 ContainerType 枚举（USER, REVIEW）

- [ ] 1.2 定义容器实体和数据模型
     【目标对象】`app/domain/container/models.py`
     【修改目的】定义容器和容器模板的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 Container 模型（user_containers 表）
        - 创建 ContainerTemplate 模型（container_templates 表）
        - 定义字段和关系
        - 实现 Pydantic Schema（ContainerCreate, ContainerResponse, ContainerTemplateSchema）

- [ ] 1.3 实现容器仓储模式
     【目标对象】`app/domain/container/repository.py`
     【修改目的】定义容器数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ContainerRepository 接口
        - 定义 ContainerTemplateRepository 接口
        - 实现 SQLAlchemy ContainerRepository
        - 实现 SQLAlchemy ContainerTemplateRepository
        - 实现 CRUD 操作
        - 实现复杂查询（按用户ID、状态、类型查询）

- [ ] 1.4 实现容器领域服务
     【目标对象】`app/domain/container/service.py`
     【修改目的】封装容器相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ContainerRepository, ContainerTemplateRepository
     【修改内容】
        - 创建容器时分配端口
        - 容器状态转换逻辑
        - 容器健康检查逻辑
        - 端口分配和冲突检测
        - 资源限制配置

- [ ] 1.5 实现容器模板领域服务
     【目标对象】`app/domain/container/template_service.py`
     【修改目的】封装容器模板相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ContainerTemplateRepository
     【修改内容】
        - 创建、更新、删除容器模板
        - 获取默认模板
        - 模板配置验证

- [ ] 1.6 实现 Docker 客户端服务
     【目标对象】`app/infrastructure/docker/client.py`
     【修改目的】封装 Docker SDK 操作
     【修改方式】使用 Docker Python SDK
     【相关依赖】docker
     【修改内容】
        - Docker 客户端初始化
        - 容器创建方法
        - 容器启动、停止、删除方法
        - 容器日志获取方法
        - 容器状态查询方法
        - 容器统计信息获取方法
        - 镜像拉取方法

- [ ] 1.7 实现端口管理服务
     【目标对象】`app/infrastructure/docker/port_manager.py`
     【修改目的】管理容器端口分配
     【修改方式】实现端口分配算法
     【相关依赖】Docker 客户端服务
     【修改内容】
        - 端口范围配置（30000-40000）
        - 随机端口分配
        - 端口占用检测
        - 端口冲突避免

- [ ] 1.8 实现应用服务层 - ContainerAppService
     【目标对象】`app/application/container/container_service.py`
     【修改目的】编排容器相关的用例
     【修改方式】实现应用服务
     【相关依赖】ContainerDomainService, DockerClientService
     【修改内容】
        - 创建容器（基于模板或自定义配置）
        - 启动容器
        - 停止容器
        - 删除容器
        - 获取容器列表（支持分页和筛选）
        - 获取容器详情
        - 获取容器日志
        - 获取容器统计信息

- [ ] 1.9 实现应用服务层 - ContainerMonitorService
     【目标对象】`app/application/container/monitor_service.py`
     【修改目的】实现容器监控功能
     【修改方式】实现应用服务
     【相关依赖】ContainerRepository, DockerClientService
     【修改内容】
        - 定时容器状态检查（每5分钟）
        - 定时资源监控（CPU、内存，每2分钟）
        - 容器健康检查
        - 异常容器处理
        - 监控数据更新

- [ ] 1.10 实现应用服务层 - ContainerTemplateAppService
     【目标对象】`app/application/container/template_service.py`
     【修改目的】编排容器模板相关的用例
     【修改方式】实现应用服务
     【相关依赖】ContainerTemplateDomainService
     【修改内容】
        - 创建容器模板
        - 更新容器模板
        - 删除容器模板
        - 获取容器模板列表
        - 获取默认模板
        - 启用/禁用模板

- [ ] 1.11 实现应用服务层 - ContainerCleanupService
     【目标对象】`app/application/container/cleanup_service.py`
     【修改目的】清理过期或异常容器
     【修改方式】实现应用服务
     【相关依赖】ContainerRepository, DockerClientService
     【修改内容】
        - 清理已删除但未清理的容器
        - 清理错误状态的容器
        - 清理长期未使用的容器
        - 数据卷清理

- [ ] 1.12 实现应用服务层 - ReviewContainerService
     【目标对象】`app/application/container/review_service.py`
     【修改目的】管理审核容器的生命周期
     【修改方式】实现应用服务
     【相关依赖】ContainerDomainService, DockerClientService
     【修改内容】
        - 创建审核容器
        - 启动审核容器
        - 停止审核容器
        - 删除审核容器
        - 审核容器自动清理


- [ ] 1.13 实现 Celery 异步任务
     【目标对象】`app/infrastructure/tasks/container_tasks.py`
     【修改目的】异步执行容器操作
     【修改方式】使用 Celery
     【相关依赖】Celery, ContainerAppService, ContainerMonitorService
     【修改内容】
        - 创建容器异步任务
        - 删除容器异步任务
        - 容器监控定时任务
        - 容器清理定时任务
        - 镜像拉取异步任务

- [ ] 1.14 创建 API 路由 - 容器管理（管理员）
     【目标对象】`app/api/v1/admin/containers.py`
     【修改目的】暴露容器管理的管理员 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ContainerAppService, ContainerMonitorService
     【修改内容】
        - `GET /api/v1/admin/containers` - 分页获取容器列表
        - `GET /api/v1/admin/containers/{id}` - 获取容器详情
        - `GET /api/v1/admin/containers/statistics` - 获取容器统计信息
        - `POST /api/v1/admin/containers/review` - 创建审核容器
        - `POST /api/v1/admin/containers/{id}/start` - 启动容器
        - `POST /api/v1/admin/containers/{id}/stop` - 停止容器
        - `DELETE /api/v1/admin/containers/{id}` - 删除容器
        - `GET /api/v1/admin/containers/{id}/logs` - 获取容器日志

- [ ] 1.15 创建 API 路由 - 容器管理（用户）
     【目标对象】`app/api/v1/containers.py`
     【修改目的】暴露容器管理的用户 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ContainerAppService, ContainerMonitorService
     【修改内容】
        - `GET /api/v1/containers/user` - 获取当前用户容器
        - `POST /api/v1/containers/user` - 创建用户容器
        - `GET /api/v1/containers/user/health` - 检查容器健康状态
        - `GET /api/v1/containers/{id}` - 获取容器详情
        - `POST /api/v1/containers/{id}/start` - 启动容器
        - `POST /api/v1/containers/{id}/stop` - 停止容器
        - `DELETE /api/v1/containers/{id}` - 删除容器
        - `GET /api/v1/containers/{id}/logs` - 获取容器日志（支持流式输出）

- [ ] 1.16 创建 API 路由 - 容器模板管理
     【目标对象】`app/api/v1/container_templates.py`
     【修改目的】暴露容器模板管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ContainerTemplateAppService
     【修改内容】
        - `GET /api/v1/container-templates` - 获取容器模板列表
        - `POST /api/v1/container-templates` - 创建容器模板
        - `GET /api/v1/container-templates/{id}` - 获取容器模板详情
        - `PUT /api/v1/container-templates/{id}` - 更新容器模板
        - `DELETE /api/v1/container-templates/{id}` - 删除容器模板
        - `GET /api/v1/container-templates/default` - 获取默认模板

- [ ] 1.17 实现认证和授权中间件
     【目标对象】`app/api/middleware/`
     【修改目的】保护需要认证的 API 端点
     【修改方式】实现 FastAPI 依赖注入和中间件
     【相关依赖】PyJWT, OAuth2PasswordBearer
     【修改内容】
        - 实现 JWT Token 验证中间件
        - 检测用户权限（管理员/普通用户）
        - 将用户信息注入 Request 对象
        - 处理认证失败和权限不足
        - 实现基于角色的访问控制（RBAC）

- [ ] 1.18 创建数据库迁移脚本
     【目标对象】`alembic/versions/`
     【修改目的】创建容器相关表结构
     【修改方式】使用 Alembic 迁移
     【相关依赖】SQLAlchemy, Alembic
     【修改内容】
        - 创建 user_containers 表迁移脚本
        - 创建 container_templates 表迁移脚本
        - 创建必要的索引（user_id, status, type）
        - 添加外键约束（user_id -> users.id）
        - 添加唯一约束（user_id + type 组合唯一）

- [ ] 1.19 编写容器管理单元测试
     【目标对象】`tests/test_container_service.py`
     【修改目的】确保容器管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ContainerAppService, Mock Docker 客户端
     【修改内容】
        - 测试容器创建
        - 测试容器启动、停止、删除
        - 测试容器状态查询
        - 测试端口分配
        - 测试容器日志获取
        - 测试容器健康检查

- [ ] 1.20 编写容器模板管理单元测试
     【目标对象】`tests/test_container_template_service.py`
     【修改目的】确保容器模板管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ContainerTemplateAppService
     【修改内容】
        - 测试容器模板创建、更新、删除
        - 测试默认模板获取
        - 测试模板配置验证

- [ ] 1.21 编写容器监控单元测试
     【目标对象】`tests/test_container_monitor_service.py`
     【修改目的】确保容器监控功能正确性
     【修改方式】使用 pytest
     【相关依赖】ContainerMonitorService, Mock Docker 客户端
     【修改内容】
        - 测试容器状态检查
        - 测试资源监控
        - 测试健康检查
        - 测试异常容器处理

- [ ] 1.22 编写 Docker 客户端单元测试
     【目标对象】`tests/test_docker_client.py`
     【修改目的】确保 Docker 客户端封装正确性
     【修改方式】使用 pytest 和 Mock
     【相关依赖】DockerClientService
     【修改内容】
        - 测试容器创建
        - 测试容器启动、停止、删除
        - 测试日志获取
        - 测试状态查询
        - 测试统计信息获取
        - 测试镜像拉取

- [ ] 1.23 编写容器管理集成测试
     【目标对象】`tests/integration/test_container_api.py`
     【修改目的】确保容器 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient 和 Mock Docker
     【相关依赖】FastAPI, ContainerAppService, Mock Docker 客户端
     【修改内容】
        - 测试创建容器端点
        - 测试启动容器端点
        - 测试停止容器端点
        - 测试删除容器端点
        - 测试获取容器列表端点
        - 测试获取容器日志端点

- [ ] 1.24 编写容器的集成测试（用户端）
     【目标对象】`tests/integration/test_user_container_api.py`
     【修改目的】确保用户容器 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, ContainerAppService
     【修改内容】
        - 测试获取用户容器
        - 测试创建用户容器
        - 测试检查容器健康状态

- [ ] 1.25 编写 Celery 任务测试
     【目标对象】`tests/test_container_tasks.py`
     【修改目的】确保异步任务正常工作
     【修改方式】使用 pytest 和 Mock
     【相关依赖】Celery, 容器任务
     【修改内容】
        - 测试创建容器异步任务
        - 测试删除容器异步任务
        - 测试监控定时任务
        - 测试清理定时任务

- [ ] 1.26 编写安全加固实施
     【目标对象】`app/infrastructure/docker/security.py`
     【修改目的】实现容器安全加固措施
     【修改方式】封装 Docker 安全配置
     【相关依赖】docker-py
     【修改内容】
        - 实现 seccomp 配置文件加载
        - 实现 AppArmor/SELinux 配置文件应用
        - 实现 Linux capabilities 限制（删除 CAP_SYS_ADMIN 等危险权限）
        - 实现敏感目录挂载保护（禁止挂载/etc、/proc、/sys）
        - 实现只读根文件系统配置
        - 实现用户命名空间重映射

- [ ] 1.27 编写资源配额管理实施
     【目标对象】`app/domain/container/quota_manager.py`
     【修改目的】管理和限制容器资源使用
     【修改方式】实现资源配额检查和限制逻辑
     【相关依赖】ContainerRepository, DockerClientService
     【修改内容】
        - 实现系统总资源配额检查（CPU、内存上限）
        - 实现单用户资源配额限制
        - 实现资源使用告警（超过 80% 时告警）
        - 实现资源超限自动降级策略

- [ ] 1.28 编写健康检查增强实施
     【目标对象】`app/application/container/health_checker.py`
     【修改目的】实现多维度的容器健康检查
     【修改方式】封装健康检查逻辑
     【相关依赖】DockerClientService, ContainerRepository
     【修改内容】
        - 实现数据库状态检查
        - 实现 Docker 容器存在性检查
        - 实现网络连通性检查（Socket 连接测试）
        - 实现 HTTP 健康端点检查（GET /health）
        - 实现健康检查超时控制（3 秒）
        - 实现健康检查结果缓存

- [ ] 1.29 编写错误恢复策略实施
     【目标对象】`app/application/container/recovery_strategy.py`
     【修改目的】实现智能的容器错误恢复
     【修改方式】实现多种恢复策略
     【相关依赖】DockerClientService, ContainerRepository
     【修改内容】
        - 实现 Docker 容器重启策略
        - 实现容器信息修正策略
        - 实现完全重建容器策略
        - 实现恢复优先级判断逻辑
        - 实现恢复重试机制（最多 3 次）
        - 实现恢复失败回滚处理

- [ ] 1.30 编写审计日志实施
     【目标对象】`app/infrastructure/logging/audit_logger.py`
     【修改目的】记录所有容器操作的审计日志
     【修改方式】实现结构化审计日志
     【相关依赖】structlog, SQLAlchemy
     【修改内容】
        - 定义审计日志数据模型
        - 实现容器创建/启动/停止/删除操作记录
        - 实现操作人和时间记录
        - 实现操作结果（成功/失败）记录
        - 实现审计日志查询接口
        - 实现审计日志保留策略（90 天）

- [ ] 1.31 编写性能监控实施
     【目标对象】`app/infrastructure/metrics/container_metrics.py`
     【修改目的】采集和导出容器性能指标
     【修改方式】集成 Prometheus 指标采集
     【相关依赖】prometheus_client
     【修改内容】
        - 定义容器数量指标（gauge）
        - 定义容器创建成功率指标（counter）
        - 定义容器恢复耗时指标（histogram）
        - 定义资源使用率指标（gauge）
        - 实现指标采集器注册
        - 实现 Prometheus 端点暴露

- [ ] 1.32 编写集成测试 - Docker 异常场景
     【目标对象】`tests/integration/test_docker_exceptions.py`
     【修改目的】测试 Docker 异常情况下的系统行为
     【修改方式】使用 pytest 和 Mock Docker API
     【相关依赖】pytest, unittest.mock
     【修改内容】
        - 测试 Docker 守护进程不可用时的处理
        - 测试镜像拉取失败时的处理
        - 测试端口冲突时的重新分配
        - 测试容器创建超时时的处理
        - 测试容器意外崩溃时的自动恢复
        - 测试资源不足时的优雅降级

- [ ] 1.33 编写集成测试 - 安全加固验证
     【目标对象】`tests/integration/test_security_hardening.py`
     【修改目的】验证容器安全加固措施有效性
     【修改方式】使用 pytest 和 Docker SDK
     【相关依赖】pytest, docker-py
     【修改内容】
        - 验证 seccomp 配置文件已应用
        - 验证 AppArmor/SELinux 配置文件已应用
        - 验证 capabilities 限制已生效
        - 验证敏感目录未挂载
        - 验证根文件系统为只读
        - 验证用户命名空间重映射已启用

- [ ] 1.34 编写性能测试 - 并发容器创建
     【目标对象】`tests/performance/test_concurrent_creation.py`
     【修改目的】测试系统在高并发下的性能表现
     【修改方式】使用 pytest-benchmark
     【相关依赖】pytest-benchmark, asyncio
     【修改内容】
        - 测试并发创建 50 个容器的耗时
        - 测试并发创建 100 个容器的成功率
        - 测试端口分配冲突率
        - 测试数据库连接池性能
        - 测试 Docker Socket 连接复用效果

- [ ] 1.35 编写压力测试 - 资源极限
     【目标对象】`tests/stress/test_resource_limits.py`
     【修改目的】测试系统在资源极限情况下的行为
     【修改方式】使用 locust 或自定义压力测试脚本
     【相关依赖】locust, psutil
     【修改内容】
        - 测试 CPU 使用率达到上限时的处理
        - 测试内存使用率达到上限时的处理
        - 测试端口耗尽时的处理
        - 测试磁盘空间不足时的处理
        - 测试系统自动降级策略

- [ ] 1.36 编写端到端测试 - 用户场景
     【目标对象】`tests/e2e/test_user_scenarios.py`
     【修改目的】测试真实用户场景的端到端流程
     【修改方式】使用 FastAPI TestClient 和真实 Docker 环境
     【相关依赖】FastAPI, httpx, docker-py
     【修改内容】
        - 测试用户首次使用 Agent 对话（自动创建容器）
        - 测试用户容器异常自动恢复
        - 测试用户容器空闲自动暂停
        - 测试用户容器长期未使用自动删除
        - 测试用户唤醒暂停容器

- [ ] 1.37 编写端到端测试 - 管理员场景
     【目标对象】`tests/e2e/test_admin_scenarios.py`
     【修改目的】测试管理员操作的端到端流程
     【修改方式】使用 FastAPI TestClient 和真实 Docker 环境
     【相关依赖】FastAPI, httpx, docker-py
     【修改内容】
        - 测试管理员创建审核容器
        - 测试管理员查看所有容器列表
        - 测试管理员操作任意容器（启动/停止/删除）
        - 测试管理员查看容器统计信息
        - 测试管理员查看审计日志

- [ ] 1.38 编写配置管理模块
     【目标对象】`app/core/config/container_config.py`
     【修改目的】集中管理容器相关配置
     【修改方式】使用 Pydantic BaseSettings
     【相关依赖】pydantic, python-dotenv
     【修改内容】
        - 定义 Docker 连接配置（socket 路径、TLS 证书）
        - 定义端口范围配置（最小值、最大值）
        - 定义资源限额配置（CPU 上限、内存上限）
        - 定义清理策略配置（暂停阈值、删除阈值）
        - 定义监控频率配置（状态检查间隔、资源采集间隔）
        - 定义安全加固配置（seccomp 配置文件路径）

- [ ] 1.39 编写容器操作工具类
     【目标对象】`app/utils/container_helpers.py`
     【修改目的】提供容器操作的辅助工具方法
     【修改方式】实现纯函数工具集
     【相关依赖】docker-py, uuid
     【修改内容】
        - 生成唯一容器名称
        - 格式化容器配置字典
        - 解析 Docker 容器网络信息
        - 计算资源使用百分比
        - 验证端口范围有效性
        - 生成数据卷路径

- [ ] 1.40 编写 API 文档和示例
     【目标对象】`docs/api/container-api.md`
     【修改目的】提供完整的 API 使用文档
     【修改方式】使用 Markdown 编写文档
     【相关依赖】无
     【修改内容】
        - 容器管理 API 概述
        - 用户容器 API 详细说明（请求/响应示例）
        - 管理员容器 API 详细说明
        - 错误码和错误处理说明
        - 认证和授权说明
        - API 调用示例代码（Python/cURL）

- [ ] 1.41 编写部署文档
     【目标对象】`docs/deployment/container-deployment.md`
     【修改目的】指导容器管理模块的部署
     【修改方式】使用 Markdown 编写文档
     【相关依赖】无
     【修改内容】
        - Docker 环境要求和安装步骤
        - 配置文件说明和环境变量设置
        - 数据库迁移执行步骤
        - Celery Worker 部署说明
        - 健康检查和监控配置
        - 常见问题排查指南

- [ ] 1.42 编写运维手册
     【目标对象】`docs/operations/container-ops.md`
     【修改目的】提供日常运维操作指南
     【修改方式】使用 Markdown 编写文档
     【相关依赖】无
     【修改内容】
        - 容器状态查看和诊断
        - 容器手动操作方法
        - 日志查看和分析
        - 性能监控和调优建议
        - 故障排查流程图
        - 应急预案和恢复步骤
