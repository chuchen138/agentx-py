## 实施
- [ ] 1.1 定义任务实体和数据模型
     【目标对象】`app/domain/task/`
     【修改目的】定义任务相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/task/model/*.java`
     【修改内容】
        - 创建 Task 模型（tasks 表）
        - 创建 TaskAggregate 聚合根模型
        - 定义字段：id, session_id, user_id, parent_task_id, task_name, description, status, progress, start_time, end_time
        - 实现 Pydantic Schema（TaskDTO, TaskCreateRequest）

- [ ] 1.2 实现任务状态枚举
     【目标对象】`app/domain/task/constant/`
     【修改目的】定义任务状态
     【修改方式】使用 Python Enum
     【相关依赖】`AgentX/domain/task/constant/TaskStatus.java`
     【修改内容】
        - 创建 TaskStatus 枚举（WAITING, IN_PROGRESS, COMPLETED, FAILED）
        - 实现状态转换逻辑

- [ ] 1.3 实现任务仓储模式
     【目标对象】`app/domain/task/repository.py`
     【修改目的】定义任务数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 TaskRepository 接口
        - 实现 SQLAlchemy TaskRepository
        - 实现 CRUD 操作
        - 实现复杂查询（按sessionId查询最新任务、按userId查询）

- [ ] 1.4 实现任务领域服务
     【目标对象】`app/domain/task/service.py`
     【修改目的】封装任务相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】TaskRepository
     【修改内容】
        - 创建任务
        - 获取当前会话任务
        - 更新任务状态
        - 更新任务进度
        - 处理父子任务关系

- [ ] 1.5 实现任务组装器
     【目标对象】`app/application/task/assembler.py`
     【修改目的】转换实体和DTO
     【修改方式】实现 Assembler 模式
     【相关依赖】TaskEntity, TaskDTO
     【修改内容】
        - 实现 toEntity (DTO -> Entity)
        - 实现 toDTO (Entity -> DTO)

- [ ] 1.6 实现应用服务层
     【目标对象】`app/application/task/`
     【修改目的】编排任务相关的用例
     【修改方式】实现应用服务
     【相关依赖】TaskDomainService, TaskAssembler
     【修改内容】
        - 实现 TaskAppService（任务管理）
        - 实现获取当前会话任务方法
        - 实现更新任务状态方法

- [ ] 1.7 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/task/`
     【修改目的】暴露任务相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】TaskAppService
     【修改内容】
        - `GET /api/v1/tasks/current-session` - 获取当前会话任务
        - `PATCH /api/v1/tasks/{id}/status` - 更新任务状态

- [ ] 1.8 编写单元测试
     【目标对象】`tests/test_task_service.py`
     【修改目的】确保任务管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】TaskDomainService
     【修改内容】
        - 测试任务创建
        - 测试任务状态更新
        - 测试获取当前会话任务
        - 测试任务进度更新

- [ ] 1.9 编写集成测试
     【目标对象】`tests/integration/test_task_api.py`
     【修改目的】确保任务 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, TaskAppService
     【修改内容】
        - 测试获取当前会话任务 API
        - 测试更新任务状态 API
