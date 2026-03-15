## 实施
- [ ] 1.1 定义定时任务实体和数据模型
     【目标对象】`app/domain/scheduledtask/`
     【修改目的】定义定时任务相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy >= 1.4
     【修改内容】
        - 创建 ScheduledTask 模型（scheduled_tasks 表）
        - 创建 RepeatConfig 模型（重复配置，JSON 字段）
        - 创建 DelayedTaskItem 模型（延迟任务）
        - 创建 TaskExecutionLog 模型（执行日志）
        - 定义字段：id, user_id, agent_id, session_id, content, repeat_type, repeat_config, status, last_execute_time, next_execute_time, max_retry_count, timeout_minutes, last_error, retry_count, notify_on_failure, docker_image, resource_quota
        - 实现 Pydantic Schema（ScheduledTaskDTO, CreateScheduledTaskRequest, UpdateScheduledTaskRequest, TaskExecutionLogDTO）
        - 添加字段校验规则（长度、格式、范围）

- [ ] 1.2 实现重复类型和状态枚举
     【目标对象】`app/domain/scheduledtask/constant/`
     【修改目的】定义重复类型和任务状态
     【修改方式】使用 Python Enum
     【相关依赖】Python enum 模块
     【修改内容】
        - 创建 RepeatType 枚举（IMMEDIATE, INTERVAL, DAILY, WEEKLY, CUSTOM）
        - 创建 ScheduleTaskStatus 枚举（PENDING, RUNNING, COMPLETED, FAILED, PAUSED）
        - 实现状态转换逻辑（validate_status_transition 方法）

- [ ] 1.3 实现定时任务仓储模式
     【目标对象】`app/domain/scheduledtask/repository.py`
     【修改目的】定义定时任务数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ScheduledTaskRepository 接口
        - 实现 SQLAlchemy ScheduledTaskRepository
        - 实现 CRUD 操作
        - 实现复杂查询（按 userId 查询、按 agentId 查询、按 status 查询、按 next_execute_time 范围查询）
        - 实现乐观锁版本控制（version 字段）

- [ ] 1.4 实现任务调度服务
     【目标对象】`app/domain/scheduledtask/service.py`
     【修改目的】封装任务调度逻辑
     【修改方式】使用 APScheduler 实现调度
     【相关依赖】APScheduler >= 3.9, croniter
     【修改内容】
        - 创建 TaskScheduleService（任务调度服务）
        - 实现下次执行时间计算（支持所有重复类型）
        - 实现 Cron 表达式验证（使用 croniter）
        - 实现任务添加到调度器（JobStore 持久化到 Redis）
        - 实现任务删除从调度器
        - 实现任务重新调度
        - 实现调度器负载均衡（多实例场景）

- [ ] 1.5 实现延迟任务队列管理
     【目标对象】`app/domain/scheduledtask/queue.py`
     【修改目的】管理延迟任务队列
     【修改方式】使用 Redis Sorted Set 实现
     【相关依赖】Redis (redis-py)
     【修改内容】
        - 创建 DelayedTaskQueueManager（延迟队列管理器）
        - 实现任务添加到队列（使用 ZADD，score 为执行时间戳）
        - 实现从队列取出任务（使用 ZPOPMIN）
        - 实现任务去重逻辑（使用 task_id 作为 member）
        - 实现任务超时清理（定期扫描过期任务）
        - 实现队列监控（队列长度、积压任务数）

- [ ] 1.6 实现定时任务领域服务
     【目标对象】`app/domain/scheduledtask/service.py`
     【修改目的】封装定时任务相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ScheduledTaskRepository, TaskScheduleService, DistributedLock
     【修改内容】
        - 创建定时任务（含权限校验）
        - 更新定时任务（重新调度）
        - 删除定时任务（取消调度）
        - 获取定时任务
        - 暂停任务（从调度器移除）
        - 恢复任务（重新注册调度）
        - 手动触发任务执行

- [ ] 1.7 实现任务执行服务
     【目标对象】`app/domain/scheduledtask/executor.py`
     【修改目的】处理任务执行逻辑
     【修改方式】实现异步任务执行
     【相关依赖】Celery 或 APScheduler, Docker SDK（沙箱模式）
     【修改内容】
        - 创建 ScheduledTaskExecutionService（任务执行服务）
        - 创建 ScheduleTaskExecutor（任务执行器）
        - 实现任务执行逻辑（含分布式锁）
        - 实现任务失败重试（指数退避）
        - 实现任务超时终止（使用 subprocess 或 Docker 容器超时）
        - 实现任务执行结果记录
        - 实现执行日志审计（敏感信息脱敏）

- [ ] 1.8 实现任务沙箱隔离
     【目标对象】`app/infrastructure/sandbox.py`
     【修改目的】任务执行环境隔离
     【修改方式】使用 Docker 容器
     【相关依赖】Docker SDK for Python, 006 容器管理模块
     【修改内容】
        - 创建 TaskSandbox 类
        - 实现容器创建（限制 CPU/内存）
        - 实现容器销毁
        - 实现网络隔离（禁用外网访问）
        - 实现文件系统隔离（只读挂载）
        - 实现资源监控

- [ ] 1.9 实现输入校验和敏感词过滤
     【目标对象】`app/application/scheduledtask/validator.py`
     【修改目的】防止恶意输入
     【修改方式】正则匹配 + 关键词列表
     【相关依赖】Python re 模块
     【修改内容】
        - 实现任务内容长度校验
        - 实现可执行代码检测（import、eval、exec 等）
        - 实现敏感词过滤（password、secret、token 等）
        - 实现 Cron 表达式合法性校验
        - 实现自动脱敏（日志输出前处理）

- [ ] 1.10 实现定时任务组装器
     【目标对象】`app/application/scheduledtask/assembler.py`
     【修改目的】转换实体和DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】ScheduledTaskEntity, ScheduledTaskDTO
     【修改内容】
        - 实现 toEntity (DTO -> Entity)
        - 实现 toDTO (Entity -> DTO)
        - 实现 entityListToDTOList
        - 处理敏感字段脱敏

- [ ] 1.11 实现应用服务层
     【目标对象】`app/application/scheduledtask/service.py`
     【修改目的】编排定时任务相关的用例
     【修改方式】实现应用服务
     【相关依赖】ScheduledTaskDomainService, TaskScheduleService, ScheduledTaskExecutionService, ScheduledTaskAssembler, TaskValidator
     【修改内容】
        - 实现 ScheduledTaskAppService（定时任务管理）
        - 实现创建定时任务方法（含校验、沙箱配置）
        - 实现更新定时任务方法
        - 实现删除定时任务方法
        - 实现获取定时任务列表方法（分页、过滤）
        - 实现获取定时任务详情方法
        - 实现暂停任务方法
        - 实现恢复任务方法
        - 实现手动触发任务执行方法
        - 实现任务执行历史查询

- [ ] 1.12 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/scheduledtask/`
     【修改目的】暴露定时任务相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ScheduledTaskAppService
     【修改内容】
        - `POST /api/v1/scheduled-tasks` - 创建定时任务
        - `GET /api/v1/scheduled-tasks` - 获取任务列表（支持分页、状态过滤）
        - `GET /api/v1/scheduled-tasks/{id}` - 获取任务详情
        - `PUT /api/v1/scheduled-tasks/{id}` - 更新定时任务
        - `DELETE /api/v1/scheduled-tasks/{id}` - 删除定时任务
        - `POST /api/v1/scheduled-tasks/{id}/pause` - 暂停任务
        - `POST /api/v1/scheduled-tasks/{id}/resume` - 恢复任务
        - `POST /api/v1/scheduled-tasks/{id}/trigger` - 手动触发执行
        - `GET /api/v1/scheduled-tasks/{id}/execution-logs` - 获取执行历史

- [ ] 1.13 实现分布式锁
     【目标对象】`app/infrastructure/distributed_lock.py`
     【修改目的】防止多实例重复执行
     【修改方式】使用 Redis SETNX 实现
     【相关依赖】Redis
     【修改内容】
        - 创建 DistributedLock 类
        - 实现 try_lock 方法（带超时时间）
        - 实现 release_lock 方法
        - 实现锁续期（watchdog 机制）
        - 实现 Redlock 算法（多 Redis 实例场景）

- [ ] 1.14 实现监控和告警
     【目标对象】`app/infrastructure/monitoring/alerting.py`
     【修改目的】任务执行监控
     【修改方式】集成 Prometheus + AlertManager
     【相关依赖】prometheus-client
     【修改内容】
        - 定义监控指标（任务成功率、执行延迟、失败堆积数）
        - 实现告警规则（连续失败、超时、队列积压）
        - 实现通知渠道（邮件、Webhook、站内信）
        - 实现告警历史记录

- [ ] 1.15 实现幂等性保证
     【目标对象】`app/domain/scheduledtask/idempotency.py`
     【修改目的】防止任务重复执行
     【修改方式】唯一键 + 数据库唯一约束
     【相关依赖】Redis, SQLAlchemy
     【修改内容】
        - 实现幂等 key 生成规则（task_id + execute_time）
        - 实现幂等记录存储
        - 实现执行前检查
        - 实现过期幂等记录清理

- [ ] 1.16 编写单元测试
     【目标对象】`tests/test_scheduled_task_service.py`
     【修改目的】确保定时任务管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ScheduledTaskDomainService, TaskScheduleService
     【修改内容】
        - 测试定时任务创建（含边界值、非法输入）
        - 测试定时任务更新
        - 测试定时任务删除
        - 测试任务暂停和恢复
        - 测试下次执行时间计算（各种重复类型）
        - 测试延迟任务队列
        - 测试分布式锁（并发场景）
        - 测试任务超时终止
        - 测试失败重试机制
        - 测试敏感词过滤

- [ ] 1.17 编写集成测试
     【目标对象】`tests/integration/test_scheduled_task_api.py`
     【修改目的】确保定时任务 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, ScheduledTaskAppService
     【修改内容】
        - 测试创建定时任务 API（含校验失败场景）
        - 测试获取任务列表 API
        - 测试更新定时任务 API
        - 测试删除定时任务 API
        - 测试暂停和恢复任务 API
        - 测试手动触发执行 API
        - 测试执行历史查询 API
        - 测试权限隔离（跨用户访问）
        - 测试分布式环境防重复执行
