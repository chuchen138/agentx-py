## 实施
- [ ] 1.1 记忆元数据常量定义
     【目标对象】`app/domain/memory/constant/`
     【修改目的】定义记忆相关常量
     【修改方式】创建常量接口
     【相关依赖】无
     【修改内容】
        - 创建 MemoryMetadataConstant 接口
        - 定义 USER_ID, ITEM_ID, MEMORY_TYPE, TAGS, STATUS 常量

- [ ] 1.2 记忆类型枚举定义
     【目标对象】`app/domain/memory/constant/`
     【修改目的】定义记忆类型枚举
     【修改方式】使用 Python Enum 实现
     【相关依赖】无
     【修改内容】
        - 创建 MemoryType 枚举（PROFILE, TASK, FACT, EPISODIC）
        - 实现 fromCode 类方法
        - 实现 getCode 和 getDescription 方法
        - 定义每种类型的描述和用例

- [ ] 1.3 创建记忆实体和数据模型
     【目标对象】`app/domain/memory/model/`
     【修改目的】定义记忆相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/memory/model/MemoryItemEntity.java`, `AgentX/docs/memory_schema.md`
     【修改内容】
        - 创建 MemoryItem 模型（memory_items 表）
        - 定义字段：id, user_id, type, text, data, importance, tags, source_session_id, dedupe_hash, status, created_at, updated_at
        - 创建 MemoryVectorStore 模型（memory_vector_store 表）
        - 定义字段：embedding_id, item_id, embedding, text, metadata, created_at
        - 实现 Pydantic Schema（MemoryItemDTO, MemoryResult, CandidateMemory, CreateMemoryRequest, QueryMemoryRequest）

- [ ] 1.4 实现记忆仓储模式
     【目标对象】`app/domain/memory/repository.py`
     【修改目的】定义记忆数据访问接口
     【修改方式】实现 Repository 模式，使用 SQLAlchemy ORM
     【相关依赖】SQLAlchemy 2.0+, PGVector 扩展
     【修改内容】
        - 定义 MemoryItemRepository 接口（抽象基类）
        - 定义 VectorStoreRepository 接口（抽象基类）
        - 实现 SQLAlchemyMemoryItemRepository（继承自抽象基类）
        - 实现 SQLAlchemyVectorStoreRepository（集成 PGVector）
        - 实现 CRUD 操作（创建、查询、更新、删除）
        - 实现按用户 ID 查询方法（getByUserId）
        - 实现按类型查询方法（getByType）
        - 实现按标签查询方法（getByTags，支持多标签 OR/AND 查询）
        - 实现分页查询方法（getPageMemories，支持多种排序策略）
        - 实现去重查询方法（findByDedupeHash）
        - 实现向量存储和检索方法（similaritySearchWithScore）
        - 实现向量索引优化方法（createIndex，支持 ivfflat/HNSW）
        - 实现批量操作方法（batchInsert、batchDelete）

- [ ] 1.5 实现记忆领域服务
     【目标对象】`app/domain/memory/service.py`
     【修改目的】封装记忆相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】MemoryItemRepository, VectorStoreRepository
     【修改内容】
        - 实现记忆保存业务逻辑（包含去重、合并）
        - 实现记忆查询业务逻辑
        - 实现记忆删除业务逻辑（软删除）
        - 实现记忆检索业务逻辑
        - 实现记忆重要性评估
        - 实现记忆去重逻辑
        - 实现记忆合并逻辑

- [ ] 1.6 实现记忆提取服务
     【目标对象】`app/domain/memory/service.py`
     【修改目的】从对话中自动提取记忆
     【修改方式】使用 LLM + Prompt 工程自动提取
     【相关依赖】LLMDomainService, OpenAI API/Sentence Transformers
     【修改内容】
        - 实现 MemoryExtractorService 核心类
        - 设计结构化的 System Prompt 模板（包含类型定义、不抽取判定、提取规则、输出格式、示例说明）
        - 实现 Prompt 模板版本管理（当前版本：v1.0）
        - 实现从对话上下文中提取候选记忆（支持最近 3 轮历史增强）
        - 实现记忆重要性打分（基于稳定性、复用频率、个性化程度、时间敏感性四个维度）
        - 实现记忆类型分类（PROFILE/TASK/FACT/EPISODIC）
        - 实现记忆过滤（基于重要性阈值：≥0.8 入库，EPISODIC≥0.9）
        - 实现记忆标签生成（自动提取关键词作为标签）
        - 实现记忆去重哈希生成（文本标准化+SHA-256）
        - 实现隐私信息识别与过滤（正则+LLM 双重机制）
        - 实现失败重试机制（最多 2 次，指数退避：1s、2s）
        - 实现频率限制（单用户每分钟最多 5 次抽取）
        - 实现 Token 成本控制（单次最多输出 3 条记忆）

- [ ] 1.7 实现向量存储和检索
     【目标对象】`app/domain/memory/repository.py`
     【修改目的】提供记忆向量化存储和检索
     【修改方式】集成 PGVector 向量数据库
     【相关依赖】pgvector 0.5+, OpenAI Embeddings API/Sentence Transformers
     【修改内容】
        - 实现文本向量化（调用 OpenAI Embeddings API 或本地 Sentence Transformers）
        - 实现向量存储（PGVector 的 vector 类型，1536 维或 384 维）
        - 实现相似度检索（余弦相似度，支持 ivfflat 索引加速）
        - 实现向量索引和优化（CREATE INDEX，ivfflat lists=100 或 HNSW m=16）
        - 实现批量向量化和存储（batch_size=10，减少 API 调用）
        - 实现并发度控制（最大并行嵌入数=3，避免网络拥塞）
        - 实现召回率优化（初筛召回加倍，后续加权筛选）
        - 实现最低相似度阈值过滤（默认 0.3，可配置）
        - 实现 HNSW 高级索引选项（适用于万级以上数据，召回率>98%）
        - 实现索引重建任务（每月自动重建一次，优化性能）

- [ ] 1.8 实现记忆应用服务层
     【目标对象】`app/application/memory/`
     【修改目的】编排记忆相关的用例
     【修改方式】实现应用服务
     【相关依赖】MemoryDomainService, MemoryExtractorService
     【修改内容】
        - 实现 MemoryAppService（记忆管理）
        - 实现分页列出用户记忆方法（listUserMemories）
        - 实现手动创建记忆方法（createMemory）
        - 实现归档记忆方法（deleteMemory - 软删除）
        - 实现自动提取和保存记忆方法（extractAndSaveMemories）
        - 实现记忆检索方法（searchMemories）
        - 实现记忆查询方法（getMemoryById）

- [ ] 1.9 实现记忆转换器
     【目标对象】`app/application/memory/`
     【修改目的】实现实体与 DTO 之间的转换
     【修改方式】实现 Assembler 模式
     【相关依赖】MemoryItem 模型, MemoryItemDTO, CandidateMemory
     【修改内容】
        - 创建 MemoryAssembler
        - 实现 toDTO 方法（从实体转换为 DTO）
        - 实现 toDTOs 方法（批量转换）
        - 创建 MemoryCommandAssembler
        - 实现 toCandidate 方法（从请求转换为候选记忆）

- [ ] 1.10 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/memory/`
     【修改目的】暴露记忆相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】MemoryAppService
     【修改内容】
        - `POST /api/v1/memories` - 手动创建记忆
        - `GET /api/v1/memories` - 分页列出用户记忆
        - `GET /api/v1/memories/{itemId}` - 获取记忆详情
        - `PUT /api/v1/memories/{itemId}` - 更新记忆
        - `DELETE /api/v1/memories/{itemId}` - 归档（软删除）记忆
        - `GET /api/v1/memories/search` - 搜索记忆

- [ ] 1.11 实现记忆提取触发机制
     【目标对象】`app/application/memory/`
     【修改目的】在对话结束后自动提取记忆
     【修改方式】集成对话事件监听
     【相关依赖】ConversationEventListener
     【修改内容】
        - 实现对话完成事件监听器
        - 调用 MemoryExtractorService 提取记忆
        - 调用 MemoryDomainService 保存记忆
        - 实现异步处理机制

- [ ] 1.12 实现记忆去重和合并策略
     【目标对象】`app/domain/memory/service.py`
     【修改目的】避免记忆重复存储
     【修改方式】实现语义哈希 + 数据库索引双重去重
     【相关依赖】MemoryItemRepository, hashlib(SHA-256)
     【修改内容】
        - 实现基于语义哈希的去重（文本标准化+SHA-256）
        - 实现有记忆对比（importance、tags、data、text 多维度对比）
        - 实现记忆合并策略：
           * importance 取最大值
           * tags 合并并去重
           * data 智能合并（相同 key 保留新值，不同 key 合并）
           * text 选择文本更丰富的版本（字符数更多）
        - 实现记忆重要性加权（合并时重新评估，取 max(旧值，新值)）
        - 实现记忆去重哈希优化（数据库唯一索引加速查询）
        - 实现相似度阈值调优（默认 0.95，支持动态调整）
        - 实现去重准确率测试基准（目标准确率>95%）

- [ ] 1.13 编写单元测试
     【目标对象】`tests/test_memory_service.py`
     【修改目的】确保记忆管理功能正确性
     【修改方式】使用 pytest + pytest-asyncio
     【相关依赖】MemoryAppService, pytest
     【修改内容】
        - 测试记忆创建（正常场景、边界场景、异常场景）
        - 测试记忆查询（按 ID、按类型、按标签、分页）
        - 测试记忆更新（文本、重要性、标签）
        - 测试记忆删除（软删除、物理删除）
        - 测试记忆提取（Prompt 有效性、阈值过滤、类型分类）
        - 测试记忆去重（哈希碰撞、相似度阈值）
        - 测试记忆检索（向量相似度、加权排序、Top-K 截取）
        - 测试记忆重要性评估（评分一致性、分布合理性）
        - 测试隐私过滤（敏感信息识别、匿名化处理）
        - 测试容量限制（超限归档、降级策略）
        - 测试并发处理（异步任务、任务队列）
        - 测试失败重试（重试次数、退避间隔）

- [ ] 1.14 编写集成测试
     【目标对象】`tests/integration/test_memory_api.py`
     【修改目的】确保记忆 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient + PostgreSQL 测试容器
     【相关依赖】FastAPI, MemoryAppService, pytest, testcontainers
     【修改内容】
        - 测试记忆创建 API（权限校验、参数验证、响应格式）
        - 测试记忆查询 API（分页、过滤、排序）
        - 测试记忆更新 API（部分更新、全量更新）
        - 测试记忆删除 API（软删除、物理删除）
        - 测试记忆搜索 API（关键词搜索、语义搜索）
        - 测试分页查询 API（页边界、空结果）
        - 测试向量相似度检索（召回率、准确率）
        - 测试去重准确率（重复输入、相似输入）
        - 测试重要性评分一致性（多次调用稳定性）
        - 测试隐私过滤有效性（敏感信息拦截率）
        - 测试性能基准（检索延迟、吞吐量）
        - 测试多租户隔离（跨用户访问拦截）

- [ ] 1.15 实现记忆缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提高记忆查询性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 实现记忆记录缓存装饰器
        - 实现向量检索结果缓存
        - 实现缓存过期和刷新策略（TTL=30 分钟，LRU 淘汰）
        - 实现缓存穿透保护（布隆过滤器或空值缓存）
        - 实现缓存预热（热门记忆主动加载）

- [ ] 1.18 实现用户可控的记忆管理
     【目标对象】`app/api/v1/memory/`
     【修改目的】增强用户对记忆的控制能力
     【修改方式】新增 RESTful API 接口
     【相关依赖】MemoryAppService
     【修改内容】
        - 实现手动编辑记忆 API（PUT /memories/{id}，修改文本、调整重要性、增删标签）
        - 实现批量导出 API（GET /memories/export，导出用户全部记忆为 JSON）
        - 实现批量导入 API（POST /memories/import，从 JSON 文件导入记忆）
        - 实现一键归档 API（POST /memories/archive-low-importance，归档所有重要性<0.6 的记忆）
        - 实现物理删除 API（DELETE /memories/{id}/permanent，GDPR 被遗忘权，需二次确认）
        - 实现记忆统计 API（GET /memories/statistics，返回各类统计数据）
        - 实现容量预警 API（GET /memories/capacity-warning，返回当前使用量和剩余容量）

- [ ] 1.16 实现记忆统计和分析
     【目标对象】`app/application/memory/`
     【修改目的】提供记忆使用分析功能
     【修改方式】实现统计服务，支持可视化数据输出
     【相关依赖】MemoryItemRepository, Pandas(可选)
     【修改内容】
        - 实现按用户统计记忆数量（总数、活跃数、归档数）
        - 实现按类型统计记忆分布（PROFILE/TASK/FACT/EPISODIC 占比）
        - 实现记忆时效性分析（平均存活时间、半衰期）
        - 实现记忆重要性分布分析（0-0.3/0.3-0.6/0.6-0.9/0.9+ 分段统计）
        - 实现记忆使用频率统计（被检索次数、注入上下文次数）
        - 实现异常记忆检测（低质量抽取、重复率高）
        - 实现清理任务建议（长期未使用、低重要性记忆）
        - 实现容量趋势预测（基于增长速度预测超限时间）

- [ ] 1.17 实现记忆批量操作
     【目标对象】`app/domain/memory/service.py`
     【修改目的】提高记忆处理效率
     【修改方式】实现批量操作，优化并发处理
     【相关依赖】MemoryItemRepository, VectorStoreRepository, asyncio
     【修改内容】
        - 实现批量保存记忆（事务性保证原子性）
        - 实现批量向量化（batch_size=10，减少 API 调用次数）
        - 实现批量删除记忆（软删除 + 物理删除）
        - 实现批量检索记忆（并行向量检索）
        - 实现批量更新记忆状态（归档、恢复）
        - 实现并发度控制（信号量限制最大并行数=3）
        - 实现失败回滚机制（部分失败时全部回滚）
