## 实施
- [ ] 1.1 定义定时任务实体和数据模型
     【目标对象】`app/domain/scheduledtask/`
     【修改目的】定义定时任务相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/scheduledtask/model/*.java`
     【修改内容】
        - 创建 ScheduledTask 模型（scheduled_tasks 表）
        - 创建 RepeatConfig 模型（重复配置）
        - 创建 DelayedTaskItem 模型（延迟任务）
        - 定义字段：id, user_id, agent_id, session_id, content, repeat_type, repeat_config, status, last_execute_time, next_execute_time
        - 实现 Pydantic Schema（ScheduledTaskDTO, CreateScheduledTaskRequest, UpdateScheduledTaskRequest）

- [ ] 1.2 实现重复类型和状态枚举
     【目标对象】`app/domain/scheduledtask/constant/`
     【修改目的】定义重复类型和任务状态
     【修改方式】使用 Python Enum
     【相关依赖】`AgentX/domain/scheduledtask/constant/*.java`
     【修改内容】
        - 创建 RepeatType 枚举（ONCE, DAILY, WEEKLY, MONTHLY, CRON）
        - 创建 ScheduleTaskStatus 枚举（ACTIVE, PAUSED, TRIGGERED, COMPLETED, FAILED）
        - 实现状态转换逻辑

- [ ] 1.3 实现定时任务仓储模式
     【目标对象】`app/domain/scheduledtask/repository.py`
     【修改目的】定义定时任务数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ScheduledTaskRepository 接口
        - 实现 SQLAlchemy ScheduledTaskRepository
        - 实现 CRUD 操作
        - 实现复杂查询（按userId查询、按agentId查询、按status查询）

- [ ] 1.4 实现任务调度服务
     【目标对象】`app/domain/scheduledtask/`
     【修改目的】封装任务调度逻辑
     【修改方式】使用 APScheduler 实现调度
     【相关依赖】APScheduler
     【修改内容】
        - 创建 TaskScheduleService（任务调度服务）
        - 实现下次执行时间计算
        - 实现任务添加到调度器
        - 实现任务删除从调度器
        - 实现任务重新调度

- [ ] 1.5 实现延迟任务队列管理
     【目标对象】`app/domain/scheduledtask/`
     【修改目的】管理延迟任务队列
     【修改方式】使用 Redis Sorted Set 实现
     【相关依赖】Redis
     【修改内容】
        - 创建 DelayedTaskQueueManager（延迟队列管理器）
        - 实现任务添加到队列
        - 实现从队列取出任务
        - 实现任务去重逻辑
        - 实现任务超时清理

- [ ] 1.6 实现定时任务领域服务
     【目标对象】`app/domain/scheduledtask/service.py`
     【修改目的】封装定时任务相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ScheduledTaskRepository, TaskScheduleService
     【修改内容】
        - 创建定时任务
        - 更新定时任务
        - 删除定时任务
        - 获取定时任务
        - 暂停任务
        - 恢复任务

- [ ] 1.7 实现任务执行服务
     【目标对象】`app/domain/scheduledtask/`
     【修改目的】处理任务执行逻辑
     【修改方式】实现异步任务执行
     【相关依赖】Celery 或 APScheduler
     【修改内容】
        - 创建 ScheduledTaskExecutionService（任务执行服务）
        - 实现任务调度
        - 实现任务取消调度
        - 实现任务重新调度
        - 实现任务删除
        - 创建 ScheduleTaskExecutor（任务执行器）
        - 实现任务执行逻辑
        - 实现任务失败重试
        - 实现任务执行结果记录

- [ ] 1.8 实现定时任务组装器
     【目标对象】`app/application/scheduledtask/assembler.py`
     【修改目的】转换实体和DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】ScheduledTaskEntity, ScheduledTaskDTO
     【修改内容】
        - 实现 toEntity (DTO -> Entity)
        - 实现 toDTO (Entity -> DTO)

- [ ] 1.9 实现应用服务层
     【目标对象】`app/application/scheduledtask/`
     【修改目的】编排定时任务相关的用例
     【修改方式】实现应用服务
     【相关依赖】ScheduledTaskDomainService, TaskScheduleService, ScheduledTaskExecutionService, ScheduledTaskAssembler
     【修改内容】
        - 实现 ScheduledTaskAppService（定时任务管理）
        - 实现创建定时任务方法
        - 实现更新定时任务方法
        - 实现删除定时任务方法
        - 实现获取定时任务列表方法
        - 实现获取定时任务详情方法
        - 实现暂停任务方法
        - 实现恢复任务方法
        - 实现手动触发任务执行方法

- [ ] 1.10 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/scheduledtask/`
     【修改目的】暴露定时任务相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ScheduledTaskAppService
     【修改内容】
        - `POST /api/v1/scheduled-tasks` - 创建定时任务
        - `GET /api/v1/scheduled-tasks` - 获取任务列表
        - `GET /api/v1/scheduled-tasks/{id}` - 获取任务详情
        - `PUT /api/v1/scheduled-tasks/{id}` - 更新定时任务
        - `DELETE /api/v1/scheduled-tasks/{id}` - 删除定时任务
        - `POST /api/v1/scheduled-tasks/{id}/pause` - 暂停任务
        - `POST /api/v1/scheduled-tasks/{id}/resume` - 恢复任务
        - `POST /api/v1/scheduled-tasks/{id}/trigger` - 手动触发执行

- [ ] 1.11 编写单元测试
     【目标对象】`tests/test_scheduled_task_service.py`
     【修改目的】确保定时任务管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ScheduledTaskDomainService, TaskScheduleService
     【修改内容】
        - 测试定时任务创建
        - 测试定时任务更新
        - 测试定时任务删除
        - 测试任务暂停和恢复
        - 测试下次执行时间计算
        - 测试延迟任务队列

- [ ] 1.12 编写集成测试
     【目标对象】`tests/integration/test_scheduled_task_api.py`
     【修改目的】确保定时任务 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, ScheduledTaskAppService
     【修改内容】
        - 测试创建定时任务 API
        - 测试获取任务列表 API
        - 测试更新定时任务 API
        - 测试删除定时任务 API
        - 测试暂停和恢复任务 API
        - 测试手动触发执行 API
