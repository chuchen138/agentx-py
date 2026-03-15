# RAG 管理技术设计

## 概述

RAG 管理模块采用领域驱动设计（DDD）架构，提供文档处理、向量化、混合检索和会话对话等核心能力。

## 技术架构

### 架构分层

### 架构分层

系统采用四层架构：
- **API 层**：使用 FastAPI 处理 HTTP 请求和 WebSocket 连接
- **应用层**：协调领域服务，包含数据集管理、文件操作、检索服务、发布审核和市场管理
- **领域层**：封装核心业务逻辑，包含检索服务、增强服务、管理服务和状态机服务
- **基础设施层**：对接向量存储（PGVector/Milvus）、数据库（PostgreSQL）、消息队列（RabbitMQ/Redis）和文件存储（MinIO/S3）

### 技术栈

### 技术栈

- **Web 框架**：FastAPI
- **ORM**：SQLAlchemy + AsyncSession
- **向量处理**：LangChain / LlamaIndex / Haystack
- **向量存储**：PGVector (psycopg2) / Milvus / Chroma
- **数据库**：PostgreSQL
- **消息队列**：RabbitMQ (pika) / Redis (celery)
- **文件存储**：本地文件系统 / MinIO / S3
- **OCR**：Tesseract (pytesseract) / EasyOCR
- **文档处理**：pypdf, python-docx, markdown
- **任务调度**：Celery / APScheduler

## 核心设计

### 文件处理状态机

文档处理采用状态机模式，状态包括：
- **UPLOADED**（已上传）
- **OCR_PROCESSING**（OCR 处理中）
- **OCR_COMPLETED**（OCR 处理完成）
- **EMBEDDING_PROCESSING**（向量化处理中）
- **COMPLETED**（处理完成）
- **OCR_FAILED**（OCR 处理失败）
- **EMBEDDING_FAILED**（向量化失败）

文档从上传开始，依次经过 OCR 处理和向量化处理，任何步骤失败都会进入对应失败状态，支持重试。采用状态模式，每个状态对应一个独立处理器（StateProcessor），状态转换由事件驱动。使用 SQLAlchemy 持久化状态变化。

### 向量存储设计

使用 LangChain 的 VectorStore 接口或 LlamaIndex 的 VectorStoreIndex 抽象向量存储，支持 PGVector、Milvus、Chroma 等多种向量数据库后端。

**向量元数据设计：**
每个向量片段携带丰富的元数据用于过滤和检索：
- `document_id`: 文档 ID
- `document_unit_id`: 文档单元 ID
- `dataset_id`: 数据集 ID
- `user_id`: 用户 ID
- `page_number`: 页码
- `file_name`: 文件名
- `chunk_index`: 分块索引

**向量化流程：**
1. 文档单元生成
2. 发送消息到向量处理队列
3. 异步处理（Celery 消费者）
4. 调用 Embedding 模型生成向量
5. 向量存储到 PGVector/Milvus
6. 更新 DocumentUnit 状态

支持批量处理和回退机制，使用 psycopg2 的 copy_from 提升 PGVector 插入性能。

### RRF 融合算法

系统并行执行向量和关键词检索，使用 RRF（Reciprocal Rank Fusion）算法融合多排序结果。

**RRF 公式：**
```
RRF(d) = Σ(1 / (k + rank_i(d)))
```
其中 k 是平滑参数（通常为 60），rank_i(d) 是文档 d 在第 i 个检索结果中的排名。

**检索流程：**
1. 并发执行向量检索和关键词检索（使用 asyncio.gather）
2. 分别获取排序结果
3. 应用 RRF 算法计算每个文档的综合得分
4. 按综合得分重新排序
5. 返回 Top-K 结果

使用 FastAPI 的异步特性实现高并发检索。

### 文档处理策略模式

定义统一的文档处理策略接口（DocumentProcessingStrategy），支持多种文档格式：

**策略实现：**
- **PDF 策略**：使用 pypdf 解析 PDF 文件，提取文本和元数据
- **Word 策略**：使用 python-docx 解析 .doc/.docx 文件
- **Markdown 策略**：使用 markdown 库解析，按标题分段
- **纯文本策略**：直接读取 txt 文件内容

**工厂模式：**
DocumentProcessingFactory 根据文件扩展名自动选择对应的处理策略，便于扩展新的文档类型。每个策略返回统一的 Document 对象，包含文本内容和元数据。

### 消息队列驱动

定义两种消息类型：

**OCR 处理消息：**
```python
{
    "file_id": str,
    "file_path": str,
    "file_type": str,
    "user_id": str,
    "dataset_id": str,
    "priority": int
}
```

**向量化消息：**
```python
{
    "document_unit_id": str,
    "content": str,
    "metadata": dict,
    "user_id": str,
    "dataset_id": str
}
```

**消费者：**
- **RagDocConsumer**：处理 OCR 消息，调用对应的文档处理策略，完成后发送向量化消息
- **RagDocStorageConsumer**：处理向量化消息，调用 Embedding 模型生成向量并存储

使用 RabbitMQ + pika 或 Redis + Celery 实现消息队列。

### HyDE 和重排序

**HyDE（Hypothetical Document Embeddings）：**
- 使用 LLM 生成假设性文档来提升向量检索效果
- 对用户查询进行扩展，生成假设性的答案文档
- 对假设文档进行向量化，用于检索
- 提升对复杂查询的理解能力

**重排序（Rerank）：**
- 使用 sentence-transformers 的 CrossEncoder 模型对检索结果进行重排序
- LLM 对检索结果进行相关性评分（0-100）
- 基于评分重新排序，提升检索结果的相关度
- 可选启用/禁用，可配置重排序的候选数量

## 数据模型

核心实体（使用 SQLAlchemy ORM 定义）：

- **UserRag** (`user_rags`): 用户知识库
- **RagVersion** (`rag_versions`): RAG 版本
- **FileDetail** (`file_details`): 文件详情
- **DocumentUnit** (`document_units`): 文档单元（包含 pgvector 类型的 embedding 字段）
- **RagQaDataset** (`rag_qa_datasets`): QA 数据集
- **RagVersionFile** (`rag_version_file`): 版本文件关联
- **RagVersionDocument** (`rag_version_document`): 版本文档关联

**关系：**
- UserRag 与 RagVersion: 一对多
- UserRag 与 FileDetail: 一对多
- FileDetail 与 DocumentUnit: 一对多
- RagVersion 与 RagVersionFile: 一对多
- RagVersion 与 RagVersionDocument: 一对多

支持版本管理和快照功能，使用 Alembic 进行数据库迁移。

## 应用服务

使用 FastAPI + Depends 实现依赖注入，应用服务协调领域服务完成业务用例：

**数据集管理（RagDatasetAppService）：**
- CRUD 操作
- 版本管理
- 发布审核
- 统计信息

**文件操作（FileOperationAppService）：**
- 文件上传（支持大文件分片上传）
- 文件处理触发
- 文件删除
- 批量删除
- 查询文件列表
- 查询和管理文档单元
- 处理进度查询

**检索服务（RAGSearchAppService）：**
- 检索接口（支持向量/关键词/混合）
- 流式对话接口（WebSocket）
- 内容预览
- 高级检索配置

**市场管理（RagMarketAppService）：**
- 查询公共 RAG 列表
- 安装 RAG
- 统计信息

**发布审核（RagPublishAppService）：**
- 发布 RAG
- 审核 RAG 版本
- 批量审核
- 查询版本列表

## 版本管理

创建版本时自动生成递增版本号（语义化版本），创建版本快照，更新数据集版本。

**版本快照：**
- 记录该版本包含的所有文件信息
- 记录文档单元快照
- 支持版本回滚和历史追溯
- 版本对比功能

## 并发与性能

**并发设计：**
- 使用 asyncio.gather 实现向量和关键词检索的并发执行
- FastAPI 异步处理 HTTP 请求
- Celery 异步处理耗时任务（OCR、向量化）
- WebSocket 支持流式输出

**性能优化：**
- 分批处理策略（batch processing）
- 向量检索结果缓存（LRU 淘汰策略，使用 Redis）
- pgvector 索引优化（ivfflat / HNSW）
- 批量向量化（使用 psycopg2 copy_from）
- 连接池管理（数据库、消息队列）

**高可用：**
- 向量化服务支持多实例部署
- 消息队列持久化和重试机制
- 数据库主从复制

## 扩展性

**策略模式：**
- 通过实现 DocumentProcessingStrategy 接口并注册到策略工厂即可新增文档类型
- 通过添加新的检索算法可实现 BM25 检索等新方式
- 通过实现 VectorStore 接口支持新的向量数据库

**插件机制：**
- 支持自定义分段策略
- 支持自定义 Embedding 模型
- 支持自定义重排序模型

**配置化：**
- 检索参数可配置（top_k、相似度阈值等）
- 批处理大小可配置
- 重试策略可配置

## 安全设计

**数据隔离：**
- 所有查询必须携带 user_id 进行数据过滤
- 使用 SQLAlchemy 的 with_parent 确保跨用户访问被阻止
- API 层进行权限校验

**文件安全：**
- 上传文件类型白名单验证
- 文件大小限制
- XSS 防护：文件名和内容过滤
- 可选病毒扫描（ClamAV）

**内容审核：**
- 发布前敏感词检测
- 违规内容过滤
- 审核日志记录

**向量安全：**
- 向量数据传输加密（TLS）
- 向量存储加密（pgvector 支持）
- 访问令牌控制

## 计费集成

**用量记录：**
- 文件上传：记录文件大小和处理时长
- 向量化：记录向量化文档单元数量
- 检索：记录检索次数和返回结果数量
- 存储：记录存储空间使用量

**计费点：**
- OCR 处理费用
- 向量化费用
- 检索 API 调用费用
- 存储空间费用

**实现方式：**
- 消息队列消费者记录用量到 usage_records 表
- 定期聚合用量数据到计费系统
- 支持用量查询和报表

## 执行追踪集成

**追踪点：**
- 文件上传和处理流程追踪
- 向量化任务执行追踪
- 检索请求追踪
- 错误和异常追踪

**实现方式：**
- 使用 OpenTelemetry 进行分布式追踪
- 记录关键操作的 trace_id 和 span_id
- 与日志系统集成（结构化日志）
- 支持链路查询和性能分析
