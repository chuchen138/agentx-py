## 实施

### 1. 领域模型和基础设施

- [ ] 1.1 定义文件存储领域模型
     【目标对象】`app/domain/file/`
     【修改目的】定义文件存储相关的领域模型和枚举
     【修改方式】使用 SQLAlchemy 定义 ORM 模型，Pydantic 定义 Schema
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 FileRecord 模型（file_records 表）
          - id: UUID (主键)
          - user_id: UUID (外键，关联 users 表)
          - file_type: String (文件类型：AVATAR, GENERAL, RAG)
          - original_filename: String (原始文件名)
          - stored_filename: String (存储文件名，含路径)
          - file_path: String (完整存储路径)
          - file_url: String (访问 URL)
          - file_size: Integer (文件大小，字节)
          - mime_type: String (MIME 类型)
          - storage_backend: String (存储后端：local, oss, s3, cos)
          - version: Integer (版本号，默认 1)
          - metadata: JSONB (元数据)
          - created_at: DateTime
          - updated_at: DateTime
          - deleted_at: DateTime (软删除标记)
          - 索引：file_url, user_id, file_type
        - 定义 FileType 枚举类（AVATAR, GENERAL, RAG）
        - 定义 StorageBackendType 枚举类（LOCAL, OSS, S3, COS）
        - 实现 Pydantic Schema:
          - FileRecordCreate, FileRecordUpdate, FileRecordResponse
          - FileUploadResponse, FileURLResponse

- [ ] 1.2 定义文件版本模型（可选）
     【目标对象】`app/domain/file/`
     【修改目的】支持文件版本管理
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, FileRecord
     【修改内容】
        - 创建 FileVersion 模型（file_versions 表）
          - id: UUID (主键)
          - file_id: UUID (外键，关联 file_records)
          - version: Integer (版本号)
          - file_url: String (版本文件 URL)
          - file_size: Integer (文件大小)
          - change_log: Text (变更日志)
          - created_by: UUID (创建者)
          - created_at: DateTime
        - 实现版本查询和回滚逻辑

- [ ] 1.3 定义存储后端抽象接口
     【目标对象】`app/infrastructure/storage/backend/`
     【修改目的】统一不同存储后端的操作
     【修改方式】使用 ABC 定义抽象基类
     【相关依赖】abc, typing
     【修改内容】
        - 定义 StorageBackend 抽象基类
          - save(file_content, filename, **kwargs) -> str (保存文件，返回 URL)
          - load(file_url) -> bytes (加载文件内容)
          - update(file_url, new_content) -> str (更新文件)
          - delete(file_url) -> bool (删除文件)
          - exists(file_url) -> bool (检查文件是否存在)
          - get_url(file_url, expires_in=3600) -> str (获取访问 URL)
          - list_files(prefix="") -> List[str] (列出文件)
          - get_metadata(file_url) -> dict (获取文件元数据)
        - 定义异步接口（AsyncStorageBackend）
          - async save(...), async load(...), etc.

- [ ] 1.4 实现本地存储适配器
     【目标对象】`app/infrastructure/storage/backend/local_storage.py`
     【修改目的】支持本地文件系统存储
     【修改方式】实现 StorageBackend 接口
     【相关依赖】StorageBackend, os, pathlib, aiofiles
     【修改内容】
        - 实现 LocalStorageBackend 类
        - 配置文件根目录和数据目录路径
        - 实现文件 CRUD 操作
        - 实现异步文件操作（aiofiles）
        - 文件名 sanitization（防止路径遍历）
        - 目录自动创建
        - 文件权限管理

- [ ] 1.5 实现阿里云 OSS 适配器
     【目标对象】`app/infrastructure/storage/backend/oss_storage.py`
     【修改目的】支持阿里云对象存储
     【修改方式】实现 StorageBackend 接口
     【相关依赖】StorageBackend, aliyun-python-sdk-oss
     【修改内容】
        - 实现 OSSStorageBackend 类
        - 配置 Endpoint、Bucket、AccessKey、Secret
        - 实现文件上传下载
        - 实现分片上传（大文件）
        - 生成预签名 URL
        - 生命周期管理配置
        - CDN 加速集成

- [ ] 1.6 实现 AWS S3 适配器
     【目标对象】`app/infrastructure/storage/backend/s3_storage.py`
     【修改目的】支持 AWS S3 对象存储
     【修改方式】实现 StorageBackend 接口
     【相关依赖】StorageBackend, boto3>=1.26
     【修改内容】
        - 实现 S3StorageBackend 类
        - 配置 Region、Bucket、AccessKey、Secret
        - 实现文件上传下载
        - 实现分片上传（multipart upload）
        - 生成预签名 URL（Presigned URL）
        - 存储桶策略管理
        - 传输加速支持

- [ ] 1.7 实现腾讯云 COS 适配器
     【目标对象】`app/infrastructure/storage/backend/cos_storage.py`
     【修改目的】支持腾讯云对象存储
     【修改方式】实现 StorageBackend 接口
     【相关依赖】StorageBackend, cos-python-sdk-v5
     【修改内容】
        - 实现 COSStorageBackend 类
        - 配置 Region、Bucket、SecretId、SecretKey
        - 实现文件上传下载
        - 实现分片上传
        - 生成临时访问密钥

### 2. 策略模式实现

- [ ] 2.1 定义文件存储策略接口
     【目标对象】`app/application/file/strategy/file_storage_strategy.py`
     【修改目的】定义文件存储策略的统一接口
     【修改方式】使用 ABC 定义抽象基类
     【相关依赖】abc, FileRecord, StorageBackend
     【修改内容】
        - 定义 FileStorageStrategy 抽象基类
          - save(file, metadata) -> FileRecord
          - update(file_record, file) -> FileRecord
          - get_by_url(file_url) -> FileRecord
          - delete(file_url) -> bool
          - validate_file(file) -> bool (验证文件合法性)
          - get_storage_backend() -> StorageBackend
        - 定义异步支持（可选）

- [ ] 2.2 实现头像文件存储策略
     【目标对象】`app/application/file/strategy/avatar_file_storage_strategy.py`
     【修改目的】实现头像文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy, PIL/Pillow
     【修改内容】
        - AvatarFileStorageStrategy 类
        - 头像文件大小限制（≤ 2MB）
        - 头像格式限制（jpg, jpeg, png, webp）
        - 头像存储路径规则：/avatar/{user_id}/{timestamp}_{filename}
        - 图片压缩和优化（保持宽高比，最大 512x512）
        - 生成缩略图（128x128）
        - MIME 类型验证
        - 图片损坏检测

- [ ] 2.3 实现通用文件存储策略
     【目标对象】`app/application/file/strategy/general_file_storage_strategy.py`
     【修改目的】实现通用文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy, python-magic
     【修改内容】
        - GeneralFileStorageStrategy 类
        - 通用文件大小限制（≤ 50MB）
        - 文件格式白名单验证
        - 存储路径规则：/general/{user_id}/{date}/{uuid}_{filename}
        - 文件去重（基于 SHA-256 哈希）
        - MIME 类型检测（python-magic）
        - 文件名 sanitization

- [ ] 2.4 实现 RAG 文件存储策略
     【目标对象】`app/application/file/strategy/rag_file_storage_strategy.py`
     【修改目的】实现 RAG 数据集文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy, pdf2image, python-docx
     【修改内容】
        - RagFileStorageStrategy 类
        - RAG 文件大小限制（≤ 500MB）
        - 支持的文件格式：PDF, DOC, DOCX, TXT, MD, CSV
        - 存储路径规则：/rag/{user_id}/{dataset_id}/{uuid}_{filename}
        - 文件预处理：
          - PDF：提取文本、OCR 识别（可选）
          - Word：提取文本
          - 文本编码检测
        - 文件版本管理
        - 批量上传支持

- [ ] 2.5 实现文件存储策略工厂
     【目标对象】`app/application/file/factory/file_storage_strategy_factory.py`
     【修改目的】根据文件类型返回对应的存储策略
     【修改方式】实现工厂模式
     【相关依赖】FileStorageStrategy, FileType, dependency injection
     【修改内容】
        - FileStorageStrategyFactory 类
        - get_strategy(file_type: FileType) -> FileStorageStrategy
        - 策略注册机制（register_strategy）
        - 默认策略处理（GeneralFileStorageStrategy）
        - 策略缓存（避免重复创建）
        - 异常处理（StrategyNotFoundException）

### 3. 应用服务层

- [ ] 3.1 实现文件存储应用服务
     【目标对象】`app/application/file/service/file_storage_app_service.py`
     【修改目的】编排文件存储相关的用例
     【修改方式】实现应用服务类
     【相关依赖】FileStorageStrategyFactory, FileRecord, Pydantic
     【修改内容】
        - FileStorageAppService 类
        - save_file(file, file_type, user_id, metadata) -> FileRecord
        - update_file(file_id, file, user_id) -> FileRecord
        - get_file(file_id or url, user_id) -> FileRecord
        - delete_file(file_id or url, user_id) -> bool
        - 文件类型自动判断（通过端点或元数据）
        - 权限验证（文件所有权检查）
        - 事务管理
        - 异步方法支持

- [ ] 3.2 实现大文件分片上传服务
     【目标对象】`app/application/file/service/chunked_upload_service.py`
     【修改目的】支持大文件分片上传和断点续传
     【修改方式】实现分片上传逻辑
     【相关依赖】FileStorageAppService, Redis
     【修改内容】
        - ChunkedUploadService 类
        - init_upload(file_id, total_size, chunk_count) -> upload_id
        - upload_chunk(upload_id, chunk_index, chunk_data) -> bool
        - complete_upload(upload_id) -> FileRecord
        - abort_upload(upload_id) -> bool
        - 分片状态管理（Redis）
        - 分片合并逻辑
        - 超时清理机制

- [ ] 3.3 实现文件元数据缓存服务
     【目标对象】`app/application/file/service/file_cache_service.py`
     【修改目的】缓存文件元数据，提高查询性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis, FileRecord
     【修改内容】
        - FileCacheService 类
        - cache_file(file_id, file_record, ttl=3600)
        - get_cached_file(file_id) -> FileRecord | None
        - invalidate_cache(file_id)
        - 缓存预热（批量加载）
        - 缓存淘汰策略（LRU）

### 4. API 层

- [ ] 4.1 实现文件上传端点
     【目标对象】`app/api/v1/files/`
     【修改目的】暴露文件上传相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】FileStorageAppService, FastAPI, UploadFile
     【修改内容】
        - `POST /api/v1/files/upload/avatar` - 头像上传
          - 表单数据：file (UploadFile)
          - 响应：FileUploadResponse
        - `POST /api/v1/files/upload/general` - 通用文件上传
          - 表单数据：file (UploadFile)
          - 响应：FileUploadResponse
        - `POST /api/v1/files/upload/rag` - RAG 文件上传
          - 表单数据：file (UploadFile), dataset_id (UUID)
          - 响应：FileUploadResponse
        - `POST /api/v1/files/upload/chunked/init` - 初始化分片上传
        - `POST /api/v1/files/upload/chunk/{upload_id}` - 上传分片
        - `POST /api/v1/files/upload/chunked/complete/{upload_id}` - 完成分片上传

- [ ] 4.2 实现文件查询和管理端点
     【目标对象】`app/api/v1/files/`
     【修改目的】提供文件查询和管理 API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】FileStorageAppService, FastAPI
     【修改内容】
        - `GET /api/v1/files/{file_id}` - 获取文件信息
        - `PUT /api/v1/files/{file_id}` - 更新文件
        - `DELETE /api/v1/files/{file_id}` - 删除文件
        - `GET /api/v1/files/{file_id}/download` - 下载文件
        - `GET /api/v1/files/{file_id}/url` - 获取临时访问 URL
        - `GET /api/v1/files/my` - 获取我的文件列表
          - 查询参数：page, page_size, file_type
        - `POST /api/v1/files/batch-delete` - 批量删除文件

- [ ] 4.3 实现文件下载中间件
     【目标对象】`app/api/middleware/file_download_middleware.py`
     【修改目的】优化文件下载性能
     【修改方式】使用 FastAPI 中间件或 BackgroundTask
     【相关依赖】FastAPI, StreamingResponse
     【修改内容】
        - 流式下载支持（StreamingResponse）
        - 断点续传支持（Range 请求头处理）
        - CDN 重定向（如果配置了 CDN）
        - 下载限流（可选）
        - 并发下载控制

### 5. 安全和验证

- [ ] 5.1 实现文件上传中间件
     【目标对象】`app/api/middleware/file_upload_middleware.py`
     【修改目的】验证上传文件的合法性和大小
     【修改方式】实现 FastAPI Depends 依赖
     【相关依赖】Pydantic, python-multipart, python-magic
     【修改内容】
        - 文件大小检查（Content-Length 头）
        - 文件格式检查（扩展名 + MIME 类型）
        - 文件名安全检查（防止路径遍历）
        - 恶意文件检测（可选：ClamAV 扫描）
        - 上传频率限制（基于用户 ID）

- [ ] 5.2 实现访问权限验证
     【目标对象】`app/api/dependencies/file_permission.py`
     【修改目的】验证用户对文件的访问权限
     【修改方式】实现 FastAPI Depends 依赖
     【相关依赖】FileRecord, current_user dependency
     【修改内容】
        - 文件所有权验证
        - 临时访问令牌验证
        - RBAC 权限检查
        - 未授权访问抛出 HTTPException(403)

### 6. 配置和工具

- [ ] 6.1 实现文件存储配置
     【目标对象】`app/application/file/config/file_storage_config.py`
     【修改目的】配置文件存储相关参数
     【修改方式】使用 Pydantic Settings
     【相关依赖】Pydantic
     【修改内容】
        - FileStorageSettings 类
        - 默认存储后端配置（LOCAL/OSS/S3/COS）
        - 各存储后端详细配置
        - 上传限制配置（最大文件大小、分片大小）
        - 文件路径规则配置
        - URL 签名配置（过期时间）
        - 缓存配置（TTL、最大缓存数）
        - 安全配置（白名单、病毒扫描开关）

- [ ] 6.2 实现文件类型白名单配置
     【目标对象】`app/application/file/config/file_type_whitelist.py`
     【修改目的】配置文件类型白名单
     【修改方式】使用 Pydantic 和字典配置
     【相关依赖】Pydantic
     【修改内容】
        - FileTypeWhitelist 类
        - 按文件类型分类（images, documents, others）
        - 扩展名到 MIME 类型的映射
        - 动态添加/移除白名单项

### 7. 测试

- [ ] 7.1 编写单元测试
     【目标对象】`tests/unit/test_file_storage/`
     【修改目的】确保文件存储功能正确性
     【修改方式】使用 pytest 和 pytest-asyncio
     【相关依赖】pytest, pytest-asyncio, pytest-mock
     【修改内容】
        - test_file_record_model.py - 测试 ORM 模型
        - test_storage_backends.py - 测试存储适配器
          - test_local_storage_save_load
          - test_oss_storage_multipart_upload
          - test_s3_storage_presigned_url
        - test_file_strategies.py - 测试文件策略
          - test_avatar_strategy_compression
          - test_general_strategy_deduplication
          - test_rag_strategy_text_extraction
        - test_factory.py - 测试策略工厂
        - test_app_service.py - 测试应用服务
        - test_cache_service.py - 测试缓存服务
        - test_chunked_upload.py - 测试分片上传

- [ ] 7.2 编写集成测试
     【目标对象】`tests/integration/test_file_endpoints.py`
     【修改目的】测试 API 端点的完整流程
     【修改方式】使用 TestClient 和 pytest
     【相关依赖】FastAPI TestClient, pytest
     【修改内容】
        - test_avatar_upload_endpoint
        - test_general_upload_endpoint
        - test_rag_upload_endpoint
        - test_file_download_endpoint
        - test_chunked_upload_flow
        - test_file_permission_check
        - test_batch_delete

- [ ] 7.3 编写性能测试
     【目标对象】`tests/performance/test_file_upload_performance.py`
     【修改目的】测试文件上传性能
     【修改方式】使用 pytest-benchmark 或 locust
     【相关依赖】pytest-benchmark 或 locust
     【修改内容】
        - 并发上传测试（100 并发）
        - 大文件上传测试（1GB）
        - 缓存命中率测试
        - 分片上传性能测试

- [ ] 7.4 编写安全测试
     【目标对象】`tests/security/test_file_security.py`
     【修改目的】测试文件存储安全性
     【修改方式】使用 pytest
     【相关依赖】pytest
     【修改内容】
        - 文件类型绕过测试
        - 路径遍历攻击测试
        - 越权访问测试
        - 大文件 DoS 攻击测试
        - 恶意文件上传测试

### 8. 监控和日志

- [ ] 8.1 实现文件操作日志记录
     【目标对象】`app/application/file/service/file_audit_service.py`
     【修改目的】记录文件操作审计日志
     【修改方式】使用结构化日志库
     【相关依赖】structlog 或 logging
     【修改内容】
        - FileAuditService 类
        - log_upload(user_id, file_id, file_type, size)
        - log_download(user_id, file_id)
        - log_delete(user_id, file_id)
        - 包含上下文信息（IP、User-Agent）
        - 敏感信息掩码

- [ ] 8.2 实现监控指标上报
     【目标对象】`app/infrastructure/metrics/file_metrics.py`
     【修改目的】收集文件存储相关指标
     【修改方式】使用 Prometheus 客户端
     【相关依赖】prometheus-client
     【修改内容】
        - 文件上传成功率指标
        - 上传耗时直方图
        - 存储使用量统计
        - 各类型文件数量统计
        - 缓存命中率指标
        - 错误类型分布

### 9. 文档和示例

- [ ] 9.1 编写 API 文档
     【目标对象】`docs/api/file-storage-api.md`
     【修改目的】提供完整的 API 文档
     【修改方式】使用 Markdown
     【相关依赖】无
     【修改内容】
        - 所有端点的详细说明
        - 请求和响应示例
        - 错误码说明
        - 认证和授权说明
        - 速率限制说明

- [ ] 9.2 编写使用示例
     【目标对象】`examples/file-storage/`
     【修改目的】提供代码使用示例
     【修改方式】创建 Python 脚本
     【相关依赖】requests 或 httpx
     【修改内容】
        - 普通文件上传示例
        - 分片上传示例
        - 文件下载示例
        - 批量操作示例
        - 错误处理示例