## 实施

- [ ] 1.1 定义 LLM 服务商和模型实体
     【目标对象】`app/domain/llm/models.py`
     【修改目的】定义 LLM 服务商和模型的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【修改内容】
        - 创建 Provider 模型（providers 表）
        - 创建 Model 模型（models 表）
        - 定义 ProviderType 枚举（ALL, OFFICIAL, CUSTOM）
        - 定义 ProviderProtocol 枚举（OPENAI, MOONSHOT, AZURE_OPENAI）
        - 定义 ModelType 枚举（CHAT, EMBEDDING）
        - 实现 Pydantic Schema（ProviderDTO, ModelDTO）

- [ ] 1.2 实现 LLM 服务商仓储模式
     【目标对象】`app/domain/llm/repository.py`
     【修改目的】定义 LLM 服务商数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ProviderRepository 接口
        - 实现 SQLAlchemy ProviderRepository
        - 实现 CRUD 操作
        - 实现按用户查询
        - 实现按类型查询（官方/自定义）

- [ ] 1.3 实现 ModelRepository
     【目标对象】`app/domain/llm/repository.py`
     【修改目的】定义 LLM 模型的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy, ModelEntity
     【修改内容】
        - 定义 ModelRepository 接口
        - 实现 SQLAlchemy ModelRepository
        - 实现 CRUD 操作
        - 实现按服务商查询
        - 实现按类型查询激活模型

- [ ] 1.4 实现 LLMDomainService
     【目标对象】`app/domain/llm/service.py`
     【修改目的】封装 LLM 服务商和模型管理的核心业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】ProviderRepository, ModelRepository
     【修改内容】
        - 创建服务商（验证协议类型）
        - 更新服务商
        - 删除服务商
        - 创建模型
        - 更新模型
        - 删除模型
        - 切换服务商/模型状态

- [ ] 1.5 实现配置加密解密
     【目标对象】`app/domain/llm/encryption.py`
     【修改目的】保护服务商配置中的敏感信息（API Key）
     【修改方式】使用 AES-256 加密
     【相关依赖】cryptography
     【修改内容】
        - 实现 ProviderConfig 加密
        - 实现 ProviderConfig 解密
        - 实现 API Key 掩码显示
        - 密钥管理

- [ ] 1.6 实现协议适配器
     【目标对象】`app/infrastructure/llm/adapters/`
     【修改目的】统一不同 LLM 服务商的接口差异
     【修改方式】策略模式
     【相关依赖】httpx
     【修改内容】
        - ProtocolAdapter 抽象基类
        - OpenAIProtocolAdapter
        - MoonshotProtocolAdapter
        - AzureOpenAIProtocolAdapter
        - CustomProtocolAdapter
        - 统一的 sendChatRequest、sendEmbeddingRequest 接口

- [ ] 1.7 实现高可用网关服务
     【目标对象】`app/application/llm/high_availability_service.py`
     【修改目的】提供智能路由、负载均衡、故障转移能力
     【修改方式】实现应用服务
     【相关依赖】LLMDomainService
     【修改内容】
        - syncModelToGateway - 同步模型到网关
        - selectBestProvider - 选择最佳服务商和模型
        - reportCallResult - 上报调用结果
        - 会话亲和性缓存
        - 负载均衡策略（轮询、健康度加权）
        - 故障转移机制
        - 降级链支持

- [ ] 1.8 实现健康度监控
     【目标对象】`app/application/llm/health_monitor.py`
     【修改目的】监控模型实例的健康状态
     【修改方式】定时任务和实时上报
     【相关依赖】无
     【修改内容】
        - 调用成功率统计
        - 平均延迟计算
        - 错误率监控
        - 健康度评分算法
        - P99 延迟统计

- [ ] 1.9 实现 LLMAppService
     【目标对象】`app/application/llm/llm_app_service.py`
     【修改目的】编排 LLM 管理相关的用例（用户侧）
     【修改方式】实现应用服务
     【相关依赖】LLMDomainService, HighAvailabilityService
     【修改内容】
        - createProvider - 创建服务商
        - updateProvider - 更新服务商
        - deleteProvider - 删除服务商
        - getAllProviders - 获取所有服务商
        - updateProviderStatus - 切换服务商状态
        - createModel - 创建模型
        - updateModel - 更新模型
        - deleteModel - 删除模型
        - updateModelStatus - 切换模型状态
        - getActiveModelsByType - 获取激活的模型列表

- [ ] 1.10 实现 AdminLLMAppService
     【目标对象】`app/application/llm/admin_llm_app_service.py`
     【修改目的】编排 LLM 管理相关的用例（管理员侧）
     【修改方式】实现应用服务
     【相关依赖】LLMDomainService
     【修改内容】
        - createOfficialProvider - 创建官方服务商
        - updateOfficialProvider - 更新官方服务商
        - deleteOfficialProvider - 删除官方服务商
        - createOfficialModel - 创建官方模型
        - updateOfficialModel - 更新官方模型
        - deleteOfficialModel - 删除官方模型

- [ ] 1.11 实现 Assembler 转换器
     【目标对象】`app/application/llm/assembler.py`
     【修改目的】领域模型和 DTO 之间的转换
     【修改方式】Assembler 模式
     【相关依赖】Pydantic Schema
     【修改内容】
        - ProviderAssembler: Entity ↔ DTO
        - ModelAssembler: Entity ↔ DTO
        - 配置掩码处理

- [ ] 1.12 实现领域事件
     【目标对象】`app/domain/llm/events.py`
     【修改目的】通过领域事件解耦各模块
     【修改方式】事件驱动架构
     【相关依赖】无
     【修改内容】
        - ModelCreatedEvent - 模型创建事件
        - ModelUpdatedEvent - 模型更新事件
        - ModelDeletedEvent - 模型删除事件
        - ModelStatusChangedEvent - 模型状态变更事件
        - ModelsBatchDeletedEvent - 批量删除模型事件
        - 事件监听器：HighAvailabilityEventListener

- [ ] 1.13 创建 API 路由 - LLM 管理
     【目标对象】`app/api/v1/llm/`
     【修改目的】暴露 LLM 管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】LLMAppService
     【修改内容】
        - `POST /api/v1/llm/providers` - 创建服务商
        - `GET /api/v1/llm/providers` - 获取服务商列表
        - `GET /api/v1/llm/providers/{id}` - 获取服务商详情
        - `PUT /api/v1/llm/providers/{id}` - 更新服务商
        - `DELETE /api/v1/llm/providers/{id}` - 删除服务商
        - `POST /api/v1/llm/providers/{id}/status` - 切换服务商状态
        - `POST /api/v1/llm/models` - 创建模型
        - `GET /api/v1/llm/models` - 获取模型列表
        - `PUT /api/v1/llm/models/{id}` - 更新模型
        - `DELETE /api/v1/llm/models/{id}` - 删除模型
        - `POST /api/v1/llm/models/{id}/status` - 切换模型状态
        - `GET /api/v1/llm/models/active` - 获取激活的模型

- [ ] 1.14 创建 API 路由 - 管理员 LLM 管理
     【目标对象】`app/api/v1/admin/llm/`
     【修改目的】暴露管理员 LLM 管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AdminLLMAppService
     【修改内容】
        - `POST /api/v1/admin/llm/providers` - 创建官方服务商
        - `PUT /api/v1/admin/llm/providers/{id}` - 更新官方服务商
        - `DELETE /api/v1/admin/llm/providers/{id}` - 删除官方服务商
        - `POST /api/v1/admin/llm/models` - 创建官方模型
        - `PUT /api/v1/admin/llm/models/{id}` - 更新官方模型
        - `DELETE /api/v1/admin/llm/models/{id}` - 删除官方模型
        - `GET /api/v1/admin/llm/statistics` - 获取统计数据

- [ ] 1.15 创建数据库迁移脚本
     【目标对象】`alembic/versions/`
     【修改目的】创建 LLM 相关数据库表
     【修改方式】使用 Alembic 创建迁移
     【相关依赖】Alembic, SQLAlchemy
     【修改内容】
        - 创建 providers 表迁移脚本
        - 创建 models 表迁移脚本
        - 创建必要的索引（user_id, provider_id, status）
        - 添加外键约束

- [ ] 1.16 编写单元测试 - 领域层
     【目标对象】`tests/test_llm_domain.py`
     【修改目的】确保 LLM 领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】LLMDomainService
     【修改内容】
        - 测试服务商创建、更新、删除
        - 测试模型创建、更新、删除
        - 测试配置加密解密
        - 测试状态切换
        - 测试协议验证

- [ ] 1.17 编写单元测试 - 高可用网关
     【目标对象】`tests/test_llm_high_availability.py`
     【修改目的】确保高可用网关逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】HighAvailabilityService
     【修改内容】
        - 测试智能路由选择
        - 测试会话亲和性
        - 测试负载均衡
        - 测试故障转移
        - 测试降级链
        - 测试健康度评估

- [ ] 1.18 编写单元测试 - 协议适配器
     【目标对象】`tests/test_llm_protocol_adapter.py`
     【修改目的】确保协议适配器正确性
     【修改方式】使用 pytest 和 Mock
     【相关依赖】ProtocolAdapter
     【修改内容】
        - 测试 OpenAI 协议适配
        - 测试 Moonshot 协议适配
        - 测试 Azure OpenAI 协议适配
        - 测试自定义协议适配
        - 测试请求转换
        - 测试响应标准化

- [ ] 1.19 编写集成测试 - API 端点
     【目标对象】`tests/integration/test_llm_api.py`
     【修改目的】确保 LLM API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, LLMAppService
     【修改内容】
        - 测试创建服务商端点
        - 测试获取服务商列表端点
        - 测试更新服务商端点
        - 测试删除服务商端点
        - 测试创建模型端点
        - 测试获取模型列表端点
        - 测试切换状态端点
        - 测试权限控制（用户隔离）

- [ ] 1.20 编写集成测试 - 管理员 API
     【目标对象】`tests/integration/test_admin_llm_api.py`
     【修改目的】确保管理员 LLM API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AdminLLMAppService
     【修改内容】
        - 测试创建官方服务商端点
        - 测试更新官方服务商端点
        - 测试删除官方服务商端点
        - 测试创建官方模型端点
        - 测试获取统计数据端点

- [ ] 1.21 实现缓存策略
     【目标对象】`app/infrastructure/cache/llm_cache.py`
     【修改目的】提高性能，减少数据库查询
     【修改方式】使用 Redis
     【相关依赖】redis
     【修改内容】
        - 缓存官方模型列表
        - 缓存激活模型列表
        - 缓存会话选择的模型实例
        - 缓存失效策略

- [ ] 1.22 实现监控和日志
     【目标对象】`app/infrastructure/monitoring/llm_monitor.py`
     【修改目的】监控系统运行状态
     【修改方式】结构化日志和指标收集
     【相关依赖】logging, prometheus_client
     【修改内容】
        - 实现应用日志
        - 实现审计日志（服务商和模型操作记录）
        - 实现性能监控（API 响应时间、路由选择时间）
        - 实现错误监控（异常捕获和告警）
        - 实现调用指标收集（成功率、延迟）