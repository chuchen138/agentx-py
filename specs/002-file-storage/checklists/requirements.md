## 实施
- [ ] 1.1 定义文件存储模型和枚举
     【目标对象】`app/domain/file/`
     【修改目的】定义文件存储相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】`AgentX/domain/file/*.java`
     【修改内容】
        - 创建 FileRecord 模型（file_records 表）
        - 定义 FileTypeEnum 枚举（AVATAR, GENERAL, RAG）
        - 定义字段（file_type, original_filename, path, url, size, metadata）
        - 实现 Pydantic Schema

- [ ] 1.2 实现文件存储策略接口
     【目标对象】`app/application/file/strategy/file_storage_strategy.py`
     【修改目的】定义文件存储策略的统一接口
     【修改方式】实现策略模式接口
     【相关依赖】SQLAlchemy, FileRecord
     【修改内容】
        - 定义 FileStorageStrategy 接口
        - save - 保存文件信息
        - update - 更新文件信息
        - getByUrl - 根据 URL 查询文件
        - delete - 根据 URL 删除文件

- [ ] 1.3 实现文件存储策略工厂
     【目标对象】`app/application/file/factory/file_storage_strategy_factory.py`
     【修改目的】根据文件类型返回对应的存储策略
     【修改方式】实现工厂模式
     【相关依赖】FileStorageStrategy, FileTypeEnum
     【修改内容】
        - 定义 FileStorageStrategyFactory
        - getStrategy - 根据文件类型获取策略
        - 策略注册机制
        - 默认策略处理

- [ ] 1.4 实现头像文件存储策略
     【目标对象】`app/application/file/strategy/avatar_file_storage_strategy.py`
     【修改目的】实现头像文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy
     【修改内容】
        - 头像文件大小限制（如 2MB）
        - 头像格式限制（jpg, jpeg, png, webp）
        - 头像存储路径规则（/avatar/{user_id}/{filename}）
        - 头像图片压缩和优化
        - 生成缩略图

- [ ] 1.5 实现通用文件存储策略
     【目标对象】`app/application/file/strategy/general_file_storage_strategy.py`
     【修改目的】实现通用文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy
     【修改内容】
        - 通用文件大小限制（如 50MB）
        - 文件格式白名单
        - 存储路径规则（/general/{date}/{filename}）
        - 文件去重（基于文件 hash）

- [ ] 1.6 实现 RAG 文件存储策略
     【目标对象】`app/application/file/strategy/rag_file_storage_strategy.py`
     【修改目的】实现 RAG 数据集文件的存储策略
     【修改方式】实现 FileStorageStrategy 接口
     【相关依赖】FileStorageStrategy
     【修改内容】
        - RAG 文件大小限制（如 500MB）
        - 支持的文件格式（PDF, Word, TXT, Markdown 等）
        - 存储路径规则（/rag/{user_id}/{dataset_id}/{filename}）
        - 文件预处理（OCR、文本提取）
        - 文件版本管理

- [ ] 1.7 实现文件存储应用服务
     【目标对象】`app/application/file/service/file_storage_app_service.py`
     【修改目的】编排文件存储相关的用例
     【修改方式】实现应用服务
     【相关依赖】FileStorageStrategyFactory, FileStorageStrategy
     【修改内容】
        - 实现 FileStorageAppService
        - save - 保存文件（通过策略）
        - update - 更新文件（通过策略）
        - getByUrl - 查询文件（通过 URL）
        - delete - 删除文件（通过 URL）
        - 文件类型自动判断（通过路径或元数据）

- [ ] 1.8 实现文件上传端点
     【目标对象】`app/api/v1/files/`
     【修改目的】暴露文件上传相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】FileStorageAppService, python-multipart
     【修改内容】
        - `POST /api/v1/files/upload/avatar` - 头像上传
        - `POST /api/v1/files/upload/general` - 通用文件上传
        - `POST /api/v1/files/upload/rag` - RAG 文件上传
        - `GET /api/v1/files/{url}` - 获取文件信息
        - `DELETE /api/v1/files/{url}` - 删除文件

- [ ] 1.9 实现文件存储配置
     【目标对象】`app/application/file/config/file_storage_config.py`
     【修改目的】配置文件存储相关参数
     【修改方式】使用 Pydantic Settings
     【相关依赖】Pydantic
     【修改内容】
        - 存储后端配置（本地/OSS/S3）
        - 上传限制配置
        - 文件路径规则配置
        - URL 签名配置

- [ ] 1.10 实现文件上传中间件
     【目标对象】`app/api/middleware/`
     【修改目的】验证上传文件的合法性和大小
     【修改方式】实现 FastAPI 中间件
     【相关依赖】Pydantic, python-multipart
     【修改内容】
        - 文件大小检查
        - 文件格式检查
        - 文件名安全检查
        - 恶意文件检测

- [ ] 1.11 实现存储后端适配器
     【目标对象】`app/infrastructure/storage/`
     【修改目的】支持多种存储后端
     【修改方式】实现适配器模式
     【相关依赖】阿里云 OSS SDK / boto3
     【修改内容】
        - 定义存储后端接口
        - 实现本地存储适配器
        - 实现阿里云 OSS 适配器
        - 实现 AWS S3 适配器

- [ ] 1.12 编写单元测试
     【目标对象】`tests/test_file_storage_service.py`
     【修改目的】确保文件存储功能正确性
     【修改方式】使用 pytest
     【相关依赖】FileStorageAppService
     【修改内容】
        - 测试文件保存
        - 测试文件更新
        - 测试文件查询
        - 测试文件删除
        - 测试文件类型判断
        - 测试头像策略
        - 测试通用策略
        - 测试 RAG 策略
        - 测试策略工厂

- [ ] 1.13 编写集成测试
     【目标对象】`tests/integration/test_file_up