# 规则引擎技术设计

## 概述

规则引擎模块采用分层架构设计，遵循领域驱动设计（DDD）原则，提供灵活的规则定义、配置和执行能力。使用 Python + FastAPI + SQLAlchemy 技术栈，集成 Redis 缓存和 Prometheus 监控。

## 技术架构

### 架构分层

```
┌─────────────────────────────────────────┐
│         接口层 (Interfaces)             │
│  - REST API (FastAPI)                   │
│  - GraphQL (可选)                        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│        应用层 (Application)             │
│  - RuleAppService                       │
│  - DTOs, Assemblers                     │
│  - Use Cases                            │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│         领域层 (Domain)                 │
│  - Entities: RuleEntity                 │
│  - Value Objects: RuleContext, Result   │
│  - Services: RuleDomainService          │
│  - Handlers: IRuleHandler               │
│  - Factory: RuleHandlerFactory          │
│  - Engine: RuleEngine                   │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│      基础设施层 (Infrastructure)        │
│  - Repositories: RuleRepository         │
│  - Cache: Redis + Local LRU             │
│  - Monitoring: Prometheus               │
│  - Database: MySQL (SQLAlchemy)         │
└─────────────────────────────────────────┘
```

### 核心组件

**RuleAppService**: 应用服务层，负责业务流程编排
- 创建/更新/删除规则
- 查询规则列表和详情
- 规则版本管理
- 规则启用/禁用

**RuleDomainService**: 领域服务层，负责核心业务逻辑
- 规则验证（含安全检查）
- 规则持久化
- 规则冲突解决
- 审计日志记录

**RuleHandlerFactory**: 策略工厂，负责处理器注册和查找
- 自动发现并注册处理器（装饰器模式）
- 根据 handlerKey 获取处理器实例
- 处理器生命周期管理

**RuleEngine**: 规则执行引擎
- 规则加载（带缓存）
- 规则执行（单个/批量）
- 超时控制
- 失败重试

## 核心设计

### 数据模型设计

#### RuleEntity（规则实体）

```python
from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, Index
from sqlalchemy.ext.declarative import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()

class RuleEntity(Base):
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    handler_key = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    config = Column(JSON, nullable=False, default=dict)
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0, comment="优先级，越高越优先")
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), comment="最后更新人邮箱")
    
    # 索引
    __table_args__ = (
        Index('idx_handler_key_version', 'handler_key', 'version'),
        Index('idx_enabled_priority', 'enabled', 'priority'),
    )
```

#### RuleVersionEntity（规则版本快照）

```python
class RuleVersionEntity(Base):
    __tablename__ = "rule_versions"
    
    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False, comment="规则完整快照")
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(String(500))
```

#### RuleAuditLogEntity（审计日志）

```python
class RuleAuditLogEntity(Base):
    __tablename__ = "rule_audit_logs"
    
    id = Column(String(36), primary_key=True)
    rule_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # CREATE/UPDATE/DELETE/EXECUTE
    old_value = Column(JSON, comment="修改前的值")
    new_value = Column(JSON, comment="修改后的值")
    operator = Column(String(100), nullable=False)
    operated_at = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45))
```

### 策略模式实现

#### 处理器注册机制

```python
# app/domain/rule/handler/__init__.py
from typing import Type, Dict
from abc import ABC, abstractmethod

class IRuleHandler(ABC):
    """规则处理器接口"""
    
    @abstractmethod
    def get_handler_key(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, context: RuleContext, rule_config: Dict) -> RuleResult:
        pass

# 装饰器定义
def rule_handler(handler_key: str):
    """规则处理器注册装饰器"""
    def decorator(cls: Type[IRuleHandler]) -> Type[IRuleHandler]:
        RuleHandlerFactory.register(cls())
        return cls
    return decorator

# 使用示例
@rule_handler("MODEL_USAGE_BILLING")
class ModelUsageBillingHandler(IRuleHandler):
    def get_handler_key(self) -> str:
        return "MODEL_USAGE_BILLING"
    
    async def execute(self, context: RuleContext, rule_config: Dict) -> RuleResult:
        # 实现计费逻辑
        pass
```

#### 处理器自动发现

```python
# app/domain/rule/handler/__init__.py
import importlib
import pkgutil

def auto_discover_handlers():
    """自动发现并注册所有规则处理器"""
    package = importlib.import_module("app.domain.rule.handler")
    for _, name, is_pkg in pkgutil.iter_modules(package.__path__, package.__name__ + "."):
        if is_pkg or name.endswith(".builtin"):
            importlib.import_module(name)

# 在应用启动时调用
# auto_discover_handlers()
```

### 缓存策略

#### 多级缓存设计

```python
# app/infrastructure/cache/rule_cache.py
import redis
from collections import OrderedDict
from typing import Optional
import json

class LRUCache:
    """本地 LRU 缓存"""
    def __init__(self, maxsize=100):
        self.cache = OrderedDict()
        self.maxsize = maxsize
    
    def get(self, key: str) -> Optional[RuleEntity]:
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key: str, value: RuleEntity):
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.maxsize:
                self.cache.popitem(last=False)
            self.cache[key] = value
    
    def pop(self, key: str):
        self.cache.pop(key, None)

class RuleCache:
    """规则多级缓存"""
    
    def __init__(self):
        self.local_cache = LRUCache(maxsize=100)
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
    
    async def get(self, handler_key: str) -> Optional[RuleEntity]:
        # 1. 尝试本地缓存
        if rule := self.local_cache.get(handler_key):
            metrics.cache_local_hit.inc()
            return rule
        
        # 2. 尝试 Redis 缓存
        cached = await self.redis_client.get(f"rule:{handler_key}")
        if cached:
            rule = RuleEntity(**json.loads(cached))
            self.local_cache.set(handler_key, rule)
            metrics.cache_redis_hit.inc()
            return rule
        
        # 3. 从数据库加载
        rule = await repository.get_by_handler_key(handler_key)
        if rule:
            # 写入两级缓存
            await self.redis_client.setex(
                f"rule:{handler_key}", 
                ttl=300,  # 5 分钟
                value=json.dumps(rule.dict())
            )
            self.local_cache.set(handler_key, rule)
            metrics.cache_miss.inc()
        
        return rule
    
    async def invalidate(self, handler_key: str):
        """缓存失效"""
        await self.redis_client.delete(f"rule:{handler_key}")
        self.local_cache.pop(handler_key, None)
        # 发布失效通知
        await self.redis_client.publish("rule:invalidated", handler_key)
```

#### 缓存预热

```python
async def warmup_cache():
    """启动时预热缓存"""
    all_enabled_rules = await repository.list(enabled=True)
    for rule in all_enabled_rules:
        await cache.set(rule.handler_key, rule)
```

### 安全设计

#### 规则内容校验

```python
# app/domain/rule/validator.py
import json
import ast
from typing import Dict

class RuleValidator:
    """规则验证器"""
    
    # 黑名单：禁止的 Python 关键字
    FORBIDDEN_KEYWORDS = [
        'eval', 'exec', 'compile', '__import__', 
        'globals', 'locals', 'getattr', 'setattr',
        'delattr', 'vars', 'dir', 'breakpoint'
    ]
    
    # 白名单：允许的 simpleeval 函数
    ALLOWED_FUNCTIONS = ['abs', 'round', 'min', 'max', 'sum', 'len']
    
    @staticmethod
    def validate_config(config: Dict) -> None:
        """验证规则配置安全性"""
        config_str = json.dumps(config)
        
        # 检查黑名单关键字
        for keyword in RuleValidator.FORBIDDEN_KEYWORDS:
            if keyword in config_str:
                raise RuleValidationError(
                    f"Forbidden keyword detected: {keyword}",
                    error_code="SECURITY_VIOLATION"
                )
        
        # 如果需要使用表达式，限制使用 simpleeval
        if "expression" in config:
            RuleValidator._validate_expression(config["expression"])
    
    @staticmethod
    def _validate_expression(expr: str) -> None:
        """验证表达式安全性"""
        from simpleeval import Expr, Name, Call
        
        try:
            expr_obj = Expr.parse(expr)
            # 遍历 AST，检查节点类型
            for node in ast.walk(expr_obj):
                if isinstance(node, ast.Call):
                    # 检查调用的函数是否在白名单中
                    if isinstance(node.func, ast.Name):
                        if node.func.id not in RuleValidator.ALLOWED_FUNCTIONS:
                            raise RuleValidationError(
                                f"Function not allowed: {node.func.id}"
                            )
        except Exception as e:
            raise RuleValidationError(f"Invalid expression: {str(e)}")
```

#### 沙箱执行

```python
# app/domain/rule/safe_executor.py
from simpleeval import SimpleEval
import ast

class SafeRuleExecutor:
    """安全规则执行器"""
    
    def __init__(self):
        self.s_eval = SimpleEval()
        self.s_eval.functions.update({
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
        })
        # 限制可用的操作符
        self.s_eval.operators.update({
            ast.Add: self.safe_add,
            ast.Sub: self.safe_sub,
            ast.Mult: self.safe_mult,
            ast.Div: self.safe_div,
        })
    
    def safe_add(self, a, b):
        # 防止溢出等安全检查
        return a + b
    
    def safe_sub(self, a, b):
        return a - b
    
    def safe_mult(self, a, b):
        return a * b
    
    def safe_div(self, a, b):
        if b == 0:
            raise RuleExecutionError("Division by zero", "DIVISION_BY_ZERO")
        return a / b
    
    def evaluate(self, expression: str, context: Dict) -> any:
        """安全地执行表达式"""
        self.s_eval.names = context
        try:
            return self.s_eval.eval(expression)
        except Exception as e:
            raise RuleExecutionError(
                f"Rule execution failed: {str(e)}",
                error_code="EXECUTION_ERROR"
            )
```

### 数据一致性

#### 乐观锁实现

```python
# app/domain/rule/repository.py
from sqlalchemy.ext.asyncio import AsyncSession

class RuleRepository:
    async def update(self, rule: RuleEntity, session: AsyncSession) -> RuleEntity:
        """更新规则（乐观锁）"""
        async with session.begin():
            # 检查版本号
            existing = await self.get(rule.id, session)
            if existing.version != rule.version:
                raise ConcurrencyError(
                    f"Rule version conflict: expected {rule.version}, "
                    f"but got {existing.version}"
                )
            
            # 递增版本号
            rule.version = existing.version + 1
            
            # 创建版本快照
            version_snapshot = RuleVersionEntity(
                rule_id=rule.id,
                version=rule.version,
                snapshot=rule.dict(),
                changed_by=rule.updated_by,
                change_reason="Update"
            )
            
            # 保存规则和版本快照
            session.add(rule)
            session.add(version_snapshot)
            
            return rule
```

#### 事务管理

```python
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

@asynccontextmanager
async def transactional(session: AsyncSession):
    """事务管理器"""
    async with session.begin() as tx:
        try:
            yield tx
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
```

## 性能优化

### 批量查询优化

```python
class RuleService:
    async def get_rules_batch(self, handler_keys: List[str]) -> Dict[str, RuleEntity]:
        """批量获取规则"""
        # 一次性查询所有规则，避免 N+1 问题
        rules = await repository.list_by_handler_keys(handler_keys)
        return {r.handler_key: r for r in rules}
```

### 异步执行

```python
import asyncio

class RuleEngine:
    async def execute_batch(
        self, 
        requests: List[Tuple[str, RuleContext]]
    ) -> List[RuleResult]:
        """批量异步执行规则"""
        tasks = [
            self.execute(handler_key, context)
            for handler_key, context in requests
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(RuleResult(
                    allowed=False,
                    reason=f"Execution error: {str(result)}",
                    data={"request_index": i}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
```

## 扩展性设计

### 新增规则类型的步骤

1. 定义新的 handlerKey（在 RuleHandlerKey 常量类中）
2. 创建处理器实现类，继承 `IRuleHandler`
3. 使用 `@rule_handler` 装饰器注册
4. 通过数据库 API 创建规则实例

### 规则版本演进

```python
class RuleEntity:
    # 支持版本字段
    version: int
    
    # 支持继承扩展
    class Config:
        extra = "allow"  # 允许额外字段
```

### 插件化架构（未来）

未来可支持外部插件形式的规则处理器：
- 从指定目录动态加载 `.py` 文件
- 通过 gRPC 调用外部规则引擎服务
- WebAssembly 沙箱执行自定义规则

## 监控与可观测性

### 指标收集

```python
# app/infrastructure/monitoring/rule_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# 规则执行次数
rule_execution_total = Counter(
    'rule_execution_total',
    'Total rule executions',
    ['handler_key', 'result']
)

# 规则执行延迟
rule_execution_latency = Histogram(
    'rule_execution_latency_seconds',
    'Rule execution latency',
    ['handler_key'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# 缓存命中率
cache_hit_ratio = Gauge(
    'rule_cache_hit_ratio',
    'Rule cache hit ratio',
    ['cache_layer']  # local, redis
)
```

### 分布式追踪

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

class RuleEngine:
    @tracer.start_as_current_span("rule_execute")
    async def execute(self, handler_key: str, context: RuleContext) -> RuleResult:
        span = trace.get_current_span()
        span.set_attribute("rule.handler_key", handler_key)
        span.set_attribute("rule.context.user_id", context.user_id)
        
        # ... 执行逻辑
```

## API接口设计

### 规则管理接口

| 接口路径 | 方法 | 功能描述 | 请求体 (JSON) | 响应体 (JSON) |
|---------|------|---------|--------------|--------------|
| `/api/v1/rules` | POST | 创建规则 | `{"name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "priority": 100}` | `{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "enabled": true, "priority": 100, "version": 1, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules/{ruleId}` | PUT | 更新规则 | `{"name": "更新后的规则", "description": "更新后的描述", "config": {...}, "priority": 200}` | `{"id": "rule-123", "name": "更新后的规则", "handlerKey": "model_usage_billing", "description": "更新后的描述", "config": {...}, "enabled": true, "priority": 200, "version": 2, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules` | GET | 查询规则列表 | N/A (查询参数: handlerKey, keyword, enabled, page, pageSize) | `{"records": [{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "enabled": true, "priority": 100, "version": 1}], "current": 1, "size": 15, "total": 1}` |
| `/api/v1/rules/{ruleId}` | GET | 获取规则详情 | N/A | `{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "enabled": true, "priority": 100, "version": 1, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules/by-handler-key/{handlerKey}` | GET | 根据处理器标识查询规则 | N/A | `{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "enabled": true, "priority": 100, "version": 1, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules/{ruleId}` | DELETE | 删除规则 | N/A | `{"message": "Rule deleted successfully"}` |
| `/api/v1/rules/{ruleId}/versions` | GET | 获取规则历史版本 | N/A | `{"versions": [{"version": 2, "snapshot": {...}, "changed_by": "admin@example.com", "changed_at": "2024-01-01T10:00:00Z", "change_reason": "Update"}]}` |
| `/api/v1/rules/{ruleId}/rollback/{version}` | POST | 回滚到指定版本 | `{"reason": "回滚原因"}` | `{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "enabled": true, "priority": 100, "version": 3, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules/{ruleId}/toggle` | POST | 启用/禁用规则 | `{"enabled": false, "reason": "禁用原因"}` | `{"id": "rule-123", "name": "规则名称", "handlerKey": "model_usage_billing", "description": "规则描述", "config": {...}, "enabled": false, "priority": 100, "version": 2, "createdAt": "2024-01-01T10:00:00Z", "updatedAt": "2024-01-01T10:00:00Z", "updatedBy": "admin@example.com"}` |
| `/api/v1/rules/execute` | POST | 执行规则 | `{"ruleId": "rule-123", "context": {"user_id": "user-123", "action": "create_agent", "resource": "agent-789", "metadata": {"token_count": 1000}}}` | `{"allowed": true, "reason": "Rule executed successfully", "data": {"cost": 0.05, "currency": "USD"}}` |

## 技术栈总结

- **Web 框架**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 + AsyncSession
- **缓存**: Redis 7.x + 本地 LRU 缓存
- **数据库**: MySQL 8.0 / PostgreSQL 15
- **监控**: Prometheus + Grafana
- **追踪**: OpenTelemetry
- **测试**: pytest + pytest-asyncio
- **安全**: simpleeval, AST 解析（规则验证）
- **消息队列**: Redis Pub/Sub（缓存失效通知）
