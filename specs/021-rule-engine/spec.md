# 规则引擎能力 - 需求说明与场景描述

## 1. 概述

规则引擎能力是 AgentX 平台的核心配置化能力，提供业务规则的声明式定义、管理和应用机制。通过规则引擎，平台可以将复杂的业务逻辑抽象为可配置的规则，支持动态调整业务策略而无需修改代码。

### 1.1 模块定位

- **核心作用**：为平台提供可配置的业务规则管理能力，支持规则定义、执行、监控全生命周期
- **服务对象**：管理员（规则配置）、其他业务模块（规则应用）、运维人员（规则监控）
- **应用场景**：计费规则、权限控制、业务策略配置、A/B 测试、限流降级等
- **核心价值**：
  - **配置化管理**：业务规则可配置化，无需修改代码即可调整
  - **策略灵活**：支持多种规则类型，覆盖不同业务场景
  - **易于扩展**：新增规则类型只需添加新的处理器，无需改动现有代码
  - **类型安全**：使用强类型的枚举定义规则处理器，减少错误
  - **安全可控**：规则执行沙箱化，防止代码注入攻击
  - **可观测性**：完整的规则执行日志和监控指标

---

## 2. 技术选型与约束

### 2.1 规则引擎内核
- **实现方式**: 轻量级策略工厂模式 + Python 表达式评估
- **表达式引擎**: 使用 `simpleeval` 库（安全的 eval 替代）或自定义 AST 解析器
- **规则存储**: 
  - 主存储：MySQL（rules 表）
  - 缓存层：Redis（TTL=5min，LRU 淘汰）
  - 本地缓存：LRU Cache（maxsize=100）
- **规则格式**: JSON 存储配置参数，支持嵌套结构和复杂对象

### 2.2 性能指标
- **单规则评估**: < 1ms（命中缓存）/ < 10ms（未命中）
- **批量规则**（10 条以内）: < 50ms
- **缓存命中率**: > 90%（热点规则）
- **并发支持**: 1000+ QPS
- **规则加载延迟**: 启动预加载 < 5s（1000 条规则）

### 2.3 安全约束
- **规则注入防护**: 
  - 禁止直接使用 eval/exec
  - 使用 simpleeval 限制可用操作符和函数
  - 规则内容白名单校验（黑名单关键字过滤）
- **权限控制**:
  - 规则 CRUD：仅 ADMIN 角色
  - 规则查询：认证用户
  - 规则执行：服务间调用（API Key 认证）
- **审计日志**: 记录所有规则变更（操作人、时间、旧值、新值、IP 地址）
- **版本追溯**: 每次修改自动生成新版本，支持回滚到任意历史版本

### 2.4 规则生命周期
- **版本管理**: 每次修改自动生成新版本（version++），创建版本快照
- **回滚机制**: 支持回滚到任意历史版本，回滚时创建新版本
- **热更新**: 修改后立即生效（通过 Redis 发布/订阅通知各节点）
- **冲突解决**: 
  - 同 handlerKey 多条规则时，取 version 最大且 enabled=true 的规则
  - 支持优先级字段（priority），高优先级优先
  - priority 相同时，按 updated_at 降序

---

## 3. 处理器接口规范

### 3.1 IRuleHandler 接口定义

```python
from typing import Any, Dict, Optional
from pydantic import BaseModel
from abc import ABC, abstractmethod

class RuleContext(BaseModel):
    """规则执行上下文"""
    user_id: str
    action: str
    resource: Optional[str] = None
    metadata: Dict[str, Any] = {}

class RuleResult(BaseModel):
    """规则执行结果"""
    allowed: bool
    reason: str
    data: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None

class IRuleHandler(ABC):
    """规则处理器接口"""
    
    @abstractmethod
    def get_handler_key(self) -> str:
        """返回处理器标识"""
        pass
    
    @abstractmethod
    async def execute(self, context: RuleContext, rule_config: Dict) -> RuleResult:
        """
        执行规则
        
        Args:
            context: 规则执行上下文
            rule_config: 规则配置（JSON 格式）
        
        Returns:
            RuleResult: 规则执行结果
        
        Raises:
            RuleExecutionError: 规则执行失败
        """
        pass
```

### 3.2 异常处理

```python
class RuleExecutionError(Exception):
    """规则执行异常"""
    def __init__(self, message: str, error_code: str, rule_id: Optional[str] = None):
        self.message = message
        self.error_code = error_code
        self.rule_id = rule_id
        super().__init__(self.message)

class RuleValidationError(Exception):
    """规则验证异常"""
    pass

class ConcurrencyError(Exception):
    """并发冲突异常"""
    pass
```

---

## 3. 核心场景

### 3.1 计费规则管理

```json
{
  "id": "rule-billing-001",
  "name": "GPT-4 模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费，区分模型类型",
  "enabled": true,
  "priority": 100,
  "version": 3,
  "config": {
    "model_type": "gpt-4",
    "input_price_per_1k_tokens": 0.03,
    "output_price_per_1k_tokens": 0.06,
    "currency": "USD",
    "min_charge": 0.001,
    "free_quota_per_day": 1000
  },
  "createdAt": "2024-01-01T10:00:00Z",
  "updatedAt": "2024-01-15T14:30:00Z",
  "updatedBy": "admin@example.com"
}
```

### 3.1 计费规则管理

管理员配置和管理计费相关的规则，用于计费系统中。

**场景描述**：

1. 管理员进入规则管理页面
2. 创建计费规则，指定 handlerKey 为计费规则类型
3. 填写规则名称、描述和配置参数
4. 保存规则
5. 计费服务在使用时根据 handlerKey 查询对应规则
6. 应用规则计算费用

**关键业务规则**：

- 每个 handlerKey 可以有多个配置实例
- 计费服务根据产品类型选择对应的计费规则
- 支持规则启用/禁用开关
- 规则修改后自动递增版本号

### 3.2 权限规则管理

管理员配置权限控制规则，用于权限验证。

**场景描述**：

1. 管理员创建权限规则
2. 指定规则类型为权限类型
3. 填写权限配置信息（功能代码、所需订阅等级等）
4. 保存规则
5. 权限验证服务在验证时查询对应规则
6. 应用规则判断用户是否有权限

**关键业务规则**：

- 权限规则定义了不同功能的访问权限
- 权限规则可以动态调整，即时生效
- 支持 deny_by_default 配置
- 支持多订阅等级组合

### 3.3 业务策略配置

管理员配置各种业务策略规则，支持业务灵活调整。

**场景描述**：

1. 管理员根据业务需求创建策略规则
2. 选择合适的规则类型（限流、A/B 测试等）
3. 填写策略配置参数
4. 保存规则
5. 业务服务在执行策略时查询并应用规则

**关键业务规则**：

- 策略规则可以配置参数
- 策略规则支持启用/禁用
- 支持优先级设置
- 支持时间范围控制
  }
}
```

### 4.4 限流规则示例

```json
{
  "id": "rule-rate-004",
  "name": "API 调用限流",
  "handlerKey": "API_RATE_LIMITING",
  "description": "限制每个用户每分钟 API 调用次数",
  "enabled": true,
  "priority": 90,
  "version": 1,
  "config": {
    "limit_type": "per_user",
    "max_requests": 100,
    "window_seconds": 60,
    "burst_allowance": 10,
    "exceeded_action": "reject"
  }
}
```

---

## 5. 处理器注册方式

### 5.1 装饰器注册

```python
from app.domain.rule.handler import rule_handler, IRuleHandler, RuleContext, RuleResult

@rule_handler("MODEL_USAGE_BILLING")
class ModelUsageBillingHandler(IRuleHandler):
    def get_handler_key(self) -> str:
        return "MODEL_USAGE_BILLING"
    
    async def execute(self, context: RuleContext, rule_config: Dict) -> RuleResult:
        # 实现计费逻辑
        usage_data = context.metadata.get("usage_data", {})
        input_tokens = usage_data.get("input_tokens", 0)
        output_tokens = usage_data.get("output_tokens", 0)
        
        price_per_1k = rule_config.get("input_price_per_1k_tokens", 0.03)
        cost = (input_tokens + output_tokens) / 1000 * price_per_1k
        
        return RuleResult(
            allowed=True,
            reason="Billing calculated successfully",
            data={"cost": cost, "currency": "USD"}
        )
```

### 5.2 策略工厂自动发现

```python
# app/domain/rule/factory.py
from typing import Dict, Type
from .handler import IRuleHandler

class RuleHandlerFactory:
    _handlers: Dict[str, IRuleHandler] = {}
    
    @classmethod
    def register(cls, handler: IRuleHandler):
        """注册处理器实例"""
        cls._handlers[handler.get_handler_key()] = handler
    
    @classmethod
    def get_handler(cls, handler_key: str) -> IRuleHandler:
        """根据 handlerKey 获取处理器"""
        if handler_key not in cls._handlers:
            from .exceptions import RuleExecutionError
            raise RuleExecutionError(
                f"Handler not found: {handler_key}",
                error_code="HANDLER_NOT_FOUND"
            )
        return cls._handlers[handler_key]
    
    @classmethod
    def get_all_handlers(cls) -> Dict[str, IRuleHandler]:
        """获取所有已注册的处理器"""
        return cls._handlers.copy()
```

### 5.3 处理器自动发现机制

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

---

## 2. 核心能力

### 2.1 规则管理

规则管理是规则引擎的基础功能，提供规则的增删改查能力。

#### 功能描述

- **规则创建**：管理员创建新的业务规则
- **规则更新**：更新规则的基本信息和配置
- **规则查询**：按条件查询规则列表
- **规则详情查询**：获取单个规则的详细信息
- **规则删除**：删除不再使用的规则

#### 关键数据

**RuleDTO（规则数据传输对象）**

- `id`：规则唯一 ID
- `name`：规则名称
- `handlerKey`：规则处理器标识
- `description`：规则描述
- `createdAt`：创建时间
- `updatedAt`：更新时间

---

### 2.2 规则配置

规则配置支持定义不同类型的业务规则，通过 handlerKey 映射到具体的应用逻辑。

#### 功能描述

- **规则类型定义**：通过 handlerKey 定义规则类型
- **规则描述**：描述规则的用途和应用场景
- **规则元数据**：支持为规则添加额外的元信息

#### 规则类型（RuleHandlerKey）

规则引擎支持多种规则类型，每种类型对应一个处理器：

- **计费规则类型**：用于定义不同的计费策略
  - 例如：按 Token 计费、按次计费、按时长计费等

- **权限规则类型**：用于定义权限控制策略
  - 例如：功能访问权限、操作权限等

- **业务策略规则**：用于定义各种业务策略
  - 例如：限流策略、阈值控制等

---

### 2.3 规则应用

规则引擎提供规则查询和应用接口，其他业务模块可以根据需要查询和应用规则。

#### 功能描述

- **规则查询**：业务模块按 handlerKey 查询对应规则
- **规则缓存**：规则数据可以缓存以提高性能
- **规则版本管理**：支持规则的历史版本管理

#### 应用方式

```
业务代码
   ↓
根据 handlerKey 查询规则
   ↓
获取规则配置
   ↓
应用规则到业务逻辑
```

---

## 3. 核心场景

### 3.1 计费规则管理

管理员配置和管理计费相关的规则，用于计费系统中。

**场景描述**：

1. 管理员进入规则管理页面
2. 创建计费规则，指定 handlerKey 为计费规则类型
3. 填写规则名称、描述和配置参数
4. 保存规则
5. 计费服务在使用时根据 handlerKey 查询对应规则
6. 应用规则计算费用

**关键业务规则**：

- 每个 handlerKey 可以有多个配置实例
- 计费服务根据产品类型选择对应的计费规则
- 支持规则启用/禁用开关
- 规则修改后自动递增版本号

### 3.2 权限规则管理

管理员配置权限控制规则，用于权限验证。

**场景描述**：

1. 管理员创建权限规则
2. 指定规则类型为权限类型
3. 填写权限配置信息（功能代码、所需订阅等级等）
4. 保存规则
5. 权限验证服务在验证时查询对应规则
6. 应用规则判断用户是否有权限

**关键业务规则**：

- 权限规则定义了不同功能的访问权限
- 权限规则可以动态调整，即时生效
- 支持 deny_by_default 配置
- 支持多订阅等级组合

### 3.3 业务策略配置

管理员配置各种业务策略规则，支持业务灵活调整。

**场景描述**：

1. 管理员根据业务需求创建策略规则
2. 选择合适的规则类型（限流、A/B 测试等）
3. 填写策略配置参数
4. 保存规则
5. 业务服务在执行策略时查询并应用规则

**关键业务规则**：

- 策略规则可以配置参数
- 策略规则支持启用/禁用
- 支持优先级设置
- 支持时间范围控制

---

## 4. 数据模型

### 4.1 RuleEntity

规则实体类，定义规则的基本信息。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | String | 规则唯一 ID |
| name | String(200) | 规则名称（索引） |
| handlerKey | String(100) | 规则处理器标识（索引） |
| description | String(500) | 规则描述 |
| config | JSON | 规则配置参数 |
| enabled | Boolean | 是否启用（索引） |
| priority | Integer | 优先级，越高越优先 |
| version | Integer | 版本号，每次修改递增 |
| createdAt | DateTime | 创建时间 |
| updatedAt | DateTime | 更新时间 |
| updatedBy | String(100) | 最后更新人邮箱 |

**索引设计**：
- PRIMARY KEY (id)
- INDEX idx_handler_key (handler_key)
- INDEX idx_enabled (enabled)
- INDEX idx_handler_key_version (handler_key, version)
- INDEX idx_enabled_priority (enabled, priority)

### 4.2 RuleVersionEntity（规则版本快照）

用于记录规则历史版本的快照。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | String | 版本记录 ID |
| rule_id | String | 规则 ID（外键） |
| version | Integer | 版本号 |
| snapshot | JSON | 规则完整快照 |
| changed_by | String | 变更人邮箱 |
| changed_at | DateTime | 变更时间 |
| change_reason | String(500) | 变更原因 |

### 4.3 RuleAuditLogEntity（审计日志）

记录规则操作日志。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | String | 日志 ID |
| rule_id | String | 规则 ID（索引） |
| action | String(50) | 操作类型（CREATE/UPDATE/DELETE/EXECUTE） |
| old_value | JSON | 修改前的值 |
| new_value | JSON | 修改后的值 |
| operator | String | 操作人邮箱 |
| operated_at | DateTime | 操作时间（索引） |
| ip_address | String(45) | IP 地址 |

### 4.4 RuleHandlerKey 常量类

规则处理器标识常量，定义支持的规则类型。

```python
class RuleHandlerKey:
    """规则处理器标识常量"""
    
    # 计费规则
    MODEL_USAGE_BILLING = "model_usage_billing"  # 模型使用计费
    AGENT_CREATION_BILLING = "agent_creation_billing"  # Agent 创建计费
    API_CALL_BILLING = "api_call_billing"  # API 调用计费
    STORAGE_USAGE_BILLING = "storage_usage_billing"  # 存储使用计费
    
    # 权限规则
    FEATURE_ACCESS_PERMISSION = "feature_access_permission"  # 功能访问权限
    OPERATION_PERMISSION = "operation_permission"  # 操作权限
    DATA_ACCESS_PERMISSION = "data_access_permission"  # 数据访问权限
    
    # 业务策略
    RATE_LIMITING = "rate_limiting"  # 限流策略
    AB_TEST_ONBOARDING = "ab_test_onboarding"  # A/B 测试 - 引导流程
    CIRCUIT_BREAKER = "circuit_breaker"  # 熔断降级
```

---

---

## 5. 接口定义

### 5.1 创建规则

```http
POST /api/v1/rules
```

**请求体**：

```json
{
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费",
  "config": {
    "model_type": "gpt-4",
    "input_price_per_1k_tokens": 0.03,
    "output_price_per_1k_tokens": 0.06
  },
  "priority": 100
}
```

**响应数据**：

```json
{
  "id": "rule-123",
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费",
  "config": {...},
  "enabled": true,
  "priority": 100,
  "version": 1,
  "createdAt": "2024-01-01T10:00:00Z",
  "updatedAt": "2024-01-01T10:00:00Z",
  "updatedBy": "admin@example.com"
}
```

### 5.2 更新规则

```http
PUT /api/v1/rules/{ruleId}
```

**请求体**：

```json
{
  "name": "模型按 Token 计费（新价格）",
  "description": "调整了价格参数",
  "config": {
    "model_type": "gpt-4",
    "input_price_per_1k_tokens": 0.04,
    "output_price_per_1k_tokens": 0.08
  },
  "priority": 100
}
```

**注意**：更新操作会自动递增 version 号，并创建版本快照。

### 5.3 查询规则列表

```http
GET /api/v1/rules
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| handlerKey | String | 否 | 规则处理器标识 |
| keyword | String | 否 | 关键词（模糊匹配名称和描述） |
| enabled | Boolean | 否 | 是否启用过滤 |
| priority | Integer | 否 | 最小优先级 |
| page | Integer | 否 | 页码，默认 1 |
| pageSize | Integer | 否 | 每页数量，默认 15 |
| sortBy | String | 否 | 排序字段，默认 priority |
| sortOrder | String | 否 | 排序方向：asc/desc，默认 desc |

**响应数据**：

```json
{
  "records": [
    {
      "id": "rule-123",
      "name": "模型按 Token 计费",
      "handlerKey": "MODEL_USAGE_BILLING",
      "enabled": true,
      "priority": 100,
      "version": 3
    }
  ],
  "current": 1,
  "size": 15,
  "total": 100
}
```

### 5.4 获取规则详情

```http
GET /api/v1/rules/{ruleId}
```

**响应数据**：

```json
{
  "id": "rule-123",
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费",
  "config": {...},
  "enabled": true,
  "priority": 100,
  "version": 3,
  "createdAt": "2024-01-01T10:00:00Z",
  "updatedAt": "2024-01-15T14:30:00Z",
  "updatedBy": "admin@example.com"
}
```

### 5.5 根据处理器标识查询规则

```http
GET /api/v1/rules/by-handler-key/{handlerKey}
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| useCache | Boolean | 否 | 是否使用缓存，默认 true |

**响应数据**：单个规则对象（返回最新且启用的版本），如果不存在则返回 null

### 5.6 删除规则

```http
DELETE /api/v1/rules/{ruleId}
```

**说明**：软删除，将 enabled 设置为 false，不真正删除数据。

### 5.7 获取规则历史版本

```http
GET /api/v1/rules/{ruleId}/versions
```

**响应数据**：

```json
{
  "versions": [
    {
      "version": 3,
      "snapshot": {...},
      "changed_by": "admin@example.com",
      "changed_at": "2024-01-15T14:30:00Z",
      "change_reason": "调整价格参数"
    },
    {
      "version": 2,
      "snapshot": {...},
      "changed_by": "admin@example.com",
      "changed_at": "2024-01-10T09:00:00Z",
      "change_reason": "添加免费配额"
    }
  ]
}
```

### 5.8 回滚到指定版本

```http
POST /api/v1/rules/{ruleId}/rollback/{version}
```

**请求体**：

```json
{
  "reason": "回滚到稳定版本"
}
```

**说明**：回滚操作会创建一个新版本，其配置与指定版本相同。

### 5.9 启用/禁用规则

```http
POST /api/v1/rules/{ruleId}/toggle
```

**请求体**：

```json
{
  "enabled": false,
  "reason": "临时禁用进行调试"
}
```

### 5.10 执行规则（内部服务调用）

```http
POST /api/v1/rules/execute
```

**请求体**：

```json
{
  "ruleId": "rule-123",
  "context": {
    "user_id": "user-456",
    "action": "create_agent",
    "resource": "agent-789",
    "metadata": {
      "token_count": 1000
    }
  }
}
```

**响应数据**：

```json
{
  "allowed": true,
  "reason": "Rule executed successfully",
  "data": {
    "cost": 0.05,
    "currency": "USD"
  }
}
```

```http
DELETE /api/rules/{ruleId}
```

---

## 6. 非功能性需求

### 6.1 性能要求

- **单规则查询响应时间**: < 10ms（命中缓存）/ < 50ms（未命中）
- **批量规则查询**（10 条以内）: < 100ms
- **规则执行延迟**: < 1ms（简单规则）/ < 10ms（复杂表达式）
- **缓存命中率**: > 90%（热点规则）
- **并发支持**: 1000+ QPS
- **启动预加载**: < 5s（1000 条规则）

### 6.2 可靠性要求

- **规则数据持久化**: 丢失率 < 0.01%
- **数据备份**: 每日自动备份，支持时间点恢复
- **操作回滚**: 支持回滚到任意历史版本
- **故障恢复**: 服务重启后自动预热缓存
- **降级策略**: 规则引擎不可用时，支持默认策略

### 6.3 可扩展性要求

- **新增规则类型**: 在 RuleHandlerKey 常量类中添加常量，创建对应处理器实现
- **新增规则处理器**: 实现 IRuleHandler 接口，使用装饰器注册
- **规则配置扩展**: config 字段使用 JSON 类型，支持灵活扩展
- **插件化架构**: 未来支持从指定目录动态加载外部处理器插件

### 6.4 安全性要求

- **权限控制**:
  - 规则 CRUD：仅 ADMIN 角色
  - 规则查询：认证用户
  - 规则执行：服务间调用（API Key 认证）
- **审计日志**: 
  - 记录所有规则变更（操作人、时间、旧值、新值、IP 地址）
  - 记录规则执行日志（rule_id、context_hash、result、execution_time）
  - 支持操作追溯和合规审计
- **规则注入防护**:
  - 禁止直接使用 eval/exec
  - 使用 simpleeval 限制可用操作符和函数
  - 规则内容白名单校验
  - 黑名单关键字过滤（eval、exec、__import__等）
- **数据加密**: 敏感配置字段支持加密存储

---

## 7. 与其他能力的关联

### 7.1 与计费能力的关联

- **集成方式**: 计费系统使用规则引擎配置计费策略
- **查询规则**: 计费服务根据产品类型查询对应的 handlerKey（如 MODEL_USAGE_BILLING）
- **应用规则**: 从规则引擎获取规则配置，使用策略工厂获取计费策略处理器
- **执行计算**: 执行处理器计算费用，返回计费结果
- **优势**: 支持动态调整计费策略，规则变更不需要修改代码

**示例流程**：
```
用户调用 API → 计费拦截器 → 查询计费规则 (handlerKey=MODEL_USAGE_BILLING)
→ 获取规则配置 → 策略工厂获取处理器 → 执行计费逻辑 → 返回费用
```

### 7.2 与权限管理的关联

- **集成方式**: 权限管理使用规则引擎配置权限策略
- **查询规则**: 根据功能类型查询权限规则（handlerKey=FEATURE_ACCESS_PERMISSION）
- **应用规则**: 验证用户订阅等级、角色等是否满足规则要求
- **返回结果**: allowed=true/false，包含拒绝原因

**示例场景**：
- 用户尝试访问高级功能 → 查询权限规则 → 验证用户订阅等级 → 允许/拒绝访问

### 7.3 与限流降级的关联

- **集成方式**: 限流模块使用规则引擎配置限流策略
- **查询规则**: 根据用户 ID 或 IP 查询限流规则（handlerKey=RATE_LIMITING）
- **应用规则**: 检查请求频率是否超过阈值
- **降级策略**: 规则引擎不可用时，使用默认限流配置

### 7.4 与 A/B 测试的关联

- **集成方式**: A/B 测试模块使用规则引擎配置分流策略
- **查询规则**: 根据实验名称查询 A/B 测试规则（handlerKey=AB_TEST_*）
- **应用规则**: 根据用户特征和流量分配比例决定实验分组

### 7.5 与其他业务的关联

- **通用集成模式**: 
  1. 业务模块定义自己的 handlerKey
  2. 实现对应的规则处理器
  3. 在策略工厂中注册
  4. 通过数据库 API 创建规则实例
  5. 业务场景中查询并应用规则
- **解耦优势**: 业务规则与代码分离，支持配置化调整

---

## 8. 使用示例

### 8.1 Python - 创建计费规则

```python
from fastapi import FastAPI
import httpx

app = FastAPI()

# 创建规则请求
create_request = {
    "name": "模型按 Token 计费",
    "handlerKey": "MODEL_USAGE_BILLING",
    "description": "按照输入和输出的 Token 数量计费",
    "config": {
        "model_type": "gpt-4",
        "input_price_per_1k_tokens": 0.03,
        "output_price_per_1k_tokens": 0.06,
        "currency": "USD",
        "min_charge": 0.001
    },
    "priority": 100
}

# 调用 API 创建规则
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/v1/rules",
        json=create_request,
        headers={"Authorization": "Bearer admin_token"}
    )
    created_rule = response.json()
    print(f"Created rule: {created_rule['id']}")
```

### 8.2 Python - 应用规则到计费

```python
from app.domain.rule.handler import RuleContext, IRuleHandler
from app.domain.rule.factory import RuleHandlerFactory
from app.domain.rule.service import RuleDomainService

# 查询计费规则
rule_service = RuleDomainService()
billing_rule = await rule_service.get_by_handler_key("MODEL_USAGE_BILLING")

# 准备执行上下文
context = RuleContext(
    user_id="user-123",
    action="model_inference",
    metadata={
        "model": "gpt-4",
        "input_tokens": 500,
        "output_tokens": 300
    }
)

# 获取处理器并执行
handler = RuleHandlerFactory.get_handler(billing_rule.handler_key)
result = await handler.execute(context, billing_rule.config)

print(f"Billing cost: {result.data['cost']} {result.data['currency']}")
```

### 8.3 Python - 更新规则配置

```python
# 更新规则请求
update_request = {
    "name": "模型按 Token 计费（新价格）",
    "description": "调整了价格参数",
    "config": {
        "model_type": "gpt-4",
        "input_price_per_1k_tokens": 0.04,  # 价格上涨
        "output_price_per_1k_tokens": 0.08,  # 价格上涨
        "currency": "USD",
        "min_charge": 0.001
    },
    "priority": 100
}

async with httpx.AsyncClient() as client:
    response = await client.put(
        f"http://localhost:8000/api/v1/rules/{rule_id}",
        json=update_request,
        headers={"Authorization": "Bearer admin_token"}
    )
    updated_rule = response.json()
    print(f"Updated rule version: {updated_rule['version']}")
```

### 8.4 Python - 查询规则历史版本并回滚

```python
# 获取历史版本列表
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"http://localhost:8000/api/v1/rules/{rule_id}/versions"
    )
    versions = response.json()["versions"]
    print(f"Total versions: {len(versions)}")

# 回滚到版本 2
rollback_response = await client.post(
    f"http://localhost:8000/api/v1/rules/{rule_id}/rollback/2",
    json={"reason": "回滚到稳定版本"},
    headers={"Authorization": "Bearer admin_token"}
)
rolled_back_rule = rollback_response.json()
print(f"Rolled back to version: {rolled_back_rule['version']}")
```

### 8.5 Python - 自定义规则处理器

```python
from app.domain.rule.handler import (
    rule_handler, IRuleHandler, RuleContext, RuleResult
)

@rule_handler("CUSTOM_DISCOUNT_RULE")
class CustomDiscountHandler(IRuleHandler):
    def get_handler_key(self) -> str:
        return "CUSTOM_DISCOUNT_RULE"
    
    async def execute(self, context: RuleContext, rule_config: dict) -> RuleResult:
        # 实现折扣计算逻辑
        user_level = context.metadata.get("user_level", "normal")
        order_amount = context.metadata.get("order_amount", 0)
        
        discount_rate = rule_config.get(f"{user_level}_rate", 1.0)
        final_amount = order_amount * discount_rate
        
        return RuleResult(
            allowed=True,
            reason=f"Discount applied: {discount_rate}",
            data={
                "original_amount": order_amount,
                "discount_rate": discount_rate,
                "final_amount": final_amount
            }
        )

# 处理器会自动注册到 RuleHandlerFactory
```
