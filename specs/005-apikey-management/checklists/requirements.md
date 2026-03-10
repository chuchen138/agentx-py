## 实施
- [ ] 1.1 定义 API Key 实体和数据模型
     【目标对象】`app/domain/apikey/model.py`
     【修改目的】定义 API Key 相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/apikey/model/*.java`
     【修改内容】
        - 创建 ApiKey 模型（api_keys 表）
        - 定义字段：id, api_key, agent_id, user_id, name, status, usage_count, last_used_at, expires_at, created_at, updated_at
        - 实现业务方法：is_expired(), is_available(), increment_usage()
        - 实现 Pydantic Schema

- [ ] 1.2 实现创建 API Key 生成策略
     【目标对象】`app/domain/apikey/service.py`
     【修改目的】实现安全的 API Key 生成机制
     【修改方式】实现领域服务方法
     【相关依赖】ApiKey 模型
     【修改内容】
        - 实现 generate_api_key() 方法
        - 生成格式：ak_{agentId}_{randomString}
        - 使用 UUID 或加密安全的随机数生成器
        - 确保 API Key 的唯一性和安全性

- [ ] 1.3 实现 API Key 验证逻辑
     【目标对象】`app/domain/apikey/service.py`
     【修改目的】提供 API Key 验证服务
     【修改方式】实现领域服务方法
     【相关依赖】ApiKey 模型
     【修改内容】
        - 实现 validate_api_key() 方法
        - 检查 API Key 是否存在
        - 检查状态是否启用
        - 检查是否过期
        - 返回验证结果（包含 user_id 和 agent_id）

- [ ] 1.4 实现 API Key 使用记录更新
     【目标对象】`app/domain/apikey/service.py`
     【修改目的】追踪 API Key 的使用情况
     【修改方式】实现领域服务方法
     【相关依赖】ApiKey 模型
     【修改内容】
        - 实现 update_usage() 方法
        - 更新使用计数（increment by 1）
        - 更新最后使用时间
        - 使用数据库原子操作确保一致性

- [ ] 1.5 实现 API Key 仓储模式
     【目标对象】`app/domain/apikey/repository.py`
     【修改目的】定义 API Key 数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ApiKeyRepository 接口
        - 实现 SQLAlchemy ApiKeyRepository
        - 实现 CRUD 操作（create, get, update, delete, list）
        - 实现复杂查询（按 user_id, agent_id, name, status 查询）
        - 实现按 api_key 查找

- [ ] 1.6 实现 API Key 领域服务层
     【目标对象】`app/domain/apikey/service.py`
     【修改目的】封装 API Key 相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ApiKeyRepository
     【修改内容】
        - 创建 API Key（包含生成和验证）
        - 查找 API Key
        - 验证 API Key
        - 更新使用记录
        - 获取用户的 API Key 列表（支持筛选）
        - 获取 Agent 的 API Key 列表
        - 更新 API Key 状态
        - 删除 API Key
        - 重置 API Key（生成新的 api_key）

- [ ] 1.7 实现 API Key 应用服务层
     【目标对象】`app/application/apikey/`
     【修改目的】编排 API Key 相关的用例
     【修改方式】实现应用服务
     【相关依赖】ApiKeyDomainService, AgentDomainService（依赖 Agent 模块）
     【修改内容】
        - 实现 ApiKeyAppService
        - create_api_key(agentId, name, userId)：创建 API Key 并验证 Agent 权限
        - get_user_api_keys(userId, queryRequest)：获取用户的 API Key 列表（支持筛选）
        - get_agent_api_keys(agentId, userId)：获取 Agent 的 API Key 列表
        - get_api_key(apiKeyId, userId)：获取 API Key 详情
        - update_api_key_status(apiKeyId, status, userId)：更新 API Key 状态
        - delete_api_key(apiKeyId, userId)：删除 API Key
        - reset_api_key(apiKeyId, userId)：重置 API Key（生成新的 api_key）
        - validate_external_api_key(apiKey)：验证外部 API Key 并更新使用记录

- [ ] 1.8 实现 API Key DTO 和请求/响应模型
     【目标对象】`app/application/apikey/dto.py`
     【修改目的】定义 API Key 相关的数据传输对象
     【修改方式】实现 Pydantic 模型
     【相关依赖】无
     【修改内容】
        - ApiKeyDTO：API Key 数据传输对象
        - CreateApiKeyRequest：创建 API Key 请求
        - UpdateApiKeyStatusRequest：更新 API Key 状态请求
        - QueryApiKeyRequest：查询 API Key 请求（支持 name, status, agent_id 筛选）
        - ApiKeyValidationResult：API Key 验证结果
        - 实现 Assembler 用于 Entity 和 DTO 之间的转换

- [ ] 1.9 创建 API Key 路由（FastAPI）
     【目标对象】`app/api/v1/apikey/`
     【修改目的】暴露 API Key 相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】ApiKeyAppService
     【修改内容】
        - `POST /api/v1/api-keys` - 创建 API Key
        - `GET /api/v1/api-keys` - 获取用户的 API Key 列表
        - `GET /api/v1/api-keys/{id}` - 获取 API Key 详情
        - `PUT /api/v1/api-keys/{id}/status` - 更新 API Key 状态
        - `DELETE /api/v1/api-keys/{id}` - 删除 API Key
        - `POST /api/v1/api-keys/{id}/reset` - 重置 API Key


- [ ] 1.10 实现 API Key 认证中间件
     【目标对象】`app/api/middleware/`
     【修改目的】保护需要 API Key 认证的 API 端点
     【修改方式】实现 FastAPI 中间件
     【相关依赖】ApiKeyDomainService
     【修改内容】
        - 创建 ApiKeyAuth 中间件
        - 从请求头提取 API Key（X-API-Key 或 Authorization Bearer）
        - 验证 API Key 有效性
        - 将用户信息和 Agent 信息注入 Request 对象
        - 处理认证失败（返回 401 Unauthorized）
        - 更新使用记录

- [ ] 1.11 添加依赖注入配置
     【目标对象】`app/core/dependency.py` 或类似配置文件
     【修改目的】配置 API Key 相关服务的依赖注入
     【修改方式】使用 FastAPI Depends
     【相关依赖】无
     【修改内容】
        - 配置 ApiKeyRepository 依赖
        - 配置 ApiKeyDomainService 依赖
        - 配置 ApiKeyAppService 依赖

- [ ] 1.12 创建数据库迁移文件
     【目标对象】`alembic/versions/`
     【修改目的】创建 api_keys 表
     【修改方式】使用 Alembic 创建迁移文件
     【相关依赖】SQLAlchemy
     【修改内容】
        - 创建 alembic revision
        - 定义 api_keys 表结构
        - 添加索引（api_key, user_id, agent_id）
        - 测试迁移脚本

- [ ] 1.13 编写单元测试
     【目标对象】`tests/test_apikey_service.py`
     【修改目的】确保 API Key 管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】ApiKeyAppService, ApiKeyDomainService
     【修改内容】
        - 测试 API Key 生成
        - 测试 API Key 验证（有效、无效、禁用、过期）
        - 测试 API Key 创建
        - 测试 API Key 状态更新
        - 测试 API Key 删除
        - 测试 API Key 重置
        - 测试使用记录更新
        - 测试查询功能（按用户、按 Agent、按状态、按名称）

- [ ] 1.14 编写集成测试
     【目标对象】`tests/integration/test_apikey_api.py`
     【修改目的】确保 API Key API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, ApiKeyAppService
     【修改内容】
        - 测试创建 API Key 端点
        - 测试获取 API Key 列表端点
        - 测试获取 API Key 详情端点
        - 测试更新 API Key 状态端点
        - 测试删除 API Key 端点
        - 测试重置 API Key 端点
        - 测试认证中间件
        - 测试权限验证（只能操作自己的 API Key）

- [ ] 1.15 安全性验证
     【目标对象】`app/domain/apikey/`
     【修改目的】确保 API Key 安全性
     【修改方式】安全审计和测试
     【相关依赖】无
     【修改内容】
        - 验证 API Key 生成算法的安全性（随机性和不可预测性）
        - 验证 API Key 存储安全性
        - 验证 API Key 验证逻辑的正确性
        - 验证使用记录更新的原子性
        - 测试并发场景下的安全性
        - 测试过期时间处理
        - 确保不会泄露敏感信息
