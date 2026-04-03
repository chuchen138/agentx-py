# 账户计费能力技术设计

## 概述

账户计费能力基于领域驱动设计（DDD）架构实现，采用分层设计模式，将账户管理、订单处理、支付集成和计费逻辑清晰分离，构建灵活、可扩展的计费系统。

## 技术架构

### 架构分层

系统采用四层架构：**接口层**（API Routes）处理 HTTP 请求和参数校验；**应用层**（Application Services）协调业务流程，包含账户、订单、支付、商品和计费服务；**领域层**（Domain Services）封装核心业务逻辑，管理账户、订单、商品实体和领域事件；**基础设施层**（Infrastructure）对接支付平台、数据库和消息队列。

### 核心组件

**账户应用服务（AccountAppService）**
负责账户信息管理、充值发起、信用额度调整和余额充足性检查。所有余额变动操作记录审计日志。

**计费服务（BillingService）**
作为核心编排服务，执行以下流程：
1. 验证计费上下文完整性和有效性
2. 查找对应的商品规则和计费策略
3. 执行幂等性检查（通过 request_id 查询 usage_records 表）
4. Redis 分布式锁防止并发超扣（lock:billing:{user_id}）
5. 根据用量数据和价格配置计算费用
6. 实现最低计费额保障（round to 0.01 元）
7. 检查余额是否充足（读 Redis 缓存）
8. 通过 PostgreSQL 事务执行扣费并记录消费
9. 更新 Redis 余额缓存

**订单应用服务（OrderAppService）**
管理订单生命周期，包括创建、查询、状态流转（PENDING → PAID/CANCELLED/REFUNDED/EXPIRED）。

**支付应用服务（PaymentAppService）**
处理支付流程，包括创建支付订单、处理支付回调、验证签名、更新订单状态、发布支付成功事件。

**商品应用服务（ProductAppService）**
管理商品和计费规则的 CRUD 操作。

**充值事件监听器（RechargeEventListener）**
通过 Celery 异步任务监听支付成功事件，自动增加账户余额，支持失败重试。

## 计费流程

### 计费触发流程

计费流程是系统的核心，负责根据用户资源使用情况自动扣费。业务模块调用计费服务后，首先验证计费上下文的完整性和有效性，然后查找对应的商品规则。如果没有配置计费规则则直接放行。执行幂等性检查防止重复扣费，获取计费规则和对应策略，根据用量数据和价格配置计算费用，实现最低计费额保障（0.01 元）。最后检查余额是否充足，通过事务执行扣费并记录消费。

### 并发控制机制

**防止超卖设计**
1. **Redis 分布式锁**：扣费前获取锁，超时自动释放
   ```python
   async with redis_lock(f"lock:billing:{user_id}", timeout=5):
       # 执行扣费逻辑
   ```
2. **数据库乐观锁**：account 表增加 version 字段
   ```sql
   UPDATE accounts 
   SET balance = balance - :amount, version = version + 1
   WHERE id = :id AND version = :old_version
   ```
3. **唯一索引防重**：usage_records.request_id 设置唯一索引

### 计费上下文

计费上下文封装计费所需的所有信息，包括规则类型（如 MODEL_USAGE、AGENT_CREATION）、服务 ID、用量数据（如输入输出 Token 数量）、请求 ID（用于幂等性控制）和用户 ID。

### 计费策略

系统采用策略模式实现灵活的计费策略，支持不同的计费逻辑。Token 计费策略按输入输出 Token 数量计费，按次计费策略按使用次数计费，按时长计费策略按时间长度计费，存储计费策略按存储容量和时长计费。计费策略工厂根据规则处理器标识动态选择对应的策略。

## 事件驱动与异步处理

### 购买成功事件

支付成功后发布 `PurchaseSuccessEvent`，包含订单 ID、用户 ID、订单号、订单类型、订单金额、完整订单实体等信息。

### Celery 异步任务

**充值处理流程**
```python
@celery.task(bind=True, max_retries=5)
def process_recharge(self, order_id: str):
    try:
        # 1. 查询订单
        order = await order_repo.get(order_id)
        
        # 2. 增加账户余额
        await account_domain.recharge(order.user_id, order.amount)
        
        # 3. 发送余额变动通知
        await notification_service.send_balance_update(...)
        
    except Exception as exc:
        # 指数退避重试
        raise self.retry(exc, countdown=2 ** self.request.retries)
```

**优势**
- 支付回调快速响应（< 200ms）
- 充值逻辑与支付解耦
- 失败自动重试，不影响支付记录
- 可独立监控和告警

### 支付平台集成

### 支付平台抽象

定义 `PaymentProvider` 接口，支持支付宝、微信支付、Stripe。每个支付平台实现：
- `create_payment()`: 创建支付
- `query_payment()`: 查询支付状态
- `verify_callback()`: 验证回调签名
- `is_available()`: 检查平台可用性

### 支付回调安全

**签名验证**
```python
def verify_alipay_signature(data: dict, signature: str) -> bool:
    # 使用支付宝公钥验证 RSA 签名
    public_key = load_alipay_public_key()
    message = build_sign_message(data)
    return public_key.verify(message, signature)
```

**防重放攻击**
```python
async def verify_nonce(nonce: str, timestamp: int) -> bool:
    # 检查时间窗口（±5 分钟）
    if abs(time.time() - timestamp) > 300:
        return False
    
    # 检查 nonce 唯一性
    exists = await redis.exists(f"payment:nonce:{nonce}")
    if exists:
        return False
    
    # 记录 nonce（TTL 10 分钟）
    await redis.setex(f"payment:nonce:{nonce}", 600, 1)
    return True
```

### 支付流程

支付流程包括用户发起充值请求创建充值订单、选择支付平台和支付类型、调用支付平台创建支付、返回支付链接或二维码、用户扫码或在页面完成支付、支付平台回调通知、验证回调签名并查询订单状态、更新订单状态为已支付、发布购买成功事件、事件监听器处理余额充值。

## 数据模型

### 核心实体

**Account（账户）**
```python
class Account(Base):
    __tablename__ = "accounts"
    
    id: UUID = Column(UUID, primary_key=True)
    user_id: UUID = Column(UUID, unique=True, nullable=False)
    balance: Decimal = Column(Numeric(10, 2), default=0)
    credit: Decimal = Column(Numeric(10, 2), default=0)
    total_consumed: Decimal = Column(Numeric(10, 2), default=0)
    version: int = Column(Integer, default=0)  # 乐观锁
    created_at: datetime = Column(DateTime)
    updated_at: datetime = Column(DateTime)
```

**Order（订单）**
```python
class Order(Base):
    __tablename__ = "orders"
    
    id: UUID = Column(UUID, primary_key=True)
    user_id: UUID = Column(UUID, nullable=False)
    order_no: str = Column(String(64), unique=True, nullable=False)
    type: OrderType = Column(Enum(OrderType))
    title: str = Column(String(255))
    description: str = Column(Text)
    amount: Decimal = Column(Numeric(10, 2))
    currency: str = Column(String(3), default="CNY")
    status: OrderStatus = Column(Enum(OrderStatus))
    paid_at: Optional[datetime] = Column(DateTime)
    refunded_at: Optional[datetime] = Column(DateTime)
    refund_amount: Optional[Decimal] = Column(Numeric(10, 2))
    payment_platform: PaymentPlatform = Column(Enum(PaymentPlatform))
    payment_type: PaymentType = Column(Enum(PaymentType))
    transaction_id: Optional[str] = Column(String(128))  # 第三方订单号
    metadata: dict = Column(JSONB)
    created_at: datetime = Column(DateTime)
    updated_at: datetime = Column(DateTime)
    
    # 索引
    __table_args__ = (
        Index("idx_user_status", "user_id", "status"),
    )
```

**UsageRecord（消费记录）**
```python
class UsageRecord(Base):
    __tablename__ = "usage_records"
    
    id: UUID = Column(UUID, primary_key=True)
    user_id: UUID = Column(UUID, nullable=False)
    product_id: UUID = Column(UUID, nullable=False)
    order_id: Optional[UUID] = Column(UUID)
    request_id: str = Column(String(128), unique=True, nullable=False)  # 幂等性
    billing_type: BillingType = Column(Enum(BillingType))
    service_id: str = Column(String(255))  # model_id / agent_id
    usage_data: dict = Column(JSONB)  # {input_tokens, output_tokens, ...}
    amount: Decimal = Column(Numeric(10, 2))
    created_at: datetime = Column(DateTime)
    
    # 索引
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
    )
```

## 接口定义

### 账户相关接口

| 路径 | 方法 | 功能 | 请求体 (JSON) | 成功响应 (200 OK) |
|------|------|------|--------------|------------------|
| `/api/accounts/me` | GET | 获取当前用户账户 | N/A | `{"id": 1, "user_id": 123, "balance": "100.00", "credit": "50.00", "total_consumed": "0.00", "version": 0, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}` |
| `/api/accounts/{id}` | GET | 根据ID获取账户 | N/A | `{"id": 1, "user_id": 123, "balance": "100.00", "credit": "50.00", "total_consumed": "0.00", "version": 0, "created_at": "2024-01-01T00:00:00", "updated_at": "2024-01-01T00:00:00"}` |
| `/api/accounts/recharge` | POST | 发起充值 | `{"amount": "100.00", "payment_platform": "alipay", "payment_type": "scan"}` | `{"order_id": 1, "order_no": "RECHARGE_TEST", "amount": "100.00", "status": "pending", "payment_platform": "alipay"}` |
| `/api/accounts/credit` | POST | 增加信用额度（管理员） | `{"amount": "50.00", "reason": "测试信用额度"}` | `{"user_id": 123, "credit_added": "50.00", "new_credit": "100.00", "reason": "测试信用额度"}` |
| `/api/accounts/balance` | GET | 获取可用余额 | N/A | `{"balance": "100.00", "credit": "50.00", "total_consumed": "0.00", "available_balance": "150.00"}` |

### 计费相关接口

| 路径 | 方法 | 功能 | 请求体 (JSON) | 成功响应 (200 OK) |
|------|------|------|--------------|------------------|
| `/api/billing/charge` | POST | 执行计费（内部调用） | `{"user_id": 123, "product_id": 1, "service_id": "llm", "usage_data": {"token_count": 1000}, "request_id": "test-request-id"}` | `{"success": true, "amount": "1.00", "usage_record_id": 1, "message": "Billing successful"}` |
| `/api/billing/usage-records` | GET | 获取用量记录 | N/A | `[{"id": 1, "user_id": 123, "product_id": 1, "request_id": "test-request-1", "billing_type": "token", "service_id": "llm", "usage_data": {"token_count": 1000}, "amount": "1.00", "created_at": "2024-01-01T00:00:00"}]` |

### 订单相关接口

| 路径 | 方法 | 功能 | 请求体 (JSON) | 成功响应 (200 OK) |
|------|------|------|--------------|------------------|
| `/api/orders` | GET | 查询订单列表 | N/A | `[{"id": 1, "user_id": 123, "order_no": "RECHARGE_TEST", "type": "recharge", "title": "账户充值", "amount": "100.00", "status": "pending", "created_at": "2024-01-01T00:00:00"}]` |
| `/api/orders/{id}` | GET | 获取订单详情 | N/A | `{"id": 1, "user_id": 123, "order_no": "RECHARGE_TEST", "type": "recharge", "title": "账户充值", "amount": "100.00", "status": "pending", "created_at": "2024-01-01T00:00:00"}` |

## 设计亮点

### 领域驱动设计

系统遵循领域驱动设计原则，划分账户领域（账户余额、信用额度管理）、订单领域（订单生命周期管理）、支付领域（支付平台集成）和商品领域（商品和计费规则管理）清晰的领域边界，提供丰富的领域模型（AccountEntity、OrderEntity、ProductEntity、PurchaseSuccessEvent）和领域服务（AccountDomainService、OrderDomainService、ProductDomainService）封装核心业务逻辑。

### 策略模式应用

系统采用灵活的计费策略扩展，通过策略接口定义统一策略，具体策略包括 TokenBillingStrategy、PerUnitBillingStrategy 等，新增计费类型只需实现新策略。工厂模式管理所有策略，根据处理器键动态选择策略，支持策略热插拔。商品的价格配置使用 JSON 格式灵活配置各种价格参数，无需修改代码即可调整价格。

## 设计亮点

### 领域驱动设计

系统遵循领域驱动设计原则，划分账户领域（账户余额、信用额度管理）、订单领域（订单生命周期管理）、支付领域（支付平台集成）和商品领域（商品和计费规则管理）清晰的领域边界，提供丰富的领域模型（AccountEntity、OrderEntity、ProductEntity、PurchaseSuccessEvent）和领域服务（AccountDomainService、OrderDomainService、ProductDomainService）封装核心业务逻辑。

### 策略模式应用

# ... existing code ...

### 事件驱动与异步处理

购买成功事件和异步监听器实现充值成功异步处理，不阻塞支付回调流程。事件驱动架构实现业务解耦提升可维护性，支付成功与权益授予分离，各业务模块独立处理订单事件，降低模块间耦合。使用 Celery 异步任务队列，支持失败重试和监控告警。

### 幂等性与并发控制

**三级防护机制**
1. **应用层**：请求级幂等（request_id），Redis 分布式锁
2. **数据库层**：唯一索引约束（request_id），乐观锁（version）
3. **业务层**：事务隔离（READ COMMITTED），行级锁（SELECT FOR UPDATE）

**扣费流程伪代码**
```python
async def charge(self, ctx: BillingContext) -> ChargeResult:
    # 1. 幂等性检查
    existing = await self.repo.get_by_request_id(ctx.request_id)
    if existing:
        return ChargeResult(success=True, already_charged=True)
    
    # 2. 获取分布式锁
    async with redis_lock(f"lock:billing:{ctx.user_id}", timeout=5):
        # 3. 再次检查（双重检查锁）
        existing = await self.repo.get_by_request_id(ctx.request_id)
        if existing:
            return ChargeResult(success=True, already_charged=True)
        
        # 4. 计算费用
        amount = await self.calculate_fee(ctx)
        
        # 5. 检查余额（读缓存）
        balance = await self.account_service.get_balance(ctx.user_id)
        if balance < amount:
            raise InsufficientBalanceError()
        
        # 6. 执行扣费（事务 + 乐观锁）
        async with db.begin():
            success = await self.account_repo.deduct_with_version(
                ctx.user_id, amount
            )
            if not success:
                raise ConcurrentModificationError()
            
            # 7. 记录消费
            record = UsageRecord(
                user_id=ctx.user_id,
                request_id=ctx.request_id,
                amount=amount,
                ...
            )
            db.add(record)
        
        # 8. 更新缓存
        await self.cache.set(f"account:{ctx.user_id}:balance", balance - amount)
        
        return ChargeResult(success=True, amount=amount)
```

## 技术栈

**后端框架**
- Python 3.10+
- FastAPI 0.100+（异步 Web 框架）
- SQLAlchemy 2.0+（异步 ORM）
- Pydantic 2.0+（数据验证）

**数据存储**
- PostgreSQL 14+（主数据库）
- Redis 7.0+（缓存 + 分布式锁 + 消息队列）

**消息队列**
- Celery 5.3+（异步任务）
- Celery Beat（定时任务）

**支付集成**
- alipay-sdk-python（支付宝）
- wechatpy（微信支付）
- stripe（国际支付）

**安全与监控**
- python-jose（JWT 签名验证）
- cryptography（数据加密）
- prometheus-client（指标监控）
- structlog（结构化日志）

## 未来优化方向

**短期（1-3 个月）**
- [ ] 完善退款流程和对账任务
- [ ] 实现订阅自动续费和降级策略
- [ ] 接入电子发票系统
- [ ] 增加余额变动实时通知（WebSocket）

**中期（3-6 个月）**
- [ ] 支持多币种和汇率转换
- [ ] 引入分布式事务（Saga 模式）处理跨服务计费
- [ ] 分润与结算功能（代理商/渠道商）
- [ ] 风控规则引擎（异常消费检测）

**长期（6-12 个月）**
- [ ] 机器学习预测用户欠费风险
- [ ] 动态定价策略（基于供需关系）
- [ ] 区块链存证（交易不可篡改）
- [ ] 全球化税务合规（VAT/GST 自动计算）
