## 实施清单

### 阶段一：核心基础设施

- [ ] 1.1 定义规则实体和数据模型
     【目标对象】`app/domain/rule/model/`
     【修改目的】定义规则相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【修改内容】
        - 创建 Rule 模型（rules 表）
        - 定义字段：id, name, handler_key, description, config(JSON), enabled, priority, version, created_at, updated_at, updated_by
        - 实现 Pydantic Schema（RuleDTO, CreateRuleRequest, UpdateRuleRequest, QueryRuleRequest, RuleVersionDTO）
        - 创建 RuleVersion 模型（rule_versions 表）
        - 创建 RuleAuditLog 模型（rule_audit_logs 表）

- [ ] 1.2 实现规则处理器标识常量
     【目标对象】`app/domain/rule/constant/rule_handler_key.py`
     【修改目的】定义规则处理器标识常量
     【修改方式】使用常量类
     【修改内容】
        - 创建 RuleHandlerKey 常量类
        - 定义常用处理器标识常量：
          - 计费规则：MODEL_USAGE_BILLING, AGENT_CREATION_BILLING, API_CALL_BILLING
          - 权限规则：FEATURE_ACCESS_PERMISSION, OPERATION_PERMISSION
          - 业务策略：RATE_LIMITING, AB_TEST_ONBOARDING, CIRCUIT_BREAKER
        - 提供验证方法：validate(handler_key: str) -> bool

- [ ] 1.3 实现规则仓储模式
     【目标对象】`app/domain/rule/repository/`
     【修改目的】定义规则数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy, Redis
     【修改内容】
        - 定义 IRuleRepository 接口
        - 实现 SQLAlchemyRuleRepository
        - 实现 CRUD 操作：create, update, delete, get_by_id
        - 实现复杂查询：
          - get_by_handler_key(handler_key, enabled=True)
          - list_by_handler_keys(handler_keys: List[str])
          - list(keyword, handler_key, enabled, priority, page, page_size, sort_by, sort_order)
          - get_versions(rule_id)
        - 集成 Redis 缓存：
          - get_by_handler_key_with_cache(handler_key)
          - invalidate_cache(handler_key)
          - warmup_cache()

- [ ] 1.4 实现规则汇编器
     【目标对象】`app/domain/rule/assembler.py`
     【修改目的】转换实体和 DTO
     【修改方式】实现 Assembler 模式
     【修改内容】
        - 实现 toEntity (DTO -> Entity)
        - 实现 toDTO (Entity -> DTO)
        - 实现 toVersionDTO (VersionEntity -> VersionDTO)

### 阶段二：领域服务与安全

- [ ] 2.1 实现规则领域服务
     【目标对象】`app/domain/rule/service.py`
     【修改目的】封装规则相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】IRuleRepository, IRuleHandler, RuleValidator
     【修改内容】
        - 创建规则（验证 handlerKey 唯一性、初始化 version=1）
        - 更新规则（乐观锁检查、version++、记录审计日志）
        - 删除规则（软删除、标记 enabled=false）
        - 获取规则详情（按 ID）
        - 获取规则详情（按 HandlerKey，带缓存）
        - 获取规则历史版本列表
        - 回滚到指定版本（创建新版本快照）
        - 查询规则列表（支持 enabled 过滤、优先级排序）
        - 启用/禁用规则

- [ ] 2.2 实现规则验证器
     【目标对象】`app/domain/rule/validator.py`
     【修改目的】验证规则内容安全性
     【修改方式】实现验证器模式
     【修改内容】
        - 验证 handlerKey 合法性
        - 验证规则名称不为空（长度 1-200）
        - 验证描述长度限制（<500 字符）
        - 验证 config JSON 结构
        - **安全检查**: 检测恶意代码注入（如 eval、exec、__import__等）
        - **白名单校验**: 如果 config 包含 expression 字段，限制可用的函数和操作符
        - 验证 priority 范围（0-1000）

- [ ] 2.3 实现规则执行审计
     【目标对象】`app/domain/rule/audit.py`
     【修改目的】记录规则执行日志
     【修改内容】
        - 定义 RuleAuditLog 实体
        - 记录规则变更（CREATE/UPDATE/DELETE）：
          - rule_id, action, old_value, new_value, operator, ip_address
        - 记录规则执行（EXECUTE）：
          - rule_id, handler_key, context_hash, result, execution_time_ms, timestamp
        - 异步写入（通过消息队列或后台任务）
        - 实现审计日志查询接口

### 阶段三：策略工厂与执行引擎

- [ ] 3.1 实现规则处理器接口
     【目标对象】`app/domain/rule/handler/__init__.py`
     【修改目的】定义标准处理器接口
     【修改内容】
        - 定义 IRuleHandler 抽象基类
        - 定义 RuleContext 和 RuleResult 数据传输对象
        - 定义 RuleExecutionError 异常类
        - 定义 ConcurrencyError 异常类

- [ ] 3.2 实现策略工厂
     【目标对象】`app/domain/rule/factory.py`
     【修改目的】根据 handlerKey 获取对应处理器
     【修改方式】使用装饰器模式自动注册
     【修改内容】
        - 实现 RuleHandlerFactory
        - 实现 @rule_handler 装饰器（自动注册处理器）
        - 实现 get_handler(handler_key: str) -> IRuleHandler
        - 实现 get_all_handlers() -> Dict[str, IRuleHandler]
        - 实现处理器自动发现机制（auto_discover_handlers）

- [ ] 3.3 实现内置规则处理器
     【目标对象】`app/domain/rule/handler/builtin/`
     【修改目的】提供常用规则处理器实现
     【修改内容】
        - ModelUsageBillingHandler（模型计费）
        - AgentCreationBillingHandler（Agent 创建计费）
        - ApiCallBillingHandler（API 调用计费）
        - FeatureAccessPermissionHandler（功能访问权限）
        - RateLimitingHandler（限流策略）
        - AbTestOnboardingHandler（A/B 测试）

- [ ] 3.4 实现规则执行引擎
     【目标对象】`app/domain/rule/engine.py`
     【修改目的】提供规则执行能力
     【修改内容】
        - 实现 RuleEngine 类
        - 实现 execute(rule_id, context) 方法：
          - 加载规则（带缓存）
          - 获取处理器
          - 执行规则
          - 记录审计日志
        - 实现 execute_batch(requests) 方法（批量异步执行）
        - 集成缓存（Redis + Local LRU）
        - 实现超时控制（单规则执行<1s）
        - 实现失败重试（最多 2 次）

### 阶段四：应用服务与 API

- [ ] 4.1 实现应用服务层
     【目标对象】`app/application/rule/`
     【修改目的】编排规则相关的用例
     【修改方式】实现应用服务
     【相关依赖】RuleDomainService, RuleAssembler, RuleEngine
     【修改内容】
        - 实现 RuleAppService（规则管理）
        - 实现创建规则方法（含审计日志）
        - 实现更新规则方法（含版本管理）
        - 实现获取规则详情方法
        - 实现获取规则列表方法
        - 实现按 HandlerKey 查询规则方法
        - 实现获取历史版本方法
        - 实现回滚到指定版本方法
        - 实现启用/禁用规则方法

- [ ] 4.2 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/rule/`
     【修改目的】暴露规则相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】RuleAppService, AuthDependency
     【修改内容】
        - `POST /api/v1/rules` - 创建规则（需 ADMIN 权限）
        - `GET /api/v1/rules` - 获取规则列表（支持分页、过滤、排序）
        - `GET /api/v1/rules/{id}` - 获取规则详情
        - `PUT /api/v1/rules/{id}` - 更新规则（需 ADMIN 权限）
        - `DELETE /api/v1/rules/{id}` - 删除规则（需 ADMIN 权限）
        - `GET /api/v1/rules/by-handler-key/{handlerKey}` - 按处理器标识查询规则
        - `GET /api/v1/rules/{id}/versions` - 获取规则历史版本
        - `POST /api/v1/rules/{id}/rollback/{version}` - 回滚到指定版本
        - `POST /api/v1/rules/{id}/toggle` - 启用/禁用规则
        - `POST /api/v1/rules/execute` - 执行规则（供内部服务调用，需 API Key 认证）

### 阶段五：监控与优化

- [ ] 5.1 实现规则执行监控
     【目标对象】`app/infrastructure/monitoring/rule_metrics.py`
     【修改目的】收集规则执行指标
     【修改内容】
        - 记录规则执行次数（按 handlerKey 分组）
        - 记录规则执行成功率
        - 记录规则执行延迟（P50/P90/P99）
        - 记录缓存命中率（本地缓存、Redis 缓存）
        - 集成 Prometheus 导出指标
        - 创建 Grafana 仪表盘模板

- [ ] 5.2 实现告警规则
     【目标对象】`app/infrastructure/alerting/rule_alerts.py`
     【修改目的】规则异常告警
     【修改内容】
        - 规则失败率>5% 告警（持续 5 分钟）
        - 规则执行延迟>P99>100ms 告警
        - 规则缓存失效告警（Redis 连接失败）
        - 非法规则内容检测到告警（安全事件）
        - 集成 AlertManager 或 Webhook 通知

- [ ] 5.3 性能优化
     【目标对象】`app/domain/rule/`
     【修改内容】
        - 实现多级缓存：
          - 本地 LRU Cache（maxsize=100）
          - Redis 分布式缓存（TTL=5min）
        - 实现缓存预热（启动时加载所有 enabled 规则）
        - 实现批量查询优化（IN 查询代替循环）
        - 实现规则预加载（启动时加载所有 enabled 规则到内存）
        - 实现数据库索引优化

### 阶段六：测试与文档

- [ ] 6.1 编写单元测试
     【目标对象】`tests/unit/domain/rule/`
     【修改目的】确保规则管理功能正确性
     【修改方式】使用 pytest + pytest-asyncio
     【修改内容】
        - 测试规则创建（正常场景 + 边界场景）
        - 测试规则更新（版本递增、乐观锁）
        - 测试规则删除（软删除）
        - 测试获取规则详情（缓存命中/未命中）
        - 测试按 HandlerKey 查询规则
        - 测试规则列表查询（分页、过滤、排序）
        - 测试规则版本管理（回滚）
        - **测试规则执行正确性**（每个内置处理器）
        - **测试规则冲突场景**（同 handlerKey 多条规则）
        - **测试安全校验**（恶意代码注入拦截）
        - 测试规则验证器（边界值、非法输入）

- [ ] 6.2 编写集成测试
     【目标对象】`tests/integration/rule/`
     【修改目的】确保规则 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient + TestContainer
     【修改内容】
        - 测试创建规则 API（权限验证）
        - 测试获取规则列表 API
        - 测试获取规则详情 API
        - 测试更新规则 API（版本变化）
        - 测试删除规则 API
        - 测试按 HandlerKey 查询规则 API
        - 测试规则回滚 API
        - 测试规则执行 API（端到端）
        - **性能压测**: 1000 并发请求，响应时间<100ms

- [ ] 6.3 编写使用文档
     【目标对象】`docs/rule-engine/`
     【修改内容】
        - 规则引擎快速开始指南
        - 如何自定义规则处理器
        - 规则配置最佳实践
        - 常见问题排查
        - 性能调优指南

- [ ] 6.4 编写运维文档
     【目标对象】`docs/rule-engine/operations.md`
     【修改内容】
        - 规则备份与恢复流程
        - 缓存清理操作手册
        - 监控指标解读
        - 告警响应流程
        - 版本升级指南
