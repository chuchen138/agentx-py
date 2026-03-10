## 实施
- [ ] 1.1 定义账户实体和数据模型
     【目标对象】`app/domain/account/`
     【修改目的】定义账户相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/user/model/*.java`
     【修改内容】
        - 创建 Account 模型（accounts 表）
        - 创建 UsageRecord 模型（usage_records 表）
        - 定义字段和关系（用户关联）
        - 实现 Pydantic Schema

- [ ] 1.2 实现账户仓储模式
     【目标对象】`app/domain/account/repository.py`
     【修改目的】定义账户数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AccountRepository 接口
        - 实现 SQLAlchemy AccountRepository
        - 实现 CRUD 操作
        - 实现按用户ID查询

- [ ] 1.3 实现账户领域服务
     【目标对象】`app/domain/account/service.py`
     【修改目的】封装账户相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】AccountRepository
     【修改内容】
        - 创建账户时初始化余额
        - 余额充值逻辑
        - 信用额度管理
        - 余额扣费逻辑
        - 可用余额计算（余额 + 信用额度 - 冻结金额）
        - 余额充足性检查

- [ ] 1.4 实现计费规则领域服务
     【目标对象】`app/domain/billing/service.py`
     【修改目的】封装计费规则逻辑
     【修改方式】实现领域服务层
     【相关依赖】AccountRepository, UsageRecordRepository
     【修改内容】
        - 计费策略接口定义
        - 按量计费策略
        - 包月计费策略
        - 分档计费策略
        - 最低计费金额控制（0.01元）
        - 用量记录保存

- [ ] 1.5 实现应用服务层 - 账户管理
     【目标对象】`app/application/account/`
     【修改目的】编排账户相关的用例
     【修改方式】实现应用服务
     【相关依赖】AccountDomainService
     【修改内容】
        - 实现 AccountAppService（账户管理）
        - getUserAccount - 获取用户账户
        - getAccountById - 根据ID获取账户
        - recharge - 账户充值
        - addCredit - 增加信用额度
        - checkSufficientBalance - 检查余额是否充足
        - getAvailableBalance - 获取可用余额
        - existsAccount - 检查账户是否存在

- [ ] 1.6 实现应用服务层 - 计费服务
     【目标对象】`app/application/billing/`
     【修改目的】编排计费相关的用例
     【修改方式】实现应用服务
     【相关依赖】BillingDomainService
     【修改内容】
        - 实现 BillingService（计费服务）
        - charge - 执行计费
        - 验证计费上下文
        - 查找商品配置
        - 检查幂等性（通过 request_id）
        - 计算费用
        - 扣费并记录用量

- [ ] 1.7 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/account/`
     【修改目的】暴露账户相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AccountAppService, BillingService
     【修改内容】
        - `GET /api/v1/accounts/me` - 获取当前用户账户
        - `GET /api/v1/accounts/{id}` - 根据ID获取账户
        - `POST /api/v1/accounts/recharge` - 账户充值
        - `POST /api/v1/accounts/credit` - 增加信用额度
        - `GET /api/v1/accounts/balance` - 获取可用余额
        - `POST /api/v1/billing/charge` - 执行计费

- [ ] 1.8 实现充值事件监听器
     【目标对象】`app/application/account/listener.py`
     【修改目的】监听充值成功事件并处理后续逻辑
     【修改方式】实现事件监听器
     【相关依赖】AccountDomainService
     【修改内容】
        - 监听充值成功事件
        - 处理充值后的业务逻辑
        - 触发余额更新通知

- [ ] 1.9 实现金额验证中间件
     【目标对象】`app/api/middleware/`
     【修改目的】确保所有金额参数的有效性
     【修改方式】实现 FastAPI 中间件
     【相关依赖】Pydantic, Decimal
     【修改内容】
        - 金额必须大于0
        - 金额精度控制（最多2位小数）
        - 防止金额溢出

- [ ] 1.10 编写单元测试
     【目标对象】`tests/test_account_service.py`
     【修改目的】确保账户管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】AccountAppService, BillingService
     【修改内容】
        - 测试账户创建
        - 测试账户充值
        - 测试信用额度管理
        - 测试余额扣费
        - 测试余额充足性检查
        - 测试计费功能
        - 测试按量计费策略
        - 测试包月计费策略
        - 测试最低计费金额（0.01元）

- [ ] 1.11 编写集成测试
     【目标对象】`tests/integration/test_account_api.py`
     【修改目的】确保账户 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AccountAppService, BillingService
     【修改内容】
        - 测试获取账户端点
        - 测试充值端点
        - 测试信用额度端点
        - 测试计费端点
        - 测试余额检查端点
        - 测试金额验证中间件
        - 测试并发充值场景
