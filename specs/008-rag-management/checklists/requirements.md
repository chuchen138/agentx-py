## 实施

**核心依赖：**
- Python >= 3.9
- SQLAlchemy >= 2.0
- FastAPI >= 0.100
- LangChain >= 0.1 或 LlamaIndex >= 0.9
- pgvector >= 0.2.0
- psycopg2-binary >= 2.9
- pypdf >= 3.0
- python-docx >= 0.8
- Tesseract OCR (pytesseract) 或 EasyOCR
- RabbitMQ / Redis (Celery)

**可选依赖：**
- sentence-transformers (用于重排序)
- MinIO Client (用于对象存储)
- ClamAV (用于病毒扫描)

---

---

## 第一阶段：领域层和数据模型

- [ ] 1.1 创建 Python RAG 模块目录结构
     【目标对象】`app/rag/`
     【修改目的】搭建 RAG 模块的基础目录结构
     【修改方式】创建领域层、应用层、API 层目录
     【相关依赖】无
     【修改内容】
        - 创建 `app/domain/rag/` 目录
        - 创建 `app/application/rag/` 目录
        - 创建 `app/api/v1/rag/` 目录
        - 创建 `app/infrastructure/rag/` 目录
        - 创建 `tests/test_rag/` 目录

- [ ] 1.2 定义 UserRag 实体和模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义用户知识库的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 UserRag 模型（user_rags 表）
        - 定义字段：id, user_id, name, description, model_config, created_at, updated_at
        - 定义与 RagVersion 的一对多关系
        - 实现 Pydantic Schema（UserRagDTO）

- [ ] 1.3 定义 RagVersion 实体和模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义 RAG 版本的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 RagVersion 模型（rag_versions 表）
        - 定义字段：id, user_rag_id, version_number, status, publish_status, description, created_at
        - 定义与 UserRag 的多对一关系
        - 定义与 RagVersionFile 的一对多关系
        - 定义与 RagVersionDocument 的一对多关系
        - 实现 Pydantic Schema（RagVersionDTO）

- [ ] 1.4 定义 FileDetail 实体和模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义文件详情的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 FileDetail 模型（file_details 表）
        - 定义字段：id, user_rag_id, file_name, file_path, file_type, file_size, status, processing_progress, created_at
        - 定义与 UserRag 的多对一关系
        - 定义与 DocumentUnit 的一对多关系
        - 实现 Pydantic Schema（FileDetailDTO, FileDetailInfoDTO）

- [ ] 1.5 定义 DocumentUnit 实体和模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义文档单元的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 DocumentUnit 模型（document_units 表）
        - 定义字段：id, file_detail_id, content, chunk_index, embedding, metadata, segment_type, created_at
        - 定义与 FileDetail 的多对一关系
        - 创建 pgvector 扩展支持（embedding 字段使用 vector 类型）
        - 实现 Pydantic Schema（DocumentUnitDTO）

---

## 第二阶段：仓储层和数据访问

- [ ] 1.6 定义 RagQaDataset 实体和模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义 QA 数据集的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 RagQaDataset 模型（rag_qa_datasets 表）
        - 定义字段：id, user_rag_id, name, question_count, created_at, updated_at
        - 定义与 UserRag 的多对一关系
        - 实现 Pydantic Schema（RagQaDatasetDTO）

- [ ] 1.7 定义关联实体模型
     【目标对象】`app/domain/rag/models.py`
     【修改目的】定义版本文件和版本文档的关联模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】无
     【修改内容】
        - 创建 RagVersionFile 模型（rag_version_file 表）
        - 创建 RagVersionDocument 模型（rag_version_document 表）
        - 定义关联关系和级联删除
        - 实现 Pydantic Schema（RagVersionFileDTO, RagVersionDocumentDTO）

- [ ] 1.8 定义枚举类型和常量
     【目标对象】`app/domain/rag/constants.py`
     【修改目的】定义 RAG 相关的枚举类型和常量
     【修改方式】使用 Python Enum 定义枚举
     【相关依赖】无
     【修改内容】
        - FileProcessingStatusEnum：文件处理状态（UPLOADED, OCR_PROCESSING, OCR_COMPLETED, EMBEDDING_PROCESSING, EMBEDDING_COMPLETED, FAILED）
        - RagPublishStatus：RAG 发布状态（DRAFT, REVIEWING, PUBLISHED, REJECTED）
        - SearchType：搜索类型（VECTOR, KEYWORD, HYBRID）
        - SegmentType：分段类型（PARAGRAPH, SENTENCE, CUSTOM）
        - MetadataConstant：元数据常量

- [ ] 1.9 实现 UserRagRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义 UserRag 的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】UserRag 模型
     【修改内容】
        - 定义 UserRagRepository 接口
        - 实现 SQLAlchemy UserRagRepository
        - 实现 CRUD 操作
        - 实现按用户查询
        - 实现按名称查询

- [ ] 1.10 实现 RagVersionRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义 RagVersion 的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】RagVersion 模型
     【修改内容】
        - 定义 RagVersionRepository 接口
        - 实现 SQLAlchemy RagVersionRepository
        - 实现 CRUD 操作
        - 实现按 UserRag 查询
        - 实现按版本号查询

- [ ] 1.11 实现 FileDetailRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义 FileDetail 的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】FileDetail 模型
     【修改内容】
        - 定义 FileDetailRepository 接口
        - 实现 SQLAlchemy FileDetailRepository
        - 实现 CRUD 操作
        - 实现按 UserRag 查询
        - 实现按状态查询

- [ ] 1.12 实现 DocumentUnitRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义 DocumentUnit 的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】DocumentUnit 模型
     【修改内容】
        - 定义 DocumentUnitRepository 接口
        - 实现 SQLAlchemy DocumentUnitRepository
        - 实现 CRUD 操作
        - 实现按 FileDetail 查询
        - 实现向量相似度查询（使用 pgvector cosine_similarity）

- [ ] 1.13 实现 RagQaDatasetRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义 RagQaDataset 的数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】RagQaDataset 模型
     【修改内容】
        - 定义 RagQaDatasetRepository 接口
        - 实现 SQLAlchemy RagQaDatasetRepository
        - 实现 CRUD 操作
        - 实现按 UserRag 查询

- [ ] 1.14 实现 VectorStoreRepository
     【目标对象】`app/domain/rag/repository.py`
     【修改目的】定义向量存储的访问接口
     【修改方式】实现 pgvector 向量存储访问
     【相关依赖】DocumentUnit 模型, pgvector
     【修改内容】
        - 定义 VectorStoreRepository 接口
        - 实现向量插入
        - 实现向量相似度搜索
        - 实现批量向量插入
        - 实现向量删除

---

## 第三阶段：领域服务层

- [ ] 1.15 实现 UserRagDomainService
     【目标对象】`app/domain/rag/service.py`
     【修改目的】封装 UserRag 相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】UserRagRepository, RagVersionRepository
     【修改内容】
        - 创建用户知识库
        - 更新用户知识库
        - 删除用户知识库（级联删除关联数据）
        - 验证知识库名称唯一性

- [ ] 1.16 实现 RagVersionDomainService
     【目标对象】`app/domain/rag/service.py`
     【修改目的】封装 RagVersion 相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】RagVersionRepository, RagVersionFileRepository, RagVersionDocumentRepository
     【修改内容】
        - 创建新版本
        - 版本号自动递增逻辑
        - 版本快照创建（复制文件和文档关联）
        - 版本发布状态管理
        - 版本删除

- [ ] 1.17 实现 FileDetailDomainService
     【目标对象】`app/domain/rag/service.py`
     【修改目的】封装 FileDetail 相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】FileDetailRepository
     【修改内容】
        - 创建文件记录
        - 更新文件处理状态
        - 更新文件处理进度
        - 文件状态转换验证

- [ ] 1.18 实现 DocumentUnitDomainService
     【目标对象】`app/domain/rag/service.py`
     【修改目的】封装 DocumentUnit 相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】DocumentUnitRepository
     【修改内容】
        - 创建文档单元
        - 批量插入文档单元
        - 更新文档单元
        - 删除文档单元

- [ ] 1.19 实现 EmbeddingDomainService
     【目标对象】`app/domain/rag/service.py`
     【修改目的】实现文档向量嵌入服务
     【修改方式】集成 LangChain 或 LlamaIndex 嵌入模型
     【相关依赖】LangChain/LlamaIndex, LLM 模块
     【修改内容】
        - 文本向量化（Embedding）
        - 批量向量化
        - 向量结果验证
        - 嵌入模型配置管理

- [ ] 1.20 实现文件处理策略
     【目标对象】`app/domain/rag/strategy/`
     【修改目的】实现文档解析和分段策略
     【修改方式】策略模式
     【相关依赖】pypdf, python-docx, python-pptx, markdown
     【修改内容】
        - DocumentProcessingStrategy 抽象基类
        - PDF 解析策略（使用 pypdf）
        - Word 解析策略（使用 python-docx）
        - Markdown 解析策略
        - 纯文本解析策略
        - DocumentProcessingFactory 工厂类

- [ ] 1.21 实现文本分段服务
     【目标对象】`app/domain/rag/service/chunking.py`
     【修改目的】实现文档文本分段
     【修改方式】基于规则的分段
     【相关依赖】langchain.text_splitter
     【修改内容】
        - 按段落分段
        - 按句子分段
        - 按字符数分段
        - 重叠分段（Chunking with overlap）
        - 分段元数据提取

---

## 第四阶段：应用服务层

- [ ] 1.22 实现 HybridSearchDomainService
     【目标对象】`app/domain/rag/service/search.py`
     【修改目的】实现混合检索（语义 + 关键词）
     【修改方式】结合向量检索和关键词检索
     【相关依赖】pgvector 全文检索或 Elasticsearch
     【修改内容】
        - 语义检索（向量相似度）
        - 关键词检索（全文搜索）
        - 混合检索（RRF 重排序）
        - 检索结果过滤
        - 检索去重

- [ ] 1.23 实现 RerankDomainService
     【目标对象】`app/domain/rag/service/rerank.py`
     【修改目的】实现检索结果重排序
     【修改方式】使用重排序模型或规则
     【相关依赖】sentence-transformers CrossEncoder 或自定义规则
     【修改内容】
        - 基于模型的重排序（可选）
        - 基于评分的重排序
        - 去除低质量结果
        - 结果截断

- [ ] 1.24 实现文件处理状态机
     【目标对象】`app/domain/rag/service/state_machine.py`
     【修改目的】实现文件处理状态机
     【修改方式】状态模式
     【相关依赖】FileDetail 模型
     【修改内容】
        - FileProcessingStateProcessor 基类
        - UploadedStateProcessor 初始状态
        - OcrProcessingStateProcessor OCR 处理状态
        - OcrCompletedStateProcessor OCR 完成状态
        - EmbeddingProcessingStateProcessor 向量化处理状态
        - CompletedStateProcessor 完成状态
        - 状态转换逻辑和验证

- [ ] 1.25 实现 UserRagAssembler
     【目标对象】`app/application/rag/assembler.py`
     【修改目的】实现 UserRag 实体与 DTO 转换
     【修改方式】Assembler 模式
     【相关依赖】UserRagDTO
     【修改内容】
        - 实体转 DTO
        - DTO 转实体

- [ ] 1.26 实现 RagVersionAssembler
     【目标对象】`app/application/rag/assembler.py`
     【修改目的】实现 RagVersion 实体与 DTO 转换
     【修改方式】Assembler 模式
     【相关依赖】RagVersionDTO
     【修改内容】
        - 实体转 DTO
        - DTO 转实体

- [ ] 1.27 实现 FileDetailAssembler
     【目标对象】`app/application/rag/assembler.py`
     【修改目的】实现 FileDetail 实体与 DTO 转换
     【修改方式】Assembler 模式
     【相关依赖】FileDetailDTO, FileDetailInfoDTO
     【修改内容】
        - 实体转 DTO
        - DTO 转实体

- [ ] 1.28 实现 DocumentUnitAssembler
     【目标对象】`app/application/rag/assembler.py`
     【修改目的】实现 DocumentUnit 实体与 DTO 转换
     【修改方式】Assembler 模式
     【相关依赖】DocumentUnitDTO
     【修改内容】
        - 实体转 DTO
        - DTO 转实体

- [ ] 1.29 实现 RagQaDatasetAssembler
     【目标对象】`app/application/rag/assembler.py`
     【修改目的】实现 RagQaDataset 实体与 DTO 转换
     【修改方式】Assembler 模式
     【相关依赖】RagQaDatasetDTO
     【修改内容】
        - 实体转 DTO
        - DTO 转实体

- [ ] 1.30 实现 FileOperationAppService
     【目标对象】`app/application/rag services/file_operation.py`
     【修改目的】编排文件上传和处理用例
     【修改方式】实现应用服务
     【相关依赖】FileDetailDomainService, DocumentProcessingStrategy
     【修改内容】
        - 上传文件（UploadFile）
        - 处理文件（ProcessFile）
        - 批量删除文件（BatchDeleteFiles）
        - 查询文件列表（QueryDatasetFiles）
        - 查询文件处理进度

- [ ] 1.31 实现 RagQaDatasetAppService
     【目标对象】`app/application/rag/services/qa_dataset.py`
     【修改目的】编排 QA 数据集管理用例
     【修改方式】实现应用服务
     【相关依赖】RagQaDatasetDomainService
     【修改内容】
        - 创建数据集（CreateDataset）
        - 更新数据集（UpdateDataset）
        - 删除数据集
        - 查询数据集列表（QueryDatasets）
        - 数据集统计

- [ ] 1.32 实现 RagMarketAppService
     【目标对象】`app/application/rag/services/market.py`
     【修改目的】编排 RAG 市场用例
     【修改方式】实现应用服务
     【相关依赖】UserRagDomainService
     【修改内容】
        - 查询公共 RAG 列表
        - 安装 RAG（InstallRag）
        - RAG 统计信息

- [ ] 1.33 实现 RagPublishAppService
     【目标对象】`app/application/rag/services/publish.py`
     【修改目的】编排 RAG 发布用例
     【修改方式】实现应用服务
     【相关依赖】RagVersionDomainService
     【修改内容】
        - 发布 RAG（PublishRag）
        - 审核 RAG（ReviewRagVersion）
        - 批量审核（BatchReview）
        - 查询版本（QueryRagVersion）

- [ ] 1.34 实现 RAGSearchAppService
     【目标对象】`app/application/rag/services/search.py`
     【修改目的】编排检索用例
     【修改方式】实现应用服务
     【相关依赖】HybridSearchDomainService, RerankDomainService
     【修改内容】
        - RAG 检索（Search）
        - 流式检索（StreamSearch）
        - 重排序（Rerank）
        - RAG 聊天（RagChat）
        - 检索用量记录（用于计费）

- [ ] 1.35 实现 RAG 路由
     【目标对象】`app/api/v1/rag/`
     【修改目的】暴露 RAG 相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】Rag 应用服务
     【修改内容】
        - `POST /api/v1/rag/market/install` - 安装 RAG
        - `GET /api/v1/rag/market` - 获取 RAG 市场列表
        - `GET /api/v1/rag/statistics` - 获取统计信息
        - `POST /api/v1/rag/datasets` - 创建数据集
        - `GET /api/v1/rag/datasets` - 查询数据集列表
        - `PUT /api/v1/rag/datasets/{id}` - 更新数据集
        - `DELETE /api/v1/rag/datasets/{id}` - 删除数据集
        - `POST /api/v1/rag/files/upload` - 上传文件
        - `POST /api/v1/rag/files/process` - 处理文件
        - `GET /api/v1/rag/files` - 查询文件列表
        - `DELETE /api/v1/rag/files` - 批量删除文件批量删除文件
        - `GET /api/v1/rag/files/{id}/progress` - 获取文件处理进度
        - `POST /api/v1/rag/search` - RAG 检索
        - `POST /api/v1/rag/versions` - 创建版本
        - `GET /api/v1/rag/versions` - 查询版本列表
        - `POST /api/v1/rag/publish` - 发布版本
        - `POST /api/v1/rag/review` - 审核版本

- [ ] 1.36 实现消息队列消费者
     【目标对象】`app/infrastructure/rag/consumer.py`
     【修改目的】异步处理文档
     【修改方式】使用 Pika 消费 RabbitMQ 消息
     【相关依赖】RabbitMQ, FileDetailDomainService, EmbeddingDomainService
     【修改内容】
        - RagDocConsumer（文档处理消费者）
        - RagDocStorageConsumer（文档存储消费者）
        - 消息解析和错误处理
        - 消息重试机制
        - 死信队列处理
        - 用量记录（用于计费）

- [ ] 1.37 实现消息队列生产者
     【目标对象】`app/infrastructure/rag/producer.py`
     【修改目的】发送文档处理消息
     【修改方式】使用 Pika 发送 RabbitMQ 消息
     【相关依赖】RabbitMQ
     【修改内容】
        - 发送文档处理消息
        - 发送文档存储消息
        - 消息序列化
        - 消息持久化
        - 优先级队列支持

- [ ] 1.37.1 实现敏感内容检测服务
     【目标对象】`app/domain/rag/service/content_moderation.py`
     【修改目的】检测和过滤敏感内容
     【修改方式】使用敏感词库或 AI 模型
     【相关依赖】sensitive-word 库或自定义 AI 模型
     【修改内容】
        - 敏感词过滤
        - 违规内容检测
        - 发布前内容审核
        - 审核日志记录

- [ ] 1.38 实现 RAG 文件存储策略
     【目标对象】`app/infrastructure/rag/storage/`
     【修改目的】实现 RAG 文件存储
     【修改方式】文件系统存储或对象存储
     【相关依赖】本地文件系统或 MinIO/S3
     【修改内容】
        - 检查文件类型和大小限制
        - 文件病毒扫描（可选集成 ClamAV）
        - XSS 防护：文件名和内容过滤
        - 保存文件到指定路径
        - 删除文件
        - 文件路径生成策略
        - 支持文件访问权限控制

- [ ] 1.39 实现向量化任务调度
     【目标对象】`app/infrastructure/rag/tasks/`
     【修改目的】定时执行向量化任务
     【修改方式】使用 Celery 或 APScheduler
     【相关依赖】Celery 或 APScheduler, Redis/RabbitMQ
     【修改内容】
        - 创建向量化任务
        - 批量向量化任务
        - 任务监控和日志
        - 任务失败告警
        - 支持任务优先级

- [ ] 1.40 实现 OCR 服务
     【目标对象】`app/infrastructure/rag/ocr/`
     【修改目的】实现文本识别功能
     【修改方式】集成 Tesseract OCR 或云服务 OCR
     【相关依赖】Tesseract (pytesseract)、EasyOCR 或 OCR 云服务 API
     【修改内容】
        - 图片 OCR
        - PDF OCR
        - OCR 结果验证
        - OCR 错误处理
        - 支持多语言识别
        - 批量 OCR 处理

- [ ] 1.41 编写单元测试 - 领域层
     【目标对象】`tests/rag/test_domain_service.py`
     【修改目的】确保 RAG 领域逻辑正确性
     【修改方式】使用 pytest
     【相关依赖】Rag 应用服务
     【修改内容】
        - 测试 UserRag 创建和删除
        - 测试 RagVersion 创建和快照
        - 测试 FileDetail 状态转换
        - 测试 DocumentUnit 批量操作
        - 测试向量化服务
        - 测试用户数据隔离

- [ ] 1.42 编写单元测试 - 向量检索
     【目标对象】`tests/rag/test_search.py`
     【修改目的】确保检索功能正确性
     【修改方式】使用 pytest
     【相关依赖】RAGSearchAppService
     【修改内容】
        - 测试语义检索
        - 测试关键词检索
        - 测试混合检索
        - 测试重排序
        - 测试 RAG 聊天
        - 测试检索精度评估（Precision/Recall）

---

## 第五阶段：基础设施层

- [ ] 1.43 编写单元测试 - 文件处理
     【目标对象】`tests/rag/test_file_processing.py`
     【修改目的】确保文件处理正确性
     【修改方式】使用 pytest
     【相关依赖】FileOperationAppService
     【修改内容】
        - 测试文件上传
        - 测试文件解析
        - 测试文本分段
        - 测试状态机转换
        - 测试 OCR 错误处理和重试机制
        - 测试多语言文档处理

- [ ] 1.44 编写集成测试 - RAG 完整流程
     【目标对象】`tests/integration/test_rag_workflow.py`
     【修改目的】确保 RAG 端到端流程正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, RAG 应用服务
     【修改内容】
        - 测试 RAG 创建、文件上传、向量化完整流程
        - 测试 RAG 发布流程
        - 测试检索功能
        - 测试 API 端点

- [ ] 1.45 编写数据库迁移文件
     【目标对象】`alembic/versions/`
     【修改目的】创建 RAG 相关数据库表
     【修改方式】使用 Alembic
     【相关依赖】SQLAlchemy, pgvector
     【修改内容】
        - 创建 user_rags 表
        - 创建 rag_versions 表
        - 创建 file_details 表
        - create rag_qa_datasets 表
        - 创建 document_units 表（含 pgvector 扩展）
        - 创建关联表（rag_version_file, rag_version_document）
        - 启用 pgvector 扩展

- [ ] 1.46 性能优化 - 向量化批处理
     【目标对象】`app/domain/rag/service/embedding.py`
     【修改目的】提高向量化性能
     【修改方式】批量化处理
     【相关依赖】LangChain/LlamaIndex
     【修改内容】
        - 实现批量向量化（batch_size 可配置）
        - 并行处理（使用 asyncio 或 multiprocessing）
        - 错误重试机制（指数退避）
        - 向量结果缓存

- [ ] 1.47 性能优化 - 索引优化
     【目标对象】`alembic/versions/`
     【修改目的】优化数据库查询性能
     【修改方式】添加数据库索引
     【相关依赖】PostgreSQL, pgvector
     【修改内容】
        - 为 embedding 字段创建 ivfflat 索引（HNSW 可选）
        - 为 user_id 字段创建索引
        - 为 status 字段创建索引
        - 为 created_at 字段创建索引
        - 为 dataset_id 字段创建索引
        - 优化向量检索查询计划

---

## 第六阶段：测试和部署

**实施优先级说明：**
1. **第一阶段**（领域层和数据模型）：基础，必须首先完成
2. **第二阶段**（仓储层）：数据访问，依赖第一阶段
3. **第三阶段**（领域服务）：核心业务逻辑，依赖前两个阶段
4. **第四阶段**（应用服务）：用例编排，可以并行开发部分功能
5. **第五阶段**（基础设施）：异步处理和存储，可以提前准备
6. **第六阶段**（测试）：贯穿整个开发过程，建议 TDD

**预计工作量：**
- 领域层和数据模型：3-5 天
- 仓储层：2-3 天
- 领域服务：5-7 天
- 应用服务：4-6 天
- 基础设施：3-5 天
- 测试和优化：5-7 天
- **总计**: 22-33 天
