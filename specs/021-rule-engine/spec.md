# 规则引擎能力 - 需求说明与场景描述

## 1. 概述

规则引擎能力是 AgentX 平台的核心配置化能力，提供业务规则的声明式定义、管理和应用机制。通过规则引擎，平台可以将复杂的业务逻辑抽象为可配置的规则，支持动态调整业务策略而无需修改代码。

### 1.1 模块定位

- **核心作用**：为平台提供可配置的业务规则管理能力
- **服务对象**：管理员（规则配置）、其他业务模块（规则应用）
- **应用场景**：计费规则、权限控制、业务策略配置等

### 1.2 核心价值

- **配置化管理**：业务规则可配置化，无需修改代码即可调整
- **策略灵活**：支持多种规则类型，覆盖不同业务场景
- **易于扩展**：新增规则类型只需添加新的处理器，无需改动现有代码
- **类型安全**：使用强类型的枚举定义规则处理器，减少错误

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
3. 填写规则名称和描述
4. 保存规则
5. 计费服务在使用时根据 handlerKey 查询对应规则

**关键业务规则**：

- 每个 handlerKey 可以有多个配置实例
- 计费服务根据产品类型选择对应的计费规则

### 3.2 权限规则管理

管理员配置权限控制规则，用于权限验证。

**场景描述**：

1. 管理员创建权限规则
2. 指定规则类型为权限类型
3. 填写权限配置信息
4. 保存规则
5. 权限验证服务在验证时查询对应规则

**关键业务规则**：

- 权限规则定义了不同功能的访问权限
- 权限规则可以动态调整，即时生效

### 3.3 业务策略配置

管理员配置各种业务策略规则，支持业务灵活调整。

**场景描述**：

1. 管理员根据业务需求创建策略规则
2. 选择合适的规则类型
3. 填写策略配置
4. 保存规则
5. 业务服务在执行策略时查询并应用规则

**关键业务规则**：

- 策略规则可以配置参数
- 策略规则支持启用/禁用

---

## 4. 数据模型

### 4.1 RuleEntity

规则实体类，定义规则的基本信息。

| 字段名 | 类型 | 说明 |
|-------|------|------|
| id | String | 规则唯一 ID |
| name | String | 规则名称 |
| handlerKey | RuleHandlerKey | 规则处理器标识（枚举） |
| description | String | 规则描述 |
| createdAt | LocalDateTime | 创建时间 |
| updatedAt | LocalDateTime | 更新时间 |

### 4.2 RuleHandlerKey

规则处理器标识枚举，定义支持的规则类型。

```java
public enum RuleHandlerKey {
    // 模型使用计费
    MODEL_USAGE_BILLING("model_usage_billing"),
    
    // Agent 创建计费
    AGENT_CREATION_BILLING("agent_creation_billing"),
    
    // API 调用计费
    API_CALL_BILLING("api_call_billing"),
    
    // 存储使用计费
    STORAGE_USAGE_BILLING("storage_usage_billing");
    
    private final String code;
    
    RuleHandlerKey(String code) {
        this.code = code;
    }
    
    public String getCode() {
        return code;
    }
}
```

---

## 5. 接口定义

### 5.1 创建规则

```http
POST /api/rules
```

**请求体**：

```json
{
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费"
}
```

**响应数据**：

```json
{
  "id": "rule-123",
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费",
  "createdAt": "2024-01-01T10:00:00",
  "updatedAt": "2024-01-01T10:00:00"
}
```

### 5.2 更新规则

```http
PUT /api/rules/{ruleId}
```

**请求体**：

```json
{
  "name": "模型按 Token 计费（新）",
  "description": "更新后的描述"
}
```

### 5.3 查询规则列表

```http
GET /api/rules
```

**请求参数**：

| 参数名 | 类型 | 必填 | 说明 |
|-------|------|------|------|
| handlerKey | String | 否 | 规则处理器标识 |
| keyword | String | 否 | 关键词（模糊匹配名称和描述） |
| page | Integer | 否 | 页码，默认 1 |
| pageSize | Integer | 否 | 每页数量，默认 15 |

**响应数据**：

```json
{
  "records": [...],
  "current": 1,
  "size": 15,
  "total": 100
}
```

### 5.4 获取规则详情

```http
GET /api/rules/{ruleId}
```

**响应数据**：

```json
{
  "id": "rule-123",
  "name": "模型按 Token 计费",
  "handlerKey": "MODEL_USAGE_BILLING",
  "description": "按照输入和输出的 Token 数量计费",
  "createdAt": "2024-01-01T10:00:00",
  "updatedAt": "2024-01-01T10:00:00"
}
```

### 5.5 根据处理器标识查询规则

```http
GET /api/rules/by-handler-key/{handlerKey}
```

**响应数据**：单个规则对象，如果不存在则返回 null

### 5.6 删除规则

```http
DELETE /api/rules/{ruleId}
```

---

## 6. 非功能性需求

### 6.1 性能要求

- 规则查询响应时间 < 100ms
- 支持规则缓存
- 支持批量查询

### 6.2 可靠性要求

- 规则数据丢失率 < 0.01%
- 提供数据备份机制
- 支持操作回滚

### 6.3 可扩展性要求

- 支持新增规则类型（枚举）
- 支持新增规则处理器
- 支持规则配置的扩展字段

### 6.4 安全性要求

- 规则管理接口需要管理员权限
- 记录规则变更的审计日志
- 支持操作追溯

---

## 7. 与其他能力的关联

### 7.1 与计费能力的关联

- 计费系统使用计费规则计算费用
- 支持动态调整计费策略
- 规则变更不需要修改代码

### 7.2 与权限管理的关联

- 权限管理使用权限规则进行权限验证
- 支持动态调整权限策略
- 灵活控制功能访问

### 7.3 与其他业务的关联

- 其他业务模块可以定义自己的规则类型
- 通过 handlerKey 映射到具体的应用逻辑
- 支持业务策略的配置化管理

---

## 8. 使用示例

### 8.1 创建计费规则

```java
// 创建规则请求
CreateRuleRequest request = new CreateRuleRequest();
request.setName("模型按 Token 计费");
request.setHandlerKey(RuleHandlerKey.MODEL_USAGE_BILLING);
request.setDescription("按照输入和输出的 Token 数量计费");

// 调用服务创建规则
RuleDTO rule = ruleAppService.createRule(request);
```

### 8.2 应用规则到计费

```java
// 查询计费规则
RuleDTO billingRule = ruleAppService.getRuleByHandlerKey(
    RuleHandlerKey.MODEL_USAGE_BILLING.getCode()
);

// 根据规则类型选择计费策略
BillingStrategy strategy = billingStrategyFactory.getStrategy(
    billingRule.getHandlerKey()
);

// 应用规则计算费用
BigDecimal cost = strategy.calculateCost(usageData);
```

### 8.3 更新规则配置

```java
// 更新规则请求
UpdateRuleRequest request = new UpdateRuleRequest();
request.setName("模型按 Token 计费（新价格）");
request.setDescription("调整了价格参数");

// 调用服务更新规则
RuleDTO updatedRule = ruleAppService.updateRule(request, ruleId);
```
