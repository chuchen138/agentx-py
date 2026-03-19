# 文件存储（File Storage）- 设计文档

## 架构设计

### 1. 整体架构

文件存储模块采用策略模式实现，通过 FileStorageAppService 作为统一入口，根据文件类型选择对应的存储策略进行处理。

```
┌─────────────────────────────────────────────────────────┐
│              FileStorageAppService                        │
│          (实现 FileRecorder 接口)                          │
└────────────────┬────────────────────────────────────────┘
                 │
                 │ 文件类型判断
                 ▼
┌─────────────────────────────────────────────────────────┐
│           FileStorageStrategyFactory                      │
│              策略工厂（根据类型返回策略）                   │
└────────────────┬────────────────────────────────────────┘
                 │
      ┌──────────┼──────────┬──────────┐
      ▼          ▼          ▼          ▼
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│ RAG     │ │ Avatar  │ │ General │ │ Custom  │
│ Strategy│ │ Strategy│ │ Strategy│ │ Strategy│
└─────────┘ └─────────┘ └─────────┘ └─────────┘
```
### 2. 核心组件

#### 2.1 FileStorageAppService

**职责**：
- 文件存储的统一入口
- 实现 FileRecorder 接口
- 文件类型判断
- 委托给对应策略处理

#### 2.2 FileStorageStrategyFactory

**职责**：
- 管理所有存储策略
- 根据文件类型返回对应策略
- 提供默认策略降级机制

#### 2.3 FileStorageStrategy 接口

**职责**：
- 定义存储策略的统一接口
- 提供文件 CRUD 操作

#### 2.4 FileTypeEnum

**支持类型**：
- `RAG`：RAG 文档文件
- `AVATAR`：用户头像文件
- `GENERAL`：通用文件（默认）

## 设计模式

### 策略模式（Strategy Pattern）

**目的**：定义一系列算法，将每个算法封装起来，并使它们可以互换。

**实现**：
- **策略接口**：FileStorageStrategy
- **具体策略**：
  - RagFileStorageStrategy
  - AvatarFileStorageStrategy
  - GeneralFileStorageStrategy
- **策略上下文**：FileStrategyFactory

### 工厂模式（Factory Pattern）

**目的**：根据输入参数（文件类型）创建对应策略对象。

**实现**：
- FileStrategyFactory 作为工厂类
- 通过 Spring 自动注入所有策略（Map<FileTypeEnum, FileStorageStrategy>）

## 技术实现

### 1. 文件类型识别

通过文件扩展名和MIME类型进行文件类型识别，支持以下类型：
- **RAG**：RAG 文档文件（PDF, DOC, DOCX, TXT, MD, CSV）
- **AVATAR**：用户头像文件（JPG, JPEG, PNG, WebP）
- **GENERAL**：通用文件（其他类型）

### 2. 策略自动注册

利用依赖注入机制，自动收集所有 FileStorageStrategy 实现，通过 FileStorageStrategyFactory 管理。

### 3. 降级机制

当未找到特定策略时，自动降级到通用策略（GeneralFileStorageStrategy）。

### 4. API 端点

#### 文件上传
- `POST /api/v1/files/upload/avatar` - 头像上传
  - **请求参数**：file (UploadFile), user_id (UUID)
  - **响应**：FileUploadResponse
  - **文件限制**：≤ 2MB，支持 JPG, JPEG, PNG, WebP
  - **Curl 命令**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload/avatar" -F "file=@test.jpg" -F "user_id=123e4567-e89b-12d3-a456-426614174000"
    ```

- `POST /api/v1/files/upload/general` - 通用文件上传
  - **请求参数**：file (UploadFile), user_id (UUID)
  - **响应**：FileUploadResponse
  - **文件限制**：≤ 50MB，支持多种文件类型
  - **Curl 命令**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload/general" -F "file=@test.txt" -F "user_id=123e4567-e89b-12d3-a456-426614174000"
    ```

- `POST /api/v1/files/upload/rag` - RAG 文件上传
  - **请求参数**：file (UploadFile), user_id (UUID), dataset_id (UUID)
  - **响应**：FileUploadResponse
  - **文件限制**：≤ 500MB，支持 PDF, DOC, DOCX, TXT, MD, CSV
  - **Curl 命令**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/upload/rag" -F "file=@test.pdf" -F "user_id=123e4567-e89b-12d3-a456-426614174000" -F "dataset_id=123e4567-e89b-12d3-a456-426614174001"
    ```

- `POST /api/v1/files/upload/chunked/init` - 初始化分片上传
  - **请求参数**：file_name (str), file_size (int), chunk_count (int), user_id (UUID)
  - **响应**：{"upload_id": "..."}

- `POST /api/v1/files/upload/chunk/{upload_id}` - 上传分片
  - **请求参数**：chunk_index (int), chunk_data (bytes)
  - **响应**：{"success": true}

- `POST /api/v1/files/upload/chunked/complete/{upload_id}` - 完成分片上传
  - **响应**：FileUploadResponse

#### 文件查询和管理
- `GET /api/v1/files/{file_id}` - 获取文件信息
  - **响应**：FileRecordResponse
  - **Curl 命令**：
    ```bash
    curl "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000"
    ```

- `PUT /api/v1/files/{file_id}` - 更新文件
  - **请求参数**：file (UploadFile), user_id (UUID)
  - **响应**：FileRecordResponse
  - **Curl 命令**：
    ```bash
    curl -X PUT "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000" -F "file=@updated.txt" -F "user_id=123e4567-e89b-12d3-a456-426614174000"
    ```

- `DELETE /api/v1/files/{file_id}` - 删除文件
  - **请求参数**：user_id (UUID)
  - **响应**：{"message": "File deleted successfully"}
  - **Curl 命令**：
    ```bash
    curl -X DELETE "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000" -F "user_id=123e4567-e89b-12d3-a456-426614174000"
    ```

- `GET /api/v1/files/{file_id}/download` - 下载文件
  - **响应**：文件流
  - **Curl 命令**：
    ```bash
    curl -OJ "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000/download"
    ```

- `GET /api/v1/files/{file_id}/url` - 获取临时访问 URL
  - **请求参数**：expires_in (int, 默认为 3600)
  - **响应**：{"url": "...", "expires_at": "..."}
  - **Curl 命令**：
    ```bash
    curl "http://localhost:8000/api/v1/files/123e4567-e89b-12d3-a456-426614174000/url?expires_in=3600"
    ```

- `GET /api/v1/files/my/list` - 获取我的文件列表
  - **请求参数**：user_id (UUID), page (int), page_size (int), file_type (str)
  - **响应**：{"items": [...], "total": 100, "page": 1, "page_size": 10}
  - **Curl 命令**：
    ```bash
    curl "http://localhost:8000/api/v1/files/my/list?user_id=123e4567-e89b-12d3-a456-426614174000&page=1&page_size=10"
    ```

- `POST /api/v1/files/batch-delete` - 批量删除文件
  - **请求参数**：file_ids (List[UUID]), user_id (UUID)
  - **响应**：{"success": true, "deleted_count": 3}
  - **Curl 命令**：
    ```bash
    curl -X POST "http://localhost:8000/api/v1/files/batch-delete" -H "Content-Type: application/json" -d '{"file_ids": ["123e4567-e89b-12d3-a456-426614174000", "123e4567-e89b-12d3-a456-426614174001"], "user_id": "123e4567-e89b-12d3-a456-426614174000"}'
    ```

## 扩展点

### 1. 新增文件类型

1. 在 FileTypeEnum 中添加新类型
2. 实现 FileStorageStrategy 接口
3. 注册到策略工厂
4. 策略自动被工厂管理

### 2. 自定义存储后端

通过实现 StorageBackend 接口，支持多种存储后端：
- 本地存储
- Minio 对象存储（S3 兼容）
- 阿里云 OSS
- AWS S3
- 腾讯云 COS

### 3. Minio 存储配置

Minio 是一个高性能的对象存储服务，兼容 S3 API，适合作为文件存储的后端。

**配置要点**：
- **Endpoint**：Minio 服务地址，格式为 `host:port`
- **Access Key**：访问密钥
- **Secret Key**： secret 密钥
- **Bucket**：存储桶名称
- **Secure**：是否使用 HTTPS
- **Region**：存储区域

**优势**：
- 高性能：支持高并发读写
- 可扩展性：支持横向扩展
- S3 兼容：可无缝切换到其他 S3 兼容存储
- 本地部署：适合开发和测试环境
- 企业级特性：支持版本控制、生命周期管理等

### 4. 策略热更新

策略作为单例对象管理，支持：
- 运行时动态替换策略实现
- 基于配置的条件激活策略
- 策略优先级控制

## 配置设计

### 文件存储配置

```yaml
file-storage:
  enabled: true
  default-platform: minio
  platforms:
    local:
      domain: http://localhost:8000
      path-prefix: /uploads/
      root-dir: ./uploads
    minio:
      endpoint: localhost:9000
      access-key: minioadmin
      secret-key: minioadmin
      bucket: agentx-files
      secure: false
      region: us-east-1
    rag-storage:
      bucket: rag-documents
      path-prefix: /rag/
    avatar-storage:
      bucket: user-avatars
      path-prefix: /avatars/
```

## 关键流程

### 文件上传流程

```
1. 客户端上传文件
   ↓
2. FileStorageAppService.save()
   ↓
3. 判断文件类型 (determineFileType)
   ↓
4. 从工厂获取策略 (getStrategy)
   ↓
5. 委托策略处理 (strategy.save)
   ↓
6. 保存到存储后端
   ↓
7. 记录文件元数据
   ↓
8. 返回文件 URL
```

### 文件查询流程

```
1. 根据文件 URL 查询
   ↓
2. FileStorageAppService.getByUrl()
   ↓
3. 从 URL 解析文件类型
   ↓
4. 从工厂获取策略
   ↓
5. 委托策略查询
   ↓
6. 返回文件信息
```

## 错误处理

### 异常类型

1. **策略未找到异常**
   - 当所有策略（包括默认策略）都不可用时抛出

2. **文件类型识别失败**
   - 默认使用 GENERAL 类型
   - 记录警告日志

3. **存储后端异常**
   - 捕获并转换为业务异常
   - 记录详细错误日志

## 性能优化

### 1. 策略缓存

- 策略对象在 Spring 容器中单例管理
- 避免重复创建策略实例

### 2. 文件类型快速判断

- 基于路径前缀的快速匹配
- 避免复杂的文件内容分析

### 3. 批量操作

- 支持批量文件上传
- 减少网络往返次数

## 监控指标

### 关键指标

1. **文件上传成功率**
2. **平均上传时间**
3. **各类型文件存储量**
4. **存储后端响应时间**
5. **策略执行失败率**

### 日志记录

- 文件操作日志（保存、更新、查询、删除）
- 策略选择日志
- 异常日志（包含堆栈信息）
