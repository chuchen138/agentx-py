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
     【相关依赖】`AgentX/domain/container/model/*.java`
     【修改内容】
        - 创建 Container 模型（user_containers 表）
        - 创建 ContainerTemplate 模型（container_templates 表）
        - 定义字段和关系
        - 实现 Pydantic Schema（ContainerDTO, ContainerTemplateDTO）

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
     【修改方式】实现 FastAPI 中间件
     【相关依赖】PyJWT, 用户认证服务
     【修改内容】
        - 检测用户权限（管理员/普通用户）
        - 将用户信息注入 Request 对象
        - 处理认证失败

- [ ] 1.18 创建数据库迁移脚本
     【目标对象】`alembic/versions/`
     【修改目的】创建容器相关表结构
     【修改方式】使用 Alembic 迁移
     【相关依赖】SQLAlchemy, Alembic
     【修改内容】
        - 创建 user_containers 表迁移脚本
        - 创建 container_templates 表迁移脚本
        - 创建必要的索引
        - 添加外键约束

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
