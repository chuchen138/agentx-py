# API 密钥管理技术设计

## 概述

API 密钥管理模块遵循 AgentX 项目的分层架构设计，使用 FastAPI 和 SQLAlchemy 构建，实现 API 密钥的创建、验证、使用统计和权限控制等功能。

## 技术架构

### 架构分层

系统采用四层架构：接口层提供 API 密钥相关 HTTP 接口和请求参数校验；应用层提供应用服务、DTO 转换器和数据传输对象；领域层提供领域服务、领域实体、仓储接口和业务规则；基础设施层提供 SQLAlchemy 数据访问、数据库表映射、异常处理和日志记录。

### 技术栈

系统使用 FastAPI 作为 Web 框架，SQLAlchemy 2.0 作为 ORM 框架，Pydantic 进行数据验证，MySQL/PostgreSQL 作为数据存储，Python secrets 模块生成加密安全的密钥，Alembic 进行数据库迁移，pytest 进行测试。

## 核心模型

### 领域模型

### ApiKeyEntity

API 密钥领域模型封装了密钥的状态和行为，包含以下字段：
- id: API 密钥主键 ID
- api_key: 密钥值（格式：ak_{agent_id}_{random_string}）
- agent_id: 关联的 Agent ID
- user_id: 创建者用户 ID
- name: 密钥名称/描述
- status: 状态（True=启用，False=禁用）
- usage_count: 已使用次数（默认 0）
- last_used_at: 最后使用时间（nullable）
- expires_at: 过期时间（nullable，None 表示永不过期）
- created_at: 创建时间（自动设置）
- updated_at: 更新时间（自动更新）

领域行为包括：
- is_expired(): 检查是否已过期
- is_available(): 检查是否可用（状态启用且未过期）
- increment_usage(): 原子增加使用次数

### 密钥格式

密钥格式采用固定格式：`ak_{agent_id}_{random_string}`
- 前缀 `ak_`: 固定标识符，表明这是 API Key
- Agent ID: 便于识别密钥归属，方便运维追踪和问题排查
- Random String: 16 位十六进制随机字符串（使用 Python secrets.token_hex(8) 生成），提供 >= 128 位熵值，确保全局唯一性和不可预测性
- 示例：`ak_agent123_a3f5c8d9e2b1f4a6`

这种格式的优势：
1. 语义清晰：通过前缀快速识别类型
2. 易于调试：包含 Agent ID 便于定位问题
3. 安全性高：16 位随机字符串提供足够熵值
4. 性能优化：可直接从密钥中提取 Agent ID 减少数据库查询

### 数据传输对象

ApiKeyDTO 用于传输 API 密钥信息，包含实体所有字段和计算字段如关联的 Agent 名称、是否已过期和是否可用。ApiKeyValidationResult 封装 API 密钥验证结果，包含验证是否成功、关联的用户 ID、关联的 Agent ID 和验证结果消息。

### 请求对象

CreateApiKeyRequest 创建 API 密钥包含关联的 Agent ID 和 API Key 名称。QueryApiKeyRequest 查询 API 密钥支持 API Key 名称模糊查询、状态筛选和 Agent ID 筛选。

## 核心算法

### 密钥生成算法

密钥生成采用确定性与随机性结合的方式：
1. **前缀标识**：固定使用 `ak_` 作为前缀，提供语义标识便于识别
2. **Agent ID 嵌入**：包含 Agent ID 可快速定位密钥归属，便于运维追踪和问题排查
3. **随机字符串生成**：使用 Python `secrets.token_hex(8)` 生成 16 位十六进制随机字符串
   - secrets 模块基于操作系统熵源，提供加密安全的随机数
   - 16 位十六进制提供 128 位熵值，碰撞概率极低
4. **唯一性保证**：通过数据库唯一索引约束确保最终一致性
5. **生成流程**：
   ```python
   import secrets
   
   def generate_api_key(agent_id: str) -> str:
       random_part = secrets.token_hex(8)  # 16 位十六进制
       return f"ak_{agent_id}_{random_part}"
   ```

### 密钥验证机制

密钥验证流程：
1. **提取密钥**：从请求头（X-API-Key 或 Authorization Bearer）提取 API Key
2. **数据库查询**：根据密钥值查询数据库，加载 ApiKey 实体
3. **存在性检查**：如果记录不存在，返回验证失败（错误码：INVALID_API_KEY）
4. **状态检查**：检查 status 是否为 True（启用），如果为 False 返回失败（错误码：API_KEY_DISABLED）
5. **过期检查**：调用 is_expired() 方法，如果已过期返回失败（错误码：API_KEY_EXPIRED）
6. **更新统计**：验证通过后，原子更新 usage_count（+1）和 last_used_at（当前时间）
7. **返回结果**：返回验证成功，包含 user_id 和 agent_id

验证规则：
```python
def validate_api_key(api_key_value: str) -> ApiKeyValidationResult:
    # 1. 查找密钥
    api_key = repository.get_by_key(api_key_value)
    if not api_key:
        return ApiKeyValidationResult(success=False, error="INVALID_API_KEY")
    
    # 2. 检查状态
    if not api_key.status:
        return ApiKeyValidationResult(success=False, error="API_KEY_DISABLED")
    
    # 3. 检查过期
    if api_key.is_expired():
        return ApiKeyValidationResult(success=False, error="API_KEY_EXPIRED")
    
    # 4. 更新使用统计（原子操作）
    repository.increment_usage(api_key.id)
    
    # 5. 返回成功
    return ApiKeyValidationResult(
        success=True,
        user_id=api_key.user_id,
        agent_id=api_key.agent_id
    )
```

### 使用统计更新机制

使用统计更新策略采用原子的 SQL 更新方式，避免并发场景下的丢失更新问题：

**原子更新实现**（使用 SQLAlchemy）：
```python
def increment_usage(api_key_id: int):
    """原子增加使用次数和更新时间"""
    db.execute(
        update(ApiKey)
        .where(ApiKey.id == api_key_id)
        .values(
            usage_count=ApiKey.usage_count + 1,
            last_used_at=datetime.utcnow()
        )
    )
```

**优势**：
1. **数据一致性**：数据库层面的原子操作确保并发场景下不会丢失更新
2. **性能优化**：单次 SQL 更新，无需先读取再写入，减少数据库交互
3. **无锁设计**：依赖数据库行级锁，无需应用层加锁，降低死锁风险
4. **高并发支持**：支持 QPS >= 1000 的并发更新

### 权限控制机制

权限控制原则：
1. **用户隔离**：用户只能查看和管理自己创建的 API 密钥
2. **Agent 所有权验证**：创建密钥时必须验证 Agent 属于当前用户
3. **全链路鉴权**：所有密钥操作都携带用户 ID 进行权限验证

实现方式：
1. **查询过滤**：所有查询自动添加 `user_id=current_user_id` 条件
   ```python
   def get_user_api_keys(user_id: str) -> List[ApiKey]:
       return db.query(ApiKey).filter(ApiKey.user_id == user_id).all()
   ```
2. **删除验证**：删除操作先查询验证所有权再执行删除
   ```python
   def delete_api_key(api_key_id: str, user_id: str):
       api_key = db.query(ApiKey).filter(
           ApiKey.id == api_key_id,
           ApiKey.user_id == user_id  # 权限过滤
       ).first()
       if not api_key:
           raise PermissionError("无权操作该密钥")
       db.delete(api_key)
   ```
3. **创建验证**：创建密钥前先验证 Agent 是否属于当前用户
   ```python
   def create_api_key(agent_id: str, user_id: str, name: str):
       # 验证 Agent 所有权
       agent = agent_repository.get_by_id(agent_id)
       if not agent or agent.user_id != user_id:
           raise PermissionError("无权为该 Agent 创建密钥")
       
       # 创建密钥
       api_key = ApiKey(
           agent_id=agent_id,
           user_id=user_id,
           name=name,
           api_key=generate_api_key(agent_id)
       )
       db.add(api_key)
   ```

## 服务接口

### 应用层服务

**ApiKeyAppService** 提供以下功能：

1. **create_api_key(agent_id: str, name: str, user_id: str) -> ApiKeyDTO**
   - 验证 Agent 是否存在且属于当前用户
   - 生成 API 密钥（调用 domain service）
   - 创建实体并保存到数据库
   - 转换为 DTO 返回（仅创建时返回密钥明文）
   - 记录审计日志

2. **get_user_api_keys(user_id: str, query: QueryApiKeyRequest) -> List[ApiKeyDTO]**
   - 查询用户密钥列表（支持名称模糊搜索、状态筛选、Agent 筛选）
   - 批量查询 Agent 信息避免 N+1 查询问题
   - 填充 Agent 名称到 DTO
   - 按创建时间倒序排列

3. **get_agent_api_keys(agent_id: str, user_id: str) -> List[ApiKeyDTO]**
   - 获取指定 Agent 的所有密钥列表
   - 验证用户对该 Agent 的权限

4. **get_api_key(api_key_id: str, user_id: str) -> ApiKeyDTO**
   - 获取单个密钥详情
   - 验证所有权
   - 计算并返回是否已过期、是否可用等状态

5. **update_api_key_status(api_key_id: str, status: bool, user_id: str) -> ApiKeyDTO**
   - 更新密钥启用/禁用状态
   - 验证所有权
   - 记录操作日志

6. **delete_api_key(api_key_id: str, user_id: str)**
   - 永久删除密钥
   - 验证所有权
   - 记录删除日志

7. **reset_api_key(api_key_id: str, user_id: str) -> str**
   - 为已有密钥生成新的密钥值
   - 保持其他属性（关联关系、状态等）不变
   - 旧密钥立即失效
   - 清零使用统计
   - 仅返回新密钥明文一次

8. **validate_external_api_key(api_key_value: str) -> ApiKeyValidationResult**
   - 验证外部请求携带的 API Key
   - 检查存在性、状态、过期时间
   - 原子更新使用统计
   - 返回验证结果及关联的用户 ID 和 Agent ID

### 领域层服务

**ApiKeyDomainService** 提供以下核心业务逻辑：

1. **create_api_key(agent_id: str, user_id: str, name: str) -> ApiKey**
   - 生成加密安全的 API 密钥值
   - 创建 ApiKey 实体
   - 设置初始状态（启用）

2. **get_by_key(api_key_value: str) -> Optional[ApiKey]**
   - 根据密钥值查找实体

3. **validate_api_key(api_key_value: str) -> ApiKeyValidationResult**
   - 完整的验证流程（存在性、状态、过期）
   - 返回验证结果

4. **update_usage(api_key_id: int)**
   - 原子更新使用次数和最后使用时间

5. **get_by_user(user_id: str, filters: dict) -> List[ApiKey]**
   - 获取用户的密钥列表（支持筛选）

6. **get_by_agent(agent_id: str) -> List[ApiKey]**
   - 获取 Agent 的所有密钥

7. **get_by_id(api_key_id: str) -> ApiKey**
   - 根据 ID 获取密钥详情

8. **update_status(api_key_id: str, status: bool)**
   - 更新密钥状态

9. **delete(api_key_id: str)**
   - 删除密钥

10. **reset(api_key_id: str) -> str**
    - 重置密钥值，生成新的密钥
    - 返回新密钥明文

### 转换器

ApiKeyAssembler 提供实体转 DTO、实体列表转 DTO 列表和 DTO 转实体（用于创建）等功能。转换逻辑包括复制属性和设置计算字段如是否已过期和是否可用。

## 数据库设计

### 表结构

API 密钥表包含 API 密钥 ID、密钥值、关联的 Agent ID、创建者用户 ID、密钥名称、状态、已使用次数、最后使用时间、过期时间、创建时间和更新时间等字段。索引设计包括主键索引、密钥值唯一索引、Agent ID 索引、用户 ID 索引和状态索引。

### 索引设计

密钥值唯一索引确保密钥不重复，支持高效的密钥验证。Agent ID 索引支持按 Agent 查询密钥列表。用户 ID 索引支持用户隔离查询，提高查询效率。状态索引支持按状态筛选，便于管理。

## 关键设计决策

### 密钥存储方式

系统采用明文存储 API 密钥值的决策，理由包括密钥验证需要快速查询、数据库索引直接完成无需解密、密钥不是用户密码泄露风险可控。安全措施包括应用层不直接返回密钥明文仅创建和重置时返回、数据库访问受权限控制、建议未来支持密钥加密存储。

### 密钥格式设计

系统采用包含 Agent ID 的固定格式密钥设计，理由包括前缀提供语义标识便于识别、包含 Agent ID 可快速定位密钥归属便于运维追踪、16 位随机字符串提供足够熵值确保安全性、格式固定便于后续扩展和解析。

### 使用统计更新策略

系统使用原子 SQL 更新而非应用层先读后写的决策，理由包括避免并发场景下的数据丢失、减少数据库交互次数一次 SQL 更新完成、性能更优无锁等待。

### 查询优化

系统使用批量查询避免 N+1 问题的决策，理由包括查询密钥列表时需填充 Agent 名称、单个查询避免循环查询提升性能。

### 权限控制方式

系统在查询和更新语句中直接添加用户 ID 条件的决策，理由包括数据库层面隔离确保数据安全、避免应用层权限漏洞、简化业务逻辑。

### 事务边界控制

系统写操作使用事务读操作不加事务的决策，理由包括写操作需要保证数据一致性、读操作不加事务减少连接占用、验证操作作为高频调用不应加事务。

## 集成

### Agent 管理模块集成

集成点包括创建密钥前验证 Agent 是否存在且属于当前用户、查询密钥列表时填充 Agent 名称、批量查询 Agent 信息以优化性能。依赖关系包括应用层依赖 Agent 领域服务进行验证和查询操作。

### 用户管理模块集成

集成点包括密钥关联用户 ID 实现用户隔离、密钥操作需要用户认证通过框架层面实现。实现方式包括通过请求上下文获取当前用户 ID，在所有操作中携带用户 ID 进行权限控制。

### 会话管理模块集成

集成点包括密钥验证成功后可用于调用 Agent 对话、验证结果包含用户 ID 和 Agent ID 可用于后续授权。交互流程包括外部请求携带 API Key、API Key 应用服务验证密钥返回用户 ID 和 Agent ID、会话应用服务使用验证结果。

## 异常处理

### 业务异常

系统定义 Agent 不存在或无权限、API 密钥不存在、API 密钥验证失败、API 密钥不可用等业务异常，异常类型和消息通过业务异常抛出，返回相应的错误码和信息。

### 日志记录

系统记录关键操作日志包括创建密钥、删除密钥、重置密钥、状态变更等操作的时间和相关信息。密钥验证失败记录安全审计日志便于问题追溯和安全分析。

## 性能考虑

### 查询性能

系统性能优化措施：
1. **索引优化**：
   - 密钥值唯一索引：加速验证查询（O(1) 时间复杂度）
   - 用户 ID 索引：支持用户维度查询
   - Agent ID 索引：支持 Agent 维度查询
   - 状态索引：支持状态筛选

2. **响应时间目标**：
   - 密钥验证（含缓存）：< 5ms
   - 密钥验证（数据库）：< 50ms
   - 查询密钥列表：< 100ms（1000 条记录内）
   - 查询密钥详情：< 20ms

3. **吞吐量目标**：
   - 验证 QPS：>= 5000（含缓存）
   - 创建 QPS：>= 500
   - 查询 QPS：>= 1000

4. **数据库优化**：
   - 使用连接池管理（最小 10，最大 100 连接）
   - 批量操作减少往返次数
   - 读写分离（可选，验证走从库）

### 写入性能

系统性能优化包括创建密钥响应时间少于 50 毫秒单条插入、更新统计响应时间少于 20 毫秒原子 SQL 更新、删除密钥响应时间少于 50 毫秒索引删除。

### 并发处理

系统使用数据库原子操作处理并发更新、避免应用层面锁机制依赖数据库锁、高并发场景下使用连接池管理。

### 缓存策略

为提高密钥验证性能，系统采用 Redis 缓存策略：

1. **缓存内容**：将有效的 API 密钥信息缓存到 Redis
   - Key: `apikey:{api_key_value}`
   - Value: JSON 格式存储 {user_id, agent_id, status, expires_at}
   - TTL: 设置为密钥过期时间或 24 小时（取较小值）

2. **验证流程优化**：
   ```python
   async def validate_api_key(api_key_value: str):
       # 1. 先查缓存
       cached = await redis.get(f"apikey:{api_key_value}")
       if cached:
           # 检查缓存中的状态和过期时间
           if cached.status and not cached.is_expired():
               # 异步更新使用统计（不阻塞响应）
               asyncio.create_task(repository.increment_usage(cached.id))
               return ValidationResult(success=True, ...)
       
       # 2. 缓存未命中，查数据库
       api_key = repository.get_by_key(api_key_value)
       if api_key and api_key.is_available():
           # 写入缓存
           await redis.setex(
               f"apikey:{api_key_value}",
               ttl=calculate_ttl(api_key.expires_at),
               value=api_key.to_cache_dict()
           )
           # 更新使用统计
           repository.increment_usage(api_key.id)
           return ValidationResult(success=True, ...)
   ```

3. **缓存失效策略**：
   - 密钥被禁用时删除缓存
   - 密钥被删除时删除缓存
   - 密钥重置时删除旧密钥缓存
   - 自然过期后自动失效

4. **性能提升**：
   - 缓存命中率目标：> 90%
   - 验证响应时间：缓存命中 < 5ms，未命中 < 50ms
   - 支持 QPS >= 5000（含缓存）

## 安全设计

### 密钥安全

系统密钥安全设计包括：
1. **生成安全**：使用 Python secrets.token_hex(8) 生成 16 位十六进制随机字符串，提供 128 位熵值
2. **存储安全**：数据库层面明文存储（便于快速查询），但应用层不暴露明文
3. **访问控制**：仅创建和重置时返回密钥明文，之后无法查看
4. **防碰撞**：16 位随机字符串碰撞概率 < 2^-128，可忽略不计
5. **不可预测性**：基于操作系统熵源，无法通过已有密钥推测新密钥

### 安全加固措施

1. **防止暴力破解**：
   - 实现速率限制：单个 IP 每分钟最多尝试 100 次验证
   - 连续失败 10 次后触发告警
   - 使用 Redis 记录失败次数

2. **防止重放攻击**：
   - 虽然密钥本身不是临时令牌，但结合 HTTPS 可防止中间人攻击
   - 未来可扩展支持 JWT 临时令牌

3. **审计日志**：
   - 所有密钥操作记录详细日志（谁、何时、做了什么）
   - 验证失败记录安全日志（包含 IP、User-Agent 等信息）
   - 异常行为检测（如地理位置突变、时间异常等）

4. **密钥轮换支持**：
   - 提供便捷的密钥重置功能
   - 支持灰度切换（新旧密钥并行一段时间）
   - 旧密钥立即失效机制

### 访问控制

系统用户只能管理自己的 API 密钥、所有操作都需要用户身份认证、数据库层面添加用户 ID 条件。

### 输入验证

系统使用 Pydantic 进行请求参数校验：
- Agent ID 和用户 ID 校验为非空
- 密钥名称校验为非空且长度 <= 100
- 状态校验为布尔值
- 过期时间校验为有效的 ISO 8601 格式（如果提供）

### 审计日志

系统记录所有密钥操作日志、密钥验证失败记录安全审计日志、便于问题追溯和安全分析。

## 监控与可观测性

### 关键指标监控

1. **业务指标**：
   - API Key 总数（按状态、按 Agent 分布）
   - 每日新增 Key 数量
   - 每日删除 Key 数量
   - 活跃 Key 比例（24 小时内有使用）

2. **性能指标**：
   - 验证请求 QPS
   - 验证成功率（成功次数 / 总尝试次数）
   - 平均响应时间（P50, P95, P99）
   - 缓存命中率

3. **安全指标**：
   - 验证失败次数（按原因分类：不存在、已禁用、已过期）
   - 异常 IP 访问频率
   - 连续失败告警次数
   - 密钥轮换频率

### 日志记录

1. **操作日志**（INFO 级别）：
   ```json
   {
     "timestamp": "2024-01-01T12:00:00Z",
     "level": "INFO",
     "event": "API_KEY_CREATED",
     "user_id": "user_123",
     "api_key_id": "apikey_456",
     "agent_id": "agent_789",
     "ip": "192.168.1.100"
   }
   ```

2. **安全日志**（WARN 级别）：
   ```json
   {
     "timestamp": "2024-01-01T12:00:00Z",
     "level": "WARN",
     "event": "API_KEY_VALIDATION_FAILED",
     "reason": "API_KEY_DISABLED",
     "api_key_prefix": "ak_agent_789_...",
     "ip": "10.0.0.50",
     "user_agent": "Mozilla/5.0..."
   }
   ```

3. **错误日志**（ERROR 级别）：
   - 数据库异常
   - 缓存异常
   - 系统异常

### 告警规则

1. **验证失败率告警**：
   - 条件：5 分钟内失败率 > 10%
   - 级别：WARNING
   - 可能原因：批量密钥过期、系统故障

2. **QPS 突增告警**：
   - 条件：当前 QPS > 过去 1 小时平均值 200%
   - 级别：WARNING
   - 可能原因：恶意攻击、流量异常

3. **缓存失效率高**：
   - 条件：10 分钟内缓存命中率 < 50%
   - 级别：WARNING
   - 可能原因：缓存穿透、Key 集中过期

4. **连续失败告警**：
   - 条件：同一 IP 连续失败 >= 10 次
   - 级别：CRITICAL
   - 动作：触发 IP 限流或封禁

## 扩展性设计

### 过期时间管理

系统预见过期时间管理：
1. **字段预留**：数据库表已包含 `expires_at` 字段（nullable）
2. **方法实现**：ApiKeyEntity 已实现 `is_expired()` 方法
3. **验证逻辑**：验证流程已包含过期检查
4. **自动失效**：过期后密钥自动失效，无需人工干预
5. **清理任务**：支持定时任务清理过期密钥（可选）

### 未来扩展方向

1. **密钥类型扩展**：支持不同类型的密钥（只读密钥、管理员密钥等）
2. **权限分级**：为不同密钥设置不同的权限级别
3. **IP 白名单**：限制密钥只能在指定 IP 地址使用
4. **频率限制**：对密钥的调用频率进行限制
5. **JWT 令牌**：支持基于 JWT 的临时访问令牌
6. **密钥轮换**：自动定期轮换密钥提高安全性