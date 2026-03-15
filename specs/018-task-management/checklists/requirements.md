## 实施清单

### 阶段 1：数据模型和基础设施

- [ ] 1.1 定义任务实体和数据模型
     【目标对象】`app/domain/task/model/`
     【修改目的】定义任务相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic v2
     【修改内容】
        - 创建 Task 模型（tasks 表）
        - 字段：id (UUID), session_id, user_id, parent_task_id, task_name, description, status, progress, start_time, end_time, task_result, version, deleted_at, created_at, updated_at
        - 索引：idx_session_created, idx_user_status, idx_parent_task, idx_deleted_at
        - 实现 Pydantic Schema（TaskDTO, TaskCreateRequest, TaskQueryRequest）
        - 字段长度限制：task_name(256), description(4096), task_result(65535)

- [ ] 1.2 实现任务状态枚举
     【目标对象】`app/domain/task/constant/task_status.py`
     【修改目的】定义任务状态
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 TaskStatus 枚举（WAITING, IN_PROGRESS, COMPLETED, FAILED）
        - 定义状态转换规则（guard conditions）
        - 实现状态转换验证方法

- [ ] 1.3 定义数据库 schema 和迁移脚本
     【目标对象】`app/infrastructure/database/migrations/`
     【修改目的】创建任务表结构
     【修改方式】Alembic 迁移脚本
     【相关依赖】Alembic, PostgreSQL
     【修改内容】
        - 创建 tasks 表（包含所有字段和约束）
        - 创建复合索引
        - 添加外键约束（session_id, user_id, parent_task_id）
        - 启用行级安全策略（RLS）

---

### 阶段 2：仓储层和数据访问

- [ ] 2.1 实现任务仓储接口
     【目标对象】`app/domain/task/repository.py`
     【修改目的】定义任务数据访问接口
     【修改方式】实现 Repository 模式（ABC 抽象基类）
     【相关依赖】SQLAlchemy, AsyncSession
     【修改内容】
        - 定义 TaskRepository 接口（抽象方法）
        - CRUD 方法：create, find_by_id, update, delete
        - 复杂查询：find_by_session_id, find_by_user_id, find_with_subtasks
        - 支持软删除过滤（默认排除 deleted_at 不为空的任务）

- [ ] 2.2 实现 SQLAlchemy 仓储
     【目标对象】`app/infrastructure/task/repository_impl.py`
     【修改目的】实现具体的数据访问逻辑
     【修改方式】继承 TaskRepository 接口
     【相关依赖】SQLAlchemy, AsyncSession, Task Model
     【修改内容】
        - 实现所有接口方法
        - 使用 async/await 异步操作
        - 实现乐观锁检查（version字段 CAS 更新）
        - 实现行级安全过滤（自动注入 WHERE user_id = :current_user_id）

- [ ] 2.3 实现 Redis 缓存（可选优化）
     【目标对象】`app/infrastructure/cache/task_cache.py`
     【修改目的】缓存频繁访问的任务数据
     【修改方式】使用 aioredis
     【相关依赖】aioredis, TaskDTO
     【修改内容】
        - 缓存键模式：`task:session:{session_id}:current`
        - TTL：5 分钟（进度缓存），状态变更时失效
        - 方法：get_current_session_tasks, set_current_session_tasks, invalidate_cache

---

### 阶段 3：领域服务层

- [ ] 3.1 实现任务领域服务
     【目标对象】`app/domain/task/service.py`
     【修改目的】封装任务相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】TaskRepository, TaskAssembler
     【修改内容】
        - 创建任务（generate UUID, set default values）
        - 获取当前会话任务（返回 TaskAggregate）
        - 更新任务状态（验证状态转换，更新 timestamps）
        - 更新任务进度（0-100 范围验证）
        - 处理父子任务关系（级联软删除）
        - 权限验证（检查 user_id 匹配）

- [ ] 3.2 实现任务组装器
     【目标对象】`app/application/task/assembler.py`
     【修改目的】转换实体和DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】TaskEntity, TaskDTO
     【修改内容】
        - toEntity 方法（DTO -> Entity）
        - toDTO 方法（Entity -> DTO）
        - toAggregate 方法（Entity List -> TaskAggregate）
        - 敏感字段脱敏处理（如需要）

---

### 阶段 4：应用服务层

- [ ] 4.1 实现应用服务层
     【目标对象】`app/application/task/`
     【修改目的】编排任务相关的用例
     【修改方式】实现应用服务
     【相关依赖】TaskDomainService, TaskAssembler, TaskCache
     【修改内容】
        - 实现 TaskAppService（任务管理）
        - 实现获取当前会话任务方法（带缓存）
        - 实现更新任务状态方法（带乐观锁重试）
        - 实现查询任务列表方法（支持过滤和分页）
        - 事务管理（@transactional 装饰器）

---

### 阶段 5：API 路由层

- [ ] 5.1 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/task/`
     【修改目的】暴露任务相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】TaskAppService, FastAPI
     【修改内容】
        - `GET /api/v1/tasks/current-session` - 获取当前会话任务
        - `GET /api/v1/tasks/query` - 查询任务列表（支持过滤和分页）
        - `PATCH /api/v1/tasks/{id}/status` - 更新任务状态
        - `GET /api/v1/tasks/{id}` - 获取单个任务详情
        - 参数校验（Pydantic BaseModel）
        - 错误处理（404, 403, 409）

---

### 阶段 6：安全实现

- [ ] 6.1 实现行级安全策略（RLS）
     【目标对象】`app/infrastructure/database/migrations/`
     【修改目的】强制用户数据隔离
     【修改方式】PostgreSQL RLS 策略
     【相关依赖】PostgreSQL
     【修改内容】
        - 启用 tasks 表的 RLS
        - 创建策略：用户只能访问自己的任务（user_id = current_user_id）
        - 管理员例外策略（admin 角色可访问所有）

- [ ] 6.2 实现任务结果加密（敏感数据）
     【目标对象】`app/infrastructure/security/encryption.py`
     【修改目的】加密存储敏感任务结果
     【修改方式】AES-256 加密
     【相关依赖】cryptography 库
     【修改内容】
        - 实现 encrypt_task_result 方法
        - 实现 decrypt_task_result 方法
        - 密钥管理（从环境变量读取）
        - 标记敏感任务（is_sensitive 字段）

- [ ] 6.3 实现审计日志
     【目标对象】`app/domain/task/audit_log.py`
     【修改目的】记录任务操作日志
     【修改方式】AOP 装饰器 + 独立审计表
     【相关依赖】SQLAlchemy, 装饰器
     【修改内容】
        - 创建 task_audit_log 表
        - 记录操作：谁（user_id）、何时（timestamp）、什么操作（action）、任务 ID（task_id）
        - 审计事件：TASK_CREATED, TASK_STATUS_CHANGED, TASK_DELETED
        - 实现 @audit_log 装饰器

---

### 阶段 7：性能优化

- [ ] 7.1 创建复合索引
     【目标对象】`app/infrastructure/database/migrations/`
     【修改目的】优化查询性能
     【修改方式】Alembic 迁移脚本
     【相关依赖】Alembic, PostgreSQL
     【修改内容】
        - idx_session_created: (session_id, created_at DESC)
        - idx_user_status: (user_id, status)
        - idx_parent_task: (parent_task_id)
        - 使用 EXPLAIN 分析查询计划

- [ ] 7.2 实现批量更新
     【目标对象】`app/infrastructure/task/repository_impl.py`
     【修改目的】支持 bulk 操作
     【修改方式】SQLAlchemy bulk_update
     【相关依赖】SQLAlchemy
     【修改内容】
        - bulk_update_statuses(task_ids, new_status)
        - bulk_delete_tasks(task_ids)
        - 事务保证一致性

- [ ] 7.3 配置连接池
     【目标对象】`app/infrastructure/database/connection.py`
     【修改目的】优化数据库连接管理
     【修改方式】SQLAlchemy async engine
     【相关依赖】SQLAlchemy, asyncio
     【修改内容】
        - 连接池大小：CPU cores * 2 + disk_spindles
        - 最大连接数：50（可配置）
        - 连接超时：30 秒
        - 启用连接回收（pool_recycle=3600）

---

### 阶段 8：测试

- [ ] 8.1 编写单元测试
     【目标对象】`tests/test_task_service.py`
     【修改目的】确保任务管理功能正确性
     【修改方式】使用 pytest + pytest-asyncio
     【相关依赖】pytest, TaskDomainService
     【修改内容】
        - 测试任务创建
        - 测试任务状态更新（包括状态转换验证）
        - 测试获取当前会话任务
        - 测试任务进度更新
        - 测试乐观锁冲突处理
        - 测试权限验证（user_id 不匹配场景）

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_task_api.py`
     【修改目的】确保任务 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, TaskAppService, httpx
     【修改内容】
        - 测试获取当前会话任务 API
        - 测试更新任务状态 API
        - 测试查询任务列表 API（过滤和分页）
        - 测试 403 Forbidden（跨用户访问）
        - 测试 409 Conflict（版本冲突）

- [ ] 8.3 编写性能测试
     【目标对象】`tests/performance/test_task_performance.py`
     【修改目的】验证性能指标达标
     【修改方式】使用 pytest-benchmark 或 locust
     【相关依赖】pytest-benchmark 或 locust
     【修改内容】
        - 基准测试：状态更新延迟 <50ms (P95)
        - 基准测试：查询延迟 <100ms (P95)
        - 负载测试：并发 1000 次更新/秒
        - 压力测试：同时追踪 5000 个任务

- [ ] 8.4 编写安全测试
     【目标对象】`tests/security/test_task_security.py`
     【修改目的】验证安全控制有效性
     【修改方式】渗透测试风格
     【相关依赖】pytest, 自定义测试用例
     【修改内容】
        - 测试越权访问（用户 A 访问用户 B 的任务）
        - 测试 SQL 注入防护
        - 测试敏感数据加密存储
        - 测试审计日志记录完整性

---

### 阶段 9：与 014/016 集成

- [ ] 9.1 与 014-agent-workflow 集成
     【目标对象】`app/api/v1/task/` 和 `014-agent-workflow/`
     【修改目的】提供持久化服务给编排引擎
     【修改方式】直接服务调用（无 HTTP）
     【相关依赖】TaskAppService, 014 的状态机
     【修改内容】
        - 014 调用 TaskAppService.update_status() 在状态转换时
        - 014 调用 TaskAppService.create_task() 在创建任务时
        - 定义清晰的接口契约（输入输出）
        - 异常处理和回滚机制

- [ ] 9.2 与 016-execution-trace 集成
     【目标对象】`app/domain/task/service.py` 和 `016-execution-trace/`
     【修改目的】自动产生执行追踪 span
     【修改方式】发布 - 订阅模式（事件总线）
     【相关依赖】EventBus, TraceCollector
     【修改内容】
        - 任务状态变更时发布 TaskStatusChangedEvent
        - 事件 payload：{task_id, old_status, new_status, timestamp, user_id}
        - 016 监听事件并创建 trace span
        - correlation_id: trace_id 关联任务和执行链路

---

### 阶段 10：文档和部署

- [ ] 10.1 编写 API 文档
     【目标对象】`docs/api/task-management.md`
     【修改目的】提供 API 使用说明
     【修改方式】Markdown + OpenAPI/Swagger
     【相关依赖】FastAPI 自动生成 Swagger UI
     【修改内容】
        - 所有 API 端点说明
        - 请求/响应示例
        - 错误码说明
        - 认证和授权说明

- [ ] 10.2 编写运维手册
     【目标对象】`ops/task-maintenance.md`
     【修改目的】指导日常运维和问题排查
     【修改方式】Markdown
     【相关依赖】无
     【修改内容】
        - 监控指标（延迟、吞吐量、错误率）
        - 告警阈值配置
        - 常见问题排查步骤
        - 数据备份和恢复策略

- [ ] 10.3 Docker 镜像和 compose 配置
     【目标对象】`docker-compose.yml` 和 `Dockerfile`
     【修改目的】容器化部署
     【修改方式】Docker
     【相关依赖】Docker, docker-compose
     【修改内容】
        - 构建 Python 应用镜像
        - 配置 PostgreSQL 连接
        - 配置 Redis 连接（如果使用）
        - 健康检查端点
