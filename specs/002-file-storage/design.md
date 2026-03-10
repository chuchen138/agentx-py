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


### 2. 策略自动注册

利用 Spring 的依赖注入机制，自动收集所有 FileStorageStrategy 实现：


### 3. 降级机制

当未找到特定策略时，自动降级到通用策略：

### 4. API 端点
  - `POST /files/upload` - 文件上传
  - `GET /files/{url}` - 根据URL获取文件
  - `DELETE /files/{url}` - 删除文件
  - `GET /files/avatar/upload` - 头像上传
  - `GET /files/rag/upload` - RAG 文件上传
  - `GET /files/general/upload` - 通用文件上传

## 扩展点

### 1. 新增文件类型

1. 在 FileTypeEnum 中添加新类型
2. 实现 FileStorageStrategy 接口
3. 使用 @Component 注解标记策略
4. 策略自动注册到工厂

### 2. 自定义存储后端

通过实现 X-File-Storage 的存储器接口，支持多种存储后端：
- 本地存储
- 对象存储（S3、OSS、COS）
- 分布式文件系统（HDFS）

### 3. 策略热更新

策略作为 Spring Bean，支持：
- 运行时动态替换策略实现
- 基于配置的条件激活策略
- 策略优先级控制

## 配置设计

### 文件存储配置

```yaml
file-storage:
  enabled: true
  default-platform: local
  platforms:
    local:
      domain: http://localhost:8080
      path-prefix: /uploads/
    oss:
      endpoint: oss-cn-hangzhou.aliyuncs.com
      bucket: agentx-files
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
