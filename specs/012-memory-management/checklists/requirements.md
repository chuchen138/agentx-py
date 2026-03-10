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
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 MemoryItemRepository 接口
        - 定义 VectorStoreRepository 接口
        - 实现 SQLAlchemy MemoryItemRepository
        - 实现 SQLAlchemy VectorStoreRepository
        - 实现 CRUD 操作（创建、查询、更新、删除）
        - 实现按用户ID查询方法（getByUserId）
        - 实现按类型查询方法（getByType）
        - 实现按标签查询方法（getByTags）
        - 实现分页查询方法（getPageMemories）
        - 实现去重查询方法（findByDedupeHash）
        - 实现向量存储和检索方法

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
     【修改方式】使用 LLM 自动提取
     【相关依赖】LLMDomainService, OpenAI API
     【修改内容】
        - 实现 MemoryExtractorService
        - 实现从对话上下文中提取候选记忆
        - 实现记忆重要性打分
        - 实现记忆类型分类
        - 实现记忆过滤（基于重要性阈值）
        - 实现记忆标签生成
        - 实现记忆去重哈希生成

- [ ] 1.7 实现向量存储和检索
     【目标对象】`app/domain/memory/repository.py`
     【修改目的】提供记忆向量化存储和检索
     【修改方式】集成向量数据库
     【相关依赖】pgvector 或其他向量数据库, OpenAI Embeddings API
     【修改内容】
        - 实现文本向量化（调用 Embeddings API）
        - 实现向量存储
        - 实现相似度检索
        - 实现向量索引和优化
        - 实现批量向量化和存储

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
     【修改方式】实现去重和合并逻辑
     【相关依赖】MemoryItemRepository
     【修改内容】
        - 实现基于语义哈希的去重
        - 实现有记忆对比
        - 实现记忆合并策略
        - 实现记忆重要性加权
        - 实现记忆去重哈希优化

- [ ] 1.13 编写单元测试
     【目标对象】`tests/test_memory_service.py`
     【修改目的】确保记忆管理功能正确性
     【修改方式】使用 pytest
     【相关依赖】MemoryAppService
     【修改内容】
        - 测试记忆创建
        - 测试记忆查询
        - 测试记忆更新
        - 测试记忆删除（软删除）
        - 测试记忆提取
        - 测试记忆去重
        - 测试记忆检索
        - 测试记忆重要性评估

- [ ] 1.14 编写集成测试
     【目标对象】`tests/integration/test_memory_api.py`
     【修改目的】确保记忆 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, MemoryAppService
     【修改内容】
        - 测试记忆创建 API
        - 测试记忆查询 API
        - 测试记忆更新 API
        - 测试记忆删除 API
        - 测试记忆搜索 API
        - 测试分页查询 API

- [ ] 1.15 实现记忆缓存策略
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提高记忆查询性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 实现记忆记录缓存装饰器
        - 实现向量检索结果缓存
        - 实现缓存过期和刷新策略
        - 实现缓存穿透保护

- [ ] 1.16 实现记忆统计和分析
     【目标对象】`app/application/memory/`
     【修改目的】提供记忆使用分析功能
     【修改方式】实现统计服务
     【相关依赖】MemoryItemRepository
     【修改内容】
        - 实现按用户统计记忆数量
        - 实现按类型统计记忆分布
        - 实现记忆时效性分析
        - 实现记忆重要性分布分析
        - 实现记忆使用频率统计

- [ ] 1.17 实现记忆批量操作
     【目标对象】`app/domain/memory/service.py`
     【修改目的】提高记忆处理效率
     【修改方式】实现批量操作
     【相关依赖】MemoryItemRepository, VectorStoreRepository
     【修改内容】
        - 实现批量保存记忆
        - 实现批量向量化
        - 实现批量删除记忆
        - 实现批量检索记忆
        - 实现批量更新记忆状态
