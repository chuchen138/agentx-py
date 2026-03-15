# 记忆管理（Memory Management）技术设计

## 技术架构

### 整体架构

记忆管理模块采用分层架构设计，遵循领域驱动设计（DDD）原则。接口层提供 RESTful API，包含 MemoryController 和 DTO（MemoryItemDTO、MemoryResult）。应用层包含 MemoryAppService 和 Assemblers（MemoryAssembler、MemoryCommandAssembler），负责编排领域服务和事务管理。领域层包含 MemoryDomainService、MemoryExtractorService、领域模型（MemoryItem、CandidateMemory）、仓储接口和常量定义。基础设施层包含记忆仓储实现（SQLAlchemyRepository）、向量存储实现（PGVectorRepository）、嵌入模型集成（OpenAI/Sentence Transformers）和数据库实体（memory_items 表、memory_vector_store 表）。

### 组件层次

**接口层**：提供对外 RESTful API 接口，包括查询记忆列表、手动创建记忆、编辑记忆、归档/删除记忆、搜索记忆、批量导出/导入。数据传输对象包含 MemoryItemDTO（记忆条目）、MemoryResult（检索结果）、CreateMemoryRequest（创建请求）、QueryMemoryRequest（查询请求）。

**应用层**：提供用例编排服务，包括分页查询用户记忆（支持类型/标签过滤）、手动创建记忆（含参数校验）、归档删除记忆（软删除+ 物理删除）、实体与 DTO 转换（双向）、命令对象转换（Request→Domain）、记忆统计（按类型/重要性/时间分布）、容量预警（使用量/剩余量计算）。

**领域层**：
- MemoryDomainService：核心领域服务，提供保存记忆（包含去重/合并 + 向量入库）、记忆检索（相似度 + 重要性加权）、查询记忆列表（分页 + 过滤）、归档记忆（状态变更）、批量操作（事务性保证）。
- MemoryExtractorService：记忆抽取服务，异步抽取并持久化、从用户消息中抽取候选记忆（基于 Prompt 工程）、重要性评分（四维评估）、类型分类、隐私过滤、失败重试、频率限制。
- 领域模型：MemoryItemEntity（记忆条目实体）、CandidateMemory（候选记忆）、MemoryResult（检索结果）、MemoryType 枚举（PROFILE/TASK/FACT/EPISODIC）。
- 仓储接口：MemoryItemRepository（CRUD+ 自定义查询）、VectorStoreRepository（向量存储与检索）。
- 常量定义：MemoryMetadataConstant（向量元数据键名）、MemoryThresholdConstant（阈值配置）。

**基础设施层**：
- 记忆仓储实现：SQLAlchemyMemoryItemRepository（基于 SQLAlchemy 2.0 ORM）。
- 向量存储实现：PGVectorRepository（基于 pgvector 0.5+ 扩展，支持 ivfflat/HNSW 索引）。
- 嵌入模型集成：OpenAIEmbeddingAdapter（兼容 OpenAI API）、SentenceTransformerAdapter（本地部署）。
- 数据库：PostgreSQL 14+ with pgvector 扩展，包含 memory_items 表和 memory_vector_store 表。

### 技术栈选型

**向量数据库**：PGVector 0.5+
- 理由：与现有 PostgreSQL 无缝集成，无需额外部署
- 性能基准：单用户<1000 条记忆时，Top-16 检索延迟<300ms
- Python 客户端：SQLAlchemy 2.0+ ORM + psycopg2-binary 驱动

**嵌入模型**：双模支持
- 云服务：OpenAI Embeddings（text-embedding-3-small，1536 维，<500ms/条）
- 本地部署：Sentence Transformers（bge-large-zh，1024 维，<100ms/条，CPU 可运行）

**ORM 框架**：SQLAlchemy 2.0+
- 特性：异步支持、类型安全、优雅的分页和过滤语法

**缓存层**：Redis 7.0+
- 用途：缓存热门记忆、向量检索结果、任务队列缓冲
- 策略：TTL=30 分钟，LRU 淘汰，布隆过滤器防穿透

## 向量存储策略

**向量化流程**：
1. 文本标准化处理（合并多行、合并空白、去除首尾、转小写）
2. 嵌入模型生成向量（调用 OpenAI API 或本地 Sentence Transformers）
3. 构建文本段加元数据（user_id、item_id、type、tags、status）
4. 写入 PGVector 向量存储（vector 字段，1536 维或 1024 维）

**嵌入模型配置**：
- 使用用户专属的嵌入模型配置，通过 UserModelConfigResolver 解析
- 支持动态切换：OpenAIEmbeddingFactory / SentenceTransformerFactory
- 每个用户使用独立的嵌入模型配置，避免交叉污染

**向量元数据**（存储在 PGVector 的 metadata JSONB 字段）：
- user_id：归属用户 ID（用于检索时的 WHERE 过滤）
- item_id：记忆条目 ID（关联业务数据，JOIN 查询）
- type：记忆类型（PROFILE/TASK/FACT/EPISODIC，支持类型过滤）
- tags：标签列表（数组类型，支持 ANY/ALL 查询）
- status：状态（1=active，0=archived，默认 1）
- created_at：创建时间戳（用于时效性排序）

**索引策略**：
- ivfflat 索引：适用于万级以下数据，lists=100，召回率>95%，建索引快
- HNSW 索引：适用于大规模场景，m=16，ef_construction=64，召回率>98%，查询更快
- 索引重建：每月自动重建一次（REINDEX），优化碎片和性能

## 相似度算法与检索优化

**检索流程**：
1. 查询文本向量化（使用相同的嵌入模型）
2. 向量相似度检索（PGVector 的 cosine_distance 函数）
3. 元数据过滤（WHERE user_id = ? AND status = 1）
4. 计算加权和（score = 0.7 * similarity + 0.3 * importance）
5. 排序并截取 Top-K（ORDER BY score DESC LIMIT k）

**相似度计算**：
- 余弦相似度：cosine_similarity = 1 - cosine_distance
- 最低阈值：默认 0.3（低于此值认为不相关）
- 召回策略：初筛召回数量加倍（Top-2N），后续加权筛选取 Top-N

**最终评分公式**：
```
score = (similarity_weight * similarity_score) + (importance_weight * importance_score)
similarity_weight = 0.7（默认，可配置）
importance_weight = 0.3（默认，可配置）
similarity_score ∈ [0, 1]（归一化后的相似度）
importance_score ∈ [0, 1]（记忆的重要性评分）
```

**高级索引选项**：
- ivfflat：适合万级以下数据，lists 参数建议为数据量的 1/10
- HNSW：适合大规模场景，m=16（连接数），ef_search=64（搜索深度）
- 性能对比：ivfflat 在 1 万条数据下 Top-16 检索约 200ms；HNSW 约 100ms

**召回率优化**：
- 候选加倍：初次检索返回 Top-32，后续加权排序取 Top-16
- 状态过滤：在数据库层面过滤 archived 状态，减少无效计算
- 类型加权：对 PROFILE 和 FACT 类型给予额外 +0.05 加分（可配置）

## 记忆提取与 Prompt 工程

**触发时机**：每轮对话结束后自动触发（异步处理，不影响主响应）

**抽取模型**：使用用户默认的聊天模型（ChatModel），通过 LLMProviderService.getStrand() 获取，支持 OpenAI GPT-4/GPT-3.5、Anthropic Claude、本地 Ollama 等多种协议。

**Prompt 模板结构**（版本：v1.0）：
1. **角色定义**：你是专业的记忆抽取助手，擅长从对话中提取有价值的长期记忆
2. **类型定义**：详细说明四种记忆类型（PROFILE/TASK/FACT/EPISODIC）及其含义和示例
3. **不抽取判定**：明确列出不应抽取的内容（一次性操作、临时数据、隐私敏感信息）
4. **提取规则**：说明重要性评分标准（0.0-1.0，保留两位小数）和提取阈值（≥0.8 入库，EPISODIC≥0.9）
5. **输出格式**：指定 XML 格式输出要求（包含<memories>根元素，<memory>子元素包含 type、text、importance、tags）
6. **示例说明**：提供 3-5 个典型示例（正例 + 反例），确保理解一致性

**Prompt 版本控制**：
- 当前版本：v1.0（硬编码在代码中）
- 未来规划：支持数据库存储 Prompt 模板，热更新无需重启

**XML 解析**：使用 Python 标准库 xml.etree.ElementTree 解析 LLM 返回的 XML 格式，提取记忆类型、文本、重要性、标签，生成 CandidateMemory 列表。解析失败时记录错误日志并丢弃该批次。

**抽取阈值**：
- 基本阈值：importance ≥ 0.8（PROFILE/TASK/FACT）
- EPISODIC 阈值：importance ≥ 0.9（更严格，因为情景信息容易过载）
- 输出数量限制：最多输出 1-3 条最高价值要点（防止 Token 爆炸）

**失败重试机制**：
- 重试次数：最多 2 次
- 退避策略：指数退避（第一次间隔 1s，第二次间隔 2s）
- 降级策略：连续失败 3 次后放弃本次抽取，记录告警日志

**频率限制**：单用户每分钟最多触发 5 次抽取，通过 Redis 计数器实现（key: memory:extract:{user_id}，TTL=60s）

## 去重与合并策略

**去重机制**（三重保障）：
1. **文本标准化**：
   - 合并多行为一行（\n → 空格）
   - 合并连续空白（多个空格 → 单个空格）
   - 去除首尾空白
   - 全部转小写（中文无影响，英文统一）
2. **哈希生成**：使用 SHA-256 算法生成语义哈希（64 字符十六进制）
3. **数据库查询**：根据 user_id + dedupe_hash 查询唯一索引，时间复杂度 O(1)

**相似度去重补充**：
- 对于语义相似但文本不完全相同的情况，使用向量相似度检测
- 相似度阈值：默认 0.95（可根据实际情况调优）
- 检测时机：在哈希去重之后，作为第二道防线

**合并策略**（当检测到重复或高度相似记忆时）：
- **importance**：取最大值（max(旧值，新值)），确保重要性不被低估
- **tags**：合并并去重（Python set union），保留所有标签
- **data**：智能合并（相同 key 保留新值，不同 key 合并），JSON Merge Patch
- **text**：选择文本更丰富的版本（字符数更多，信息量更大）
- **updated_at**：更新时间戳设为当前时间

**合并示例**：
- 旧记忆："主要编程语言是 Python"，importance=0.85，tags=["技能"]
- 新记忆："主要编程语言是 Python 和 Java"，importance=0.9，tags=["技能", "多语言"]
- 合并后："主要编程语言是 Python 和 Java"，importance=0.9，tags=["技能", "多语言"]

**数据库索引优化**：
- 唯一索引：UNIQUE INDEX idx_user_dedupe ON memory_items(user_id, dedupe_hash)
- 加速查询：CREATE INDEX idx_type_status ON memory_items(type, status)

## 数据模型与表结构

**memory_items 表**（记忆条目主表）：
- id：UUID 主键，主键索引
- user_id：VARCHAR(64)，归属用户 ID，普通索引
- type：VARCHAR(20)，记忆类型（PROFILE/TASK/FACT/EPISODIC），普通索引
- text：TEXT，记忆文本内容（最大 5000 字符）
- data：JSONB，额外结构化数据（最大 10KB）
- importance：FLOAT，重要性评分（0.0-1.0，保留两位小数）
- tags：ARRAY(TEXT)，标签列表（最多 10 个）
- source_session_id：VARCHAR(64)，来源会话 ID，用于审计追踪
- dedupe_hash：CHAR(64)，去重 SHA-256 哈希值，唯一索引
- status：SMALLINT，状态（1=active，0=archived，默认 1）
- created_at：TIMESTAMP，创建时间戳，默认 CURRENT_TIMESTAMP
- updated_at：TIMESTAMP，更新时间戳，ON UPDATE CURRENT_TIMESTAMP
- deleted_at：TIMESTAMP，删除时间戳（软删除时使用，NULL 表示未删除）

**memory_vector_store 表**（向量存储表，使用 PGVector 扩展）：
- embedding_id：UUID 主键，主键索引
- item_id：UUID，关联 memory_items.id，外键索引
- embedding：VECTOR(1536)，嵌入向量（OpenAI 1536 维，本地模型可能是 384 或 1024）
- text：TEXT，冗余文本字段，便于独立查询
- metadata：JSONB，元数据（包含 user_id、type、tags、status 等）
- created_at：TIMESTAMP，创建时间戳

**索引设计**：
- PRIMARY KEY (id)：主键索引
- UNIQUE INDEX idx_user_dedupe (user_id, dedupe_hash)：去重唯一索引
- INDEX idx_type_status (type, status)：类型 + 状态组合索引
- INDEX idx_user_type (user_id, type)：用户 + 类型组合索引
- INDEX idx_tags (tags USING GIN)：标签 GIN 索引（支持数组查询）
- INDEX idx_embedding (embedding USING ivfflat WITH (lists=100))：向量索引

**扩展字段设计**：
- data 字段采用 JSONB 格式，支持灵活扩展（如：{"project": "AgentX", "priority": "high"}）
- 支持动态添加新字段而无需修改表结构
- 查询时使用 JSONB 操作符（->、->>、?）

## 核心流程详解

**保存记忆流程**（含去重/合并/向量化）：
1. 接收候选记忆列表（CandidateMemory[]）
2. 遍历每个候选记忆：
   a. 文本标准化（合并行、并空白、去首尾、转小写）
   b. 生成去重哈希（SHA-256）
   c. 根据 user_id + dedupe_hash 查询数据库
   d. 存在则执行合并逻辑（update importance=max(旧，新), tags=union, data=merge）
   e. 不存在则新增插入（insert into memory_items）
   f. 构建向量元数据（user_id、item_id、type、tags、status）
   g. 调用嵌入模型生成向量（1536 维或 1024 维）
   h. 写入向量存储（insert into memory_vector_store）
3. 返回保存结果（成功数量、失败数量、详情列表）

**记忆检索流程**（相似度 + 重要性加权）：
1. 接收查询字符串 query 和用户 ID user_id
2. 调用嵌入模型将 query 转换为向量
3. PGVector 执行相似度检索：
   ```sql
   SELECT item_id, metadata, 1 - (embedding <=> :query_vector) AS similarity
   FROM memory_vector_store
   WHERE metadata->>'user_id' = :user_id
     AND metadata->>'status' = '1'
     AND 1 - (embedding <=> :query_vector) >= 0.3
   ORDER BY similarity DESC
   LIMIT 32  -- 候选加倍
   ```
4. JOIN memory_items 表获取完整信息（importance、type、tags）
5. 计算加权评分：score = 0.7 * similarity + 0.3 * importance
6. 按 score 降序排序，截取 Top-K（默认 Top-16）
7. 返回检索结果（MemoryResult[]，包含 itemId、text、score、importance 等）

**记忆抽取流程**（异步 + 重试）：
1. 对话结束事件触发（ConversationCompletedEvent）
2. 构建抽取请求（用户消息 + 最近 3 轮历史）
3. 异步提交任务到线程池（max_workers=5）
4. 调用 LLM 抽取服务（System Prompt v1.0）
5. 解析 XML 响应，生成候选记忆列表
6. 调用 MemoryDomainService.saveMemories()
7. 失败时自动重试（最多 2 次，间隔 1s、2s）
8. 连续失败 3 次后记录告警日志并放弃

## 扩展性设计

**新增记忆类型**：
1. 在 MemoryType 枚举中添加新类型（如 COGNITIVE：认知类记忆）
2. 更新抽取 Prompt 的类型定义部分，说明新类型的含义和示例
3. 更新检索过滤逻辑，支持按新类型筛选
4. 可选：为新类型配置不同的提取阈值（如 COGNITIVE 需≥0.85）

**新增向量存储后端**：
1. 定义统一的 VectorStore 接口（add、search、delete 方法）
2. 实现 PGVectorAdapter（已实现）
3. 实现 ChromaAdapter、MilvusAdapter、WeaviateAdapter（按需扩展）
4. 通过配置文件切换实现（vector_store.type=pgvector/chroma/milvus）
5. 支持热切换，无需重启服务

**新增抽取模型**：
1. 实现 MemoryExtractor 接口（extract 方法）
2. 支持自定义 Prompt 模板（从配置文件或数据库加载）
3. 支持多种 LLM 协议（OpenAI、Claude、Ollama、自部署）
4. 通过工厂模式动态创建（ExtractorFactory.create(provider)）

**元数据扩展**：
1. data 字段采用 JSONB，支持任意结构化扩展
2. 新增字段无需修改表结构（如：{"source": "chat", "language": "zh-CN"}）
3. 查询时使用 JSONB 操作符（WHERE data->>'source' = 'chat'）

**插件化架构**：
1. 定义 MemoryExtractorPlugin 接口（preExtract、postExtract 钩子）
2. 支持自定义插件注入（如：添加领域特定的过滤规则）
3. 通过依赖注入容器管理插件生命周期

## 性能优化策略

**向量化优化**：
- 批量嵌入：batch_size=10，减少 API 调用次数（10 条变 1 次）
- 异步处理：使用 asyncio.gather 并发向量化，提升吞吐量
- 连接池：psycopg2 连接池大小=20，避免频繁创建连接
- 本地缓存：对相同文本缓存向量结果（Redis，TTL=24h）

**检索优化**：
- 候选加倍：初筛 Top-32，加权后 Top-16，提升召回率
- 状态过滤：WHERE 条件直接过滤 archived，减少无效数据
- 索引优化：定期 REINDEX 重建索引，优化碎片（每月一次）
- 覆盖索引：SELECT 只取必要字段，避免回表查询
- 向量索引调优：ivfflat lists=数据量/10，HNSW m=16、ef_search=64

**去重优化**：
- 哈希去重：数据库唯一索引，O(1) 时间复杂度
- 缓存结果：对常见文本缓存 dedupe_hash（Redis，TTL=1h）
- 预计算：在抽取阶段并行计算哈希，减少数据库查询

**并发控制**：
- 信号量：限制最大并行嵌入数=3（asyncio.Semaphore(3)）
- 任务队列：Redis List 作为缓冲，削峰填谷
- 超时控制：单次向量化超时=10s，防止长时间阻塞

**容量优化**：
- 自动归档：当用户记忆>1200 条时，自动归档重要性<0.6 的旧记忆
- 分级存储：高重要性常驻内存，低重要性冷存储
- 压缩存储：对长文本使用 LZ77 压缩（可选）

## 安全、监控与合规

**数据隔离**：
- 用户 ID 强制过滤：所有查询必须包含 WHERE user_id = ?
- 向量存储过滤：PGVector 的 metadata 中包含 user_id，检索时双重过滤
- 权限校验：JWT 鉴权后，细粒度校验资源归属（防止越权）

**数据加密**：
- HTTPS 传输加密：所有 API 请求强制 TLS 1.3
- 敏感字段加密：data 字段可选 AES-256 加密存储（通过@Encrypted 注解）
- 密钥管理：使用 AWS KMS 或 HashiCorp Vault 管理加密密钥

**访问控制**：
- 用户鉴权：基于 JWT 的身份认证（有效期 24h）
- 操作审计：所有写操作记录审计日志（谁、何时、做了什么）
- 速率限制：单用户每秒最多 10 次记忆 API 请求（Redis 计数器实现）

**隐私保护**：
- 匿名化处理：精确地址→城市级（上海市浦东新区→上海）
- 脱敏处理：手机号中间四位替换为*号（138****5678）
- 可配置删除策略：软删除默认保留 30 天，超期自动物理清理
- GDPR 被遗忘权：支持彻底物理删除（需二次确认 + 密码验证）

**SQL 注入防护**：
- ORM 参数化查询：使用 SQLAlchemy 的 bind parameter
- 禁止字符串拼接：所有动态条件使用表达式树

**监控指标**（Prometheus + Grafana）：
- 记忆保存成功率：目标>99%（失败时告警）
- 记忆检索成功率：目标>99.5%
- 向量嵌入成功率：目标>98%（排除网络波动）
- 抽取模型调用成功率：目标>95%
- 检索平均响应时间：P95 < 500ms，P99 < 800ms
- 抽取平均响应时间：P95 < 5s（含 LLM 调用）
- 存储内存使用量：单用户<10MB（1000 条记忆）
- 向量索引大小：单用户<50MB（1536 维，FP32）
- 重复记忆检测准确率：目标>95%（抽样人工审核）
- 相似度分布统计：记录每日相似度均值、分位数

**告警规则**（AlertManager）：
- 保存失败率>5%（5 分钟窗口）→ P1 告警
- 检索失败率>2%（5 分钟窗口）→ P1 告警
- 抽取模型调用失败>10 次/小时 → P2 告警
- 向量存储异常（连接失败、写入失败）→ P0 告警
- 重复率异常（>30% 的记忆重复）→ P3 告警（提示优化 Prompt）
- 检索延迟 P95 > 1s → P2 告警（提示优化索引）

## 与其他模块的集成

**与会话上下文模块（011）集成**：
- 注入时机：每次对话开始时，自动检索 Top-5 相关记忆注入上下文
- 触发条件：用户消息与记忆相似度>0.85 时，主动提示"您之前提到过..."
- 冲突处理：当记忆与当前上下文矛盾时，以最新信息为准；高重要性记忆（≥0.9）需用户确认是否更新
- API 调用：ConversationService 调用 MemoryService.searchMemories(query=userMessage, topK=5)

**与对话管理模块（013）集成**：
- 抽取触发：对话结束时触发 MemoryService.extractAndSaveMemories()
- 上下文传递：传递最近 3 轮对话历史，增强抽取准确性
- 异步处理：抽取任务异步执行，不阻塞对话响应

**与执行追踪模块（016）集成**：
- 审计日志：记忆操作（创建/更新/删除）记录 TraceLog
- 性能追踪：记录抽取耗时、检索耗时、向量化耗时
- 错误追踪：抽取失败、向量化失败记录详细错误堆栈

**与用户管理模块（001）集成**：
- 用户配置：读取用户的嵌入模型配置（openai/local）
- 多租户隔离：通过 user_id 实现严格的数据隔离
- 用户注销：用户注销时自动归档所有记忆（可选物理删除）
