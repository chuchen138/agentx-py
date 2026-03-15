## 实施
- [ ] 1.1 定义高可用性模型和枚举
     【目标对象】`app/domain/highavailability/`
     【修改目的】定义高可用相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/highavailability/*.java`
     【修改内容】
        - 创建 ServiceHealth 模型（service_health 表）
        - 创建 HAEvent 模型（ha_events 表）
        - 定义 ServiceStatusEnum 枚举（HEALTHY, DEGRADED, UNHEALTHY）
        - 定义 EventTypeEnum 枚举（FAIL_OVER, RECOVER, CONFIG_CHANGE）
        - 实现 Pydantic Schema

- [ ] 1.2 实现高可用仓储模式
     【目标对象】`app/domain/highavailability/repository.py`
     【修改目的】定义高可用数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ServiceHealthRepository 接口
        - 定义 HAEventRepository 接口
        - 实现 SQLAlchemy ServiceHealthRepository
        - 实现 SQLAlchemy HAEventRepository
        - 实现 CRUD 操作
        - 实现按服务ID查询
        - 实现查询所有 unhealthy 服务

- [ ] 1.3 实现高可用领域服务
     【目标对象】`app/domain/highavailability/service.py`
     【修改目的】封装高可用相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ServiceHealthRepository, HAEventRepository
     【修改内容】
        - 创建服务健康记录
        - 更新服务健康状态
        - 记录故障数量
        - 计算服务可用性评分
        - 记录高可用事件

- [ ] 1.4 实现高可用网关
     【目标对象】`app/domain/highavailability/gateway/ha_gateway.py`
     【修改目的】定义高可用网关统一入口
     【修改方式】实现网关模式
     【相关依赖】ServiceHealthRepository
     【修改内容】
        - 定义 HighAvailabilityGateway 接口
        - routeRequest - 路由请求到可用服务
        - executeRequest - 执行请求并处理故障
        - getAvailableService - 获取可用服务
        - handleFailure - 处理服务故障

- [ ] 1.5 实现健康检查服务
     【目标对象】`app/domain/highavailability/health_check_service.py`
     【修改目的】执行服务健康检查
     【修改方式】实现健康检查服务
     【相关依赖】httpx, ServiceHealthRepository
     【修改内容】
        - checkServiceHealth - 检查单个服务健康
        - checkAllServices - 检查所有服务健康
        - 健康检查间隔配置
        - 健康检查超时处理
        - 服务降级处理

- [ ] 1.6 实现故障转移服务
     【目标对象】`app/domain/highavailability/failover_service.py`
     【修改目的】实现自动故障转移
     【修改方式】实现故障转移服务
     【相关依赖】ServiceHealthRepository, HAEventRepository
     【修改内容】
        - detectFailure - 检测服务故障
        - initiateFailover - 启动故障转移
        - recoverService - 服务恢复后处理
        - 故障计数阈值配置
        - 故障转移策略

- [ ] 1.7 实现应用服务层 - 高可用管理
     【目标对象】`app/application/highavailability/service/`
     【修改目的】编排高可用相关的用例
     【修改方式】实现应用服务
     【相关依赖】HighAvailabilityDomainService
     【修改内容】
        - 实现 HAConfigService（高可用配置管理）
        - getServiceHealth - 获取服务健康状态
        - getAllServicesHealth - 获取所有服务健康状态
        - manualFailover - 手动触发故障转移
        - updateHAConfig - 更新高可用配置
        - getHAEvents - 获取高可用事件日志

- [ ] 1.8 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/ha/`
     【修改目的】暴露高可用相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】HAConfigService
     【修改内容】
        - `GET /api/v1/ha/health/service/{service_id}` - 获取服务健康状态
        - `GET /api/v1/ha/health/status` - 获取所有服务健康状态
        - `POST /api/v1/ha/failover/service/{service_id}` - 手动触发故障转移
        - `GET /api/v1/ha/events` - 获取高可用事件日志
        - `PUT /api/v1/ha/config` - 更新高可用配置

- [ ] 1.9 实现高可用事件监听器
     【目标对象】`app/application/highavailability/listener.py`
     【修改目的】监听高可用事件并处理
     【修改方式】实现事件监听器
     【相关依赖】HAEventRepository, AlertService
     【修改内容】
        - 监听故障事件
        - 监听恢复事件
        - 监听配置变更事件
        - 触发告警通知（邮件、短信、Webhook）
        - 告警去重和收敛逻辑
        - 集成 Slack/钉钉/企业微信

- [ ] 1.10 实现健康检查定时任务
     【目标对象】`app/infrastructure/scheduler/health_check_scheduler.py`
     【修改目的】定期执行健康检查
     【修改方式】使用 APScheduler
     【相关依赖】HealthCheckService, ServiceHealthRepository
     【修改内容】
        - 定义定时任务（每 30 秒执行一次）
        - 异步执行健康检查（不阻塞主线程）
        - 处理并发检查（使用信号量控制）
        - 任务调度和取消机制
        - 定时任务监控指标

- [ ] 1.11 实现权重动态调整服务
     【目标对象】`app/domain/highavailability/weight_adjustment_service.py`
     【修改目的】根据延迟和错误率动态调整实例权重
     【修改方式】实现权重调整算法
     【相关依赖】ServiceHealthRepository, LoadBalancer
     【修改内容】
        - 基于响应时间的权重计算（响应越快权重越高）
        - 基于错误率的权重惩罚（错误率越高权重越低）
        - 平滑权重更新（避免剧烈波动）
        - 权重上下限配置（默认 0.1-1.0）
        - 权重调整日志和审计
        - 支持手动锁定权重

- [ ] 1.12 实现手动强制切换/恢复接口
     【目标对象】`app/api/v1/ha/manual_control.py`
     【修改目的】提供管理员手动干预能力
     【修改方式】FastAPI REST API
     【相关依赖】HighAvailabilityDomainService
     【修改内容】
        - `POST /api/v1/ha/manual/failover` - 手动触发故障切换
        - `POST /api/v1/ha/manual/recover` - 手动恢复服务
        - `PUT /api/v1/ha/manual/lock-instance` - 锁定/解锁实例
        - `PUT /api/v1/ha/manual/set-weight` - 手动设置实例权重
        - 权限验证（仅管理员）
        - 操作审计日志
        - 防止误操作确认机制

- [ ] 1.13 实现分布式锁服务
     【目标对象】`app/infrastructure/distributed_lock.py`
     【修改目的】防止多实例同时执行故障切换
     【修改方式】Redis RedLock 算法
     【相关依赖】Redis
     【修改内容】
        - 实现 Redis 分布式锁
        - 锁超时时间设置（默认 30 秒）
        - 锁重试机制（最多重试 3 次）
        - 防止死锁（自动过期）
        - 锁持有者标识
        - 分布式锁监控指标

- [ ] 1.14 实现熔断器服务
     【目标对象】`app/domain/highavailability/circuit_breaker_service.py`
     【修改目的】实现熔断模式
     【修改方式】状态机模式
     【相关依赖】ServiceHealthRepository, HAEventRepository
     【修改内容】
        - 熔断状态管理（CLOSED、OPEN、HALF_OPEN）
        - 错误率计算（1 分钟滑动窗口）
        - 熔断触发判断（错误率>50% 或连续失败>10 次）
        - 半开状态探测（放行 3 个请求）
        - 自动恢复逻辑
        - 熔断配置可配置化
        - 熔断事件记录

- [ ] 1.15 实现健康检查并发控制
     【目标对象】`app/domain/highavailability/health_check_scheduler.py`
     【修改目的】控制健康检查的并发度
     【修改方式】信号量 + 协程池
     【相关依赖】asyncio, ServiceHealthRepository
     【修改内容】
        - 最大并发探测数限制（默认 100）
        - 探测超时处理（HTTP Probe 5s，推理探针 10s）
        - 失败重试策略（最多 2 次，间隔 3s）
        - 探测任务优先级队列
        - 紧急停止机制（遇到大规模故障时暂停）

- [ ] 1.16 实现 Prometheus 监控指标
     【目标对象】`app/infrastructure/metrics/ha_metrics.py`
     【修改目的】暴露高可用监控指标
     【修改方式】prometheus_client
     【相关依赖】prometheus_client, ServiceHealthRepository
     【修改内容】
        - 实例健康状态指标（gauge）
        - 故障切换次数（counter）
        - 健康检查耗时（histogram）
        - 熔断状态指标（gauge）
        - 降级触发次数（counter）
        - 请求路由延迟（histogram）
        - 告警发送次数（counter）
        - Prometheus 规则模板（告警规则）

- [ ] 1.17 实现配置热加载
     【目标对象】`app/infrastructure/config/ha_config_loader.py`
     【修改目的】支持不重启更新高可用配置
     【修改方式】文件监听 + 配置中心
     【相关依赖】watchdog, etcd/nacos client
     【修改内容】
        - 监听配置文件变更（YAML/JSON）
        - 集成配置中心（etcd/Nacos）
        - 配置变更验证（语法检查）
        - 配置回滚机制（失败时恢复旧配置）
        - 配置变更通知（事件驱动）

- [ ] 1.11 实现健康状态缓存
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升健康状态查询性能
     【修改方式】使用 Redis 进行缓存
     【相关依赖】Redis, ServiceHealthRepository
     【修改内容】
        - 缓存服务健康状态
        - 缓存过期配置
        - 状态变更时更新缓存
        - 实现缓存预热

- [ ] 1.12 实现告警服务
     【目标对象】`app/infrastructure/alert/`
     【修改目的】在故障发生时发送告警
     【修改方式】实现告警服务
     【相关依赖】HAEventRepository, AlertRuleRepository
     【修改内容】
        - 定义告警渠道（邮件、短信、Webhook、Slack、钉钉、企业微信）
        - 发送故障告警（支持 P0-P3 级别）
        - 发送恢复告警
        - 告警去重（相同告警 5 分钟内合并）
        - 告警风暴抑制（1 小时最多 10 条）
        - 告警规则模板（Prometheus 规则格式）
        - 告警历史记录和统计

- [ ] 1.18 编写单元测试
     【目标对象】`tests/test_high_availability_service.py`
     【修改目的】确保高可用功能正确
     【修改方式】使用 pytest + pytest-asyncio
     【相关依赖】HighAvailabilityDomainService
     【修改内容】
        - 测试服务健康检查（HTTP Probe、推理探针）
        - 测试故障检测（模拟超时、错误响应）
        - 测试故障转移（主备切换逻辑）
        - 测试服务恢复（自动恢复、手动恢复）
        - 测试健康状态更新（状态变更事件）
        - 测试事件记录（事件完整性）
        - 测试熔断器（状态转换、半开探测）
        - 测试权重动态调整
        - 测试分布式锁（并发安全）

- [ ] 1.19 编写集成测试
     【目标对象】`tests/integration/test_ha_gateway.py`
     【修改目的】确保高可用网关端到端正常工作
     【修改方式】使用 pytest 和 httpx
     【相关依赖】HighAvailabilityGateway
     【修改内容】
        - 测试请求路由（轮询、随机、响应时间策略）
        - 测试故障切换（模拟实例宕机）
        - 测试重试机制（指数退避）
        - 测试健康检查定时任务（真实 HTTP 探测）
        - 测试手动故障转移（管理员 API）
        - 测试高可用事件日志（事件完整性）
        - 测试熔断器（错误注入触发熔断）
        - 测试降级链（主模型失败自动降级）
        - **故障注入测试**：
          - 模拟网络延迟（使用 toxiproxy 或 mock）
          - 模拟实例随机失败（chaos engineering）
          - 模拟大规模故障（雪崩场景）
          - 模拟 Redis 故障（分布式锁失效）
          - 模拟消息队列故障（事件丢失）
