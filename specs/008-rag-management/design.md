# RAG 管理技术设计

## 概述

RAG 管理模块采用领域驱动设计（DDD）架构，提供文档处理、向量化、混合检索和会话对话等核心能力。

## 技术架构

### 架构分层

系统采用四层架构：API 层处理 HTTP 请求；应用层协调领域服务，包含数据集管理、文件操作、检索服务、发布审核和市场管理；领域层封装核心业务逻辑，包含检索服务、增强服务、管理服务和状态机服务；基础设施层对接向量存储（PGVector/Milvus）、数据库（PostgreSQL）、消息队列和文件存储。

### 技术栈

Spring Boot、MyBatis Plus、LangChain4j、PGVector/Milvus、PostgreSQL、RabbitMQ/RocketMQ、分布式文件存储、Tesseract/EasyOCR。

## 核心设计

### 文件处理状态机

文档处理采用状态机模式，状态包括 UPLOADED（已上传）、OCR_PROCESSING（OCR 处理中）、OCR_COMPLETED（OCR 处理完成）、EMBEDDING_PROCESSING（向量化处理中）、COMPLETED（处理完成）、OCR_FAILED（OCR 处理失败）、EMBEDDING_FAILED（向量化失败）。文档从上传开始，依次经过 OCR 处理和向量化处理，任何步骤失败都会进入对应失败状态，支持重试。采用状态模式，每个状态对应一个独立处理器，状态转换由事件驱动。

### 向量存储设计

使用 LangChain4j 的 EmbeddingStore 接口抽象向量存储，支持 PGVector、Milvus 等多种向量数据库后端。每个向量片段携带丰富的元数据用于过滤和检索，包括文档 ID、文档单元 ID、数据集 ID、用户 ID、页码、文件名等。向量化流程包括文档单元生成、消息队列触发、异步处理、Embedding 模型调用、向量存储和状态更新，支持批量处理和回退机制。

### RRF 融合算法

系统并行执行向量和关键词检索，使用 RRF（Reciprocal Rank Fusion）算法融合多排序结果，公式为：RRF(d) = Σ(1 / (k + rank_i(d)))，其中 k 是平滑参数（通常为 60）。检索完成后使用 RRF 算法计算每个文档的综合得分并排序。

### 文档处理策略模式

定义统一的文档处理策略接口，支持 PDF（Apache PDFBox）、TXT（直接使用）、Word（Apache POI）、Markdown（按标题分段）等多种文档格式。通过策略工厂根据文件类型自动选择对应的处理策略，便于扩展新的文档类型。

### 消息队列驱动

定义两种消息类型：OCR 处理消息和向量化消息，包含文件 ID、文件路径、文件类型、用户 ID、数据集 ID 等信息。RagDocConsumer 处理 OCR 消息，调用对应的文档处理策略，完成后发送向量化消息；RagDocStorageConsumer 处理向量化消息，调用 Embedding 模型生成向量并存储。

### HyDE 和重排序

使用 HyDE（Hypothetical Document Embeddings）技术，让 LLM 生成假设性文档来提升向量检索效果。使用 LLM 对检索结果进行重排序（0-100 评分），提升检索结果的相关度。

## 数据模型

核心实体包括 RagQaDatasetEntity（数据集）、FileDetailEntity（文件详情）、DocumentUnitEntity（文档单元）、RagVersionEntity（RAG 版本）。数据集与文件、版本、文档单元之间建立关联关系，支持版本管理和快照功能。

## 应用服务

数据集管理提供 CRUD、版本管理、发布审核和统计信息功能。文件操作提供文件上传、处理、删除、批量删除、查询和管理文档单元功能，同时提供处理进度查询。检索服务提供检索接口、流式对话接口、内容预览和高级检索配置功能。

## 版本管理

创建版本时自动生成递增版本号，创建版本快照，更新数据集版本。版本快照记录该版本包含的所有文件信息，支持版本回滚和历史追溯。

## 并发与性能

使用 CompletableFuture 实现向量和关键词检索的并发执行，采用分批处理策略，对向量检索结果进行缓存（LRU 淘汰策略），向量化服务支持高可用。

## 扩展性

通过实现文档处理接口并注册到策略工厂即可新增文档类型，通过添加新的检索算法可实现 BM25 检索等新方式，通过实现 EmbeddingStore 接口支持新的向量数据库。
