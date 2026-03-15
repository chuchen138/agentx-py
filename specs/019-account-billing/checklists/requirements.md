## 实施
- [ ] 1.1 定义账户实体和数据模型
     【目标对象】`app/domain/account/`
     【修改目的】定义账户相关的领域模型
     【修改方式】使用 SQLAlchemy 2.0 异步模式定义 ORM 模型
     【相关依赖】SQLAlchemy 2.0+, Pydantic 2.0+
     【修改内容】
        - 创建 Account 模型（accounts 表）
          - 字段：id, user_id, balance (DECIMAL(10,2)), credit (DECIMAL(10,2)), 
            total_consumed (DECIMAL(10,2)), version (乐观锁), created_at, updated_at
          - 索引：user_id 唯一索引，created_at 普通索引
        - 创建 UsageRecord 模型（usage_records 表）
          - 字段：id, user_id, product_id, order_id, request_id (唯一索引), 
            billing_type, service_id, usage_data (JSONB), amount, created_at
          - 索引：request_id 唯一索引，user_id + created_at 组合索引
        - 创建 Order 模型（orders 表）
          - 字段：id, user_id, order_no (唯一), type, title, description, 
            amount, currency, status, paid_at, cancelled_at, refunded_at, 
            expired_at, refund_amount, payment_platform, payment_type, 
            transaction_id (第三方), metadata (JSONB), created_at, updated_at
          - 索引：order_no 唯一索引，user_id + status 组合索引
        - 创建 Product 模型（products 表）
          - 字段：id, name, billing_type, service_id, rule_id, 
            price_config (JSONB), status, created_at, updated_at
        - 实现 Pydantic Schema（AccountCreate, AccountResponse, OrderResponse 等）

- [ ] 1.2 实现账户仓储模式
     【目标对象】`app/domain/account/repository.py`
     【修改目的】定义账户数据访问接口
     【修改方式】实现 Repository 模式 + 异步会话
     【相关依赖】SQLAlchemy 2.0 async
     【修改内容】
        - 定义 AccountRepository 接口
        - 实现 AsyncAccountRepository
        - CRUD 操作：create, get_by_id, get_by_user_id, update, delete
        - 余额更新方法（带乐观锁）：update_balance_with_version(account_id, new_balance, old_version)
        - 按用户 ID 查询优化：使用 joinedload 预加载关联数据

- [ ] 1.3 实现账户领域服务
     【目标对象】`app/domain/account/service.py`
     【修改目的】封装账户相关的业务逻辑
     【修改方式】实现领域服务层 + Redis 缓存
     【相关依赖】AccountRepository, Redis
     【修改内容】
        - 创建账户时初始化余额（balance=0, credit=0）
        - 余额充值逻辑（事务 + 审计日志）
        - 信用额度管理（增加/减少额度，记录操作日志）
        - 余额扣费逻辑（先检查后扣费，防止超扣）
        - 可用余额计算：available = balance + credit - frozen_amount
        - 余额充足性检查（读取 Redis 缓存，未命中查库）
        - Redis 缓存策略：
          - key: account:{user_id}:balance
          - TTL: 5 分钟
          - 更新时失效缓存

- [ ] 1.4 实现计费规则领域服务
     【目标对象】`app/domain/billing/service.py`
     【修改目的】封装计费规则逻辑
     【修改方式】实现领域服务层 + 策略模式
     【相关依赖】ProductRepository, UsageRecordRepository, Redis
     【修改内容】
        - 计费策略接口定义（BillingStrategy）
        - 按量计费策略（TokenUsageStrategy, StorageUsageStrategy）
        - 包月计费策略（SubscriptionStrategy）
        - 分档计费策略（TieredPricingStrategy）
        - 最低计费金额控制（round to 0.01）
        - 用量记录保存（异步写入，降低延迟）
        - 幂等性检查：通过 request_id 查询 usage_records 表

- [ ] 1.5 实现应用服务层 - 账户管理
     【目标对象】`app/application/account/service.py`
     【修改目的】编排账户相关的用例
     【修改方式】实现应用服务 + Celery 异步任务
     【相关依赖】AccountDomainService, Celery
     【修改内容】
        - 实现 AccountAppService
        - getUserAccount - 获取用户账户（读缓存）
        - getAccountById - 根据 ID 获取账户
        - recharge - 账户充值（异步任务，发送事件）
        - addCredit - 增加信用额度（需管理员权限）
        - checkSufficientBalance - 检查余额是否充足
        - getAvailableBalance - 获取可用余额
        - existsAccount - 检查账户是否存在
        - 大额充值验证（> 1000 元触发二次确认）

- [ ] 1.6 实现应用服务层 - 计费服务
     【目标对象】`app/application/billing/service.py`
     【修改目的】编排计费相关的用例
     【修改方式】实现应用服务 + 分布式锁
     【相关依赖】BillingDomainService, Redis, AccountDomainService
     【修改内容】
        - 实现 BillingService
        - charge - 执行计费（核心方法）
        - 验证计费上下文完整性
        - 查找商品配置
        - 检查幂等性（通过 request_id）
        - 计算费用（调用对应策略）
        - Redis 分布式锁防止并发超扣：
          - key: lock:billing:{user_id}
          - timeout: 5 秒
          - 重试机制：最多重试 3 次
        - 扣费并记录用量（同一事务）
        - 更新 Redis 余额缓存

- [ ] 1.7 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/account/`, `app/api/v1/billing/`
     【修改目的】暴露账户和计费相关的 HTTP API
     【修改方式】使用 FastAPI 异步路由
     【相关依赖】AccountAppService, BillingService
     【修改内容】
        - `GET /api/v1/accounts/me` - 获取当前用户账户
        - `GET /api/v1/accounts/{id}` - 根据 ID 获取账户
        - `POST /api/v1/accounts/recharge` - 发起充值
        - `POST /api/v1/accounts/credit` - 增加信用额度（管理员）
        - `GET /api/v1/accounts/balance` - 获取可用余额
        - `POST /api/v1/billing/charge` - 执行计费（内部调用）
        - `GET /api/v1/orders` - 查询订单列表
        - `GET /api/v1/orders/{id}` - 获取订单详情
        - `POST /api/v1/refunds` - 申请退款

- [ ] 1.8 实现充值事件监听器
     【目标对象】`app/application/account/listener.py`
     【修改目的】监听充值成功事件并异步处理后续逻辑
     【修改方式】使用 Celery 任务队列
     【相关依赖】AccountDomainService, Celery
     【修改内容】
        - 监听充值成功事件（通过消息队列）
        - 异步处理充值后的业务逻辑（增加余额）
        - 触发余额更新通知（WebSocket 推送）
        - 失败重试机制（指数退避，最多 5 次）

- [ ] 1.9 实现金额验证中间件
     【目标对象】`app/api/middleware/amount_validation.py`
     【修改目的】确保所有金额参数的有效性
     【修改方式】实现 FastAPI 中间件 + Pydantic 验证器
     【相关依赖】Pydantic 2.0+, Decimal
     【修改内容】
        - 金额必须大于 0
        - 金额精度控制（最多 2 位小数）
        - 防止金额溢出（max < 10^8）
        - 自定义 Pydantic 类型：PositiveDecimal

- [ ] 1.10 实现支付回调安全验证
     【目标对象】`app/api/v1/payment/callback.py`
     【修改目的】确保支付回调的真实性和安全性
     【修改方式】签名验证 + 防重放攻击
     【相关依赖】hashlib, time, Redis
     【修改内容】
        - 验证支付平台签名（RSA/MD5）
        - 检查时间戳（允许前后 5 分钟偏差）
        - 检查 nonce 唯一性（Redis 记录，TTL 10 分钟）
        - 验证订单金额一致性
        - 返回 success/failure 响应

- [ ] 1.11 编写单元测试
     【目标对象】`tests/unit/test_account_service.py`, `tests/unit/test_billing_service.py`
     【修改目的】确保账户管理和计费功能正确性
     【修改方式】使用 pytest + pytest-asyncio
     【相关依赖】pytest, pytest-asyncio, asgi-lifespan
     【修改内容】
        - 测试账户创建和初始化
        - 测试账户充值（正常/大额/并发）
        - 测试信用额度管理
        - 测试余额扣费（充足/不足/并发）
        - 测试余额充足性检查
        - 测试计费功能（Token/按次/包月）
        - 测试最低计费金额（0.01 元）
        - 测试幂等性（重复 request_id）
        - 测试负余额模拟攻击
        - 测试支付回调签名验证
        - 测试支付回调失败重试

- [ ] 1.12 编写集成测试
     【目标对象】`tests/integration/test_billing_flow.py`
     【修改目的】确保计费流程端到端正常工作
     【修改方式】使用 FastAPI TestClient + Docker Compose
     【相关依赖】FastAPI, TestClient, PostgreSQL, Redis
     【修改内容】
        - 测试完整充值流程（创建订单 -> 支付 -> 回调 -> 到账）
        - 测试完整扣费流程（LLM 调用 -> 计费 -> 扣费 -> 记录）
        - 测试并发充值场景（100 个并发请求）
        - 测试并发扣费场景（防止超卖）
        - 测试退款流程
        - 测试金额验证中间件
        - 测试支付回调防重放攻击
        - 测试 Redis 缓存失效策略
        - 测试 Celery 异步任务执行

- [ ] 1.13 实现定时对账任务
     【目标对象】`app/tasks/reconciliation.py`
     【修改目的】每日自动对账，发现并处理差异
     【修改方式】使用 Celery Beat 定时任务
     【相关依赖】Celery Beat, Pandas（数据分析）
     【修改内容】
        - 每日凌晨 2:00 执行 T+1 对账
        - 对比支付平台订单 vs 系统订单
        - 对比消费记录 vs 账户余额变动
        - 生成差异报告（邮件发送给财务）
        - 小额差异自动平账
        - 大额差异触发告警（钉钉/企业微信）
