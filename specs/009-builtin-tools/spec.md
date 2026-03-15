# 内置工具（Built-in Tools）

## 概述

内置工具模块提供系统级别的工具注册和管理能力，包括 RAG 检索工具和系统内置工具。通过工具提供者模式（Provider Pattern）和工具注册表（Registry Pattern），实现工具的动态管理、分类查询和状态控制。所有内置工具在系统启动时自动注册，支持热插拔扩展。

## 功能需求

### 1. 系统内置工具注册

**描述**：注册和管理系统提供的内置工具，不需要用户配置。

**功能**：
- **工具注册**：系统启动时自动注册所有内置工具
- **工具分类**：按类型和用途分类工具（RAG 检索、文件操作、数据处理、系统工具）
- **工具查询**：支持按名称、类型、标签查询可用的内置工具
- **工具状态管理**：管理工具的启用/禁用状态，支持黑名单机制
- **工具版本管理**：支持工具版本控制和演进

**内置工具类型**：
- **RAG 检索工具**：rag_search（向量检索）、rag_hybrid_search（混合检索）、rag_keyword_search（关键词检索）
- **文件操作工具**：file_read、file_write、file_delete、file_list
- **数据处理工具**：data_parse、data_transform、data_validate
- **系统工具**：system_info、datetime_query、calculator

**范围说明**：
- 内置工具与 MCP 工具的区分：内置工具由系统提供，MCP 工具由用户通过 MCP 协议接入
- 内置工具优先级高于市场工具，同名工具优先使用内置版本
- 内置工具无需安装，市场工具需要用户安装后才能使用

### 2. RAG 检索工具

**描述**：提供知识库检索能力，支持向量检索、关键词检索和混合检索，与 RAG 管理模块深度集成。

**功能**：
- **向量检索**：基于向量相似度检索相关文档（调用 RAGSearchAppService）
- **关键词检索**：基于 BM25 算法的关键词匹配检索
- **混合检索**：结合向量和关键词检索，使用 RRF 算法融合结果
- **参数预设**：支持检索参数的预设和自定义（top_k、相似度阈值等）
- **重排序支持**：可选启用 CrossEncoder 或 LLM 重排序
- **HyDE 支持**：支持假设性文档嵌入提升检索效果

**检索策略**：
- 向量相似度（余弦相似度、欧氏距离）
- 关键词匹配（BM25、TF-IDF）
- 重排序（CrossEncoder、LLM 评分）
- 混合权重（RRF 融合算法）

**与 RAG 管理模块的耦合**：
- 依赖 RAGSearchAppService 提供检索能力
- 共享向量存储和索引配置
- 复用 RAG 管理的缓存和性能优化机制

### 3. 工具提供者模式

**描述**：通过工具提供者（Provider）模式注册和管理工具，支持多种提供者类型。

**功能**：
- **提供者注册**：注册工具提供者到注册表
- **工具发现**：从提供者自动发现所有可用工具
- **工具聚合**：聚合所有提供者的工具到统一注册表
- **动态更新**：支持提供者的动态添加和移除
- **提供者隔离**：不同提供者之间的工具命名空间隔离

**提供者类型**：
- **RAG 工具提供者**（RagBuiltInToolProvider）：提供 RAG 检索工具
- **系统工具提供者**（SystemBuiltInToolProvider）：提供文件操作、数据处理、系统工具
- **MCP 工具提供者**（McpBuiltInToolProvider）：提供 MCP 协议兼容的工具（与 007-tool-integration 集成）

**Python 实现方式**：
- 使用 FastAPI Depends 注入实现提供者注册
- 使用 Python 元类（metaclass）实现自动注册机制
- 支持使用装饰器标记提供者类

### 4. 工具定义

**描述**：定义工具的接口、参数、返回值等元数据，使用 Pydantic 模型和 JSON Schema。

**定义内容**：
- **工具名称**（name）：工具的唯一标识符（字符串，符合命名规范：小写字母和下划线）
- **工具描述**（description）：工具的功能描述（字符串，必填）
- **输入参数**（parameters）：工具所需的参数定义（Pydantic 模型或 JSON Schema）
- **返回值**（output）：工具返回的数据结构定义（Pydantic 模型或 JSON Schema）
- **工具类型**（type）：工具的类型分类（枚举：RAG_SEARCH、FILE_OPERATION、DATA_PROCESSING、SYSTEM）
- **工具标签**（tags）：工具的标签列表，用于分类和搜索（如 ["rag", "search", "vector"]）
- **工具权限**（permission）：工具需要的权限级别（枚举：PUBLIC、USER、ADMIN）
- **提供者标识**（provider_id）：工具的提供者 ID
- **版本号**（version）：工具版本（语义化版本号，如 1.0.0）

**要求**：
- 工具定义使用 Pydantic v2 模型定义，自动生成 JSON Schema
- 支持参数校验（必填字段、类型检查、值域范围）
- 支持工具版本管理和向后兼容
- 工具定义示例见文末附录

**工具定义 JSON Schema 示例**：
```json
{
  "name": "rag_search",
  "description": "基于向量相似度的知识库检索",
  "type": "RAG_SEARCH",
  "version": "1.0.0",
  "provider_id": "rag_builtin_provider",
  "tags": ["rag", "search", "vector"],
  "permission": "USER",
  "parameters": {
    "type": "object",
    "properties": {
      "query": {
        "type": "string",
        "description": "检索查询文本"
      },
      "dataset_id": {
        "type": "string",
        "description": "数据集 ID"
      },
      "top_k": {
        "type": "integer",
        "description": "返回结果数量",
        "default": 5,
        "minimum": 1,
        "maximum": 20
      },
      "similarity_threshold": {
        "type": "number",
        "description": "相似度阈值",
        "default": 0.7,
        "minimum": 0.0,
        "maximum": 1.0
      }
    },
    "required": ["query", "dataset_id"]
  },
  "output": {
    "type": "array",
    "items": {
      "type": "object",
      "properties": {
        "content": {"type": "string"},
        "score": {"type": "number"},
        "metadata": {"type": "object"}
      }
    }
  }
}
```

### 5. 工具注册表

**描述**：维护所有可用工具的注册表，提供快速查找、过滤和缓存能力。

**功能**：
- **工具存储**：使用线程安全的字典存储所有工具定义
- **工具查询**：根据名称、类型、标签、提供者查询工具
- **工具过滤**：按权限、状态、版本等条件过滤工具列表
- **工具缓存**：使用 LRU 缓存常用工具的定义（TTL 可配置）
- **冲突处理**：处理工具名称冲突，支持版本优先级

**要求**：
- 支持工具的热注册和注销（不重启系统）
- 支持工具版本管理（同一工具多个版本共存）
- 提供快速的查询接口（响应时间 < 50ms）
- 注册表支持持久化（可选 Redis 或数据库）
- 启动时自动扫描并注册所有 BuiltInToolProvider

### 6. 工具调用

**描述**：执行工具的调用，处理参数验证、工具执行、结果返回和错误处理。

**功能**：
- **参数验证**：验证调用参数的合法性（JSON Schema 校验、类型检查、值域验证）
- **工具执行**：执行工具的逻辑（同步/异步）
- **结果返回**：返回工具执行的标准化结果（成功/失败、数据/错误信息）
- **错误处理**：处理工具执行失败（超时、异常、资源不可用）
- **超时控制**：支持工具调用超时设置（默认 30 秒）
- **并发控制**：限制最大并发调用数（默认 1000 QPS）

**要求**：
- 统一的工具调用接口（execute 方法）
- 支持异步工具调用（async/await）
- 支持工具调用超时控制（可配置）
- 记录工具调用日志（结构化日志）
- 支持工具调用重试机制（可配置重试次数）

## 技术约束

### 1. Python 技术栈实现
- **Web 框架**：FastAPI（使用 Depends 实现依赖注入）
- **数据模型**：Pydantic v2（用于工具定义和参数验证）
- **注册表实现**：使用单例模式 + 线程安全字典
- **提供者注册**：使用元类（metaclass）或装饰器自动注册
- **异步支持**：使用 asyncio 实现异步工具调用
- **缓存机制**：使用 functools.lru_cache 或 aiocache

### 2. 工具定义标准
- 工具定义使用 Pydantic BaseModel 定义
- 自动生成 JSON Schema 用于参数验证
- 遵循 OpenAPI 3.0 参数格式规范
- 支持工具版本语义化版本控制（SemVer 2.0.0）

### 3. 与 RAG 管理模块集成
- 依赖 RAGSearchAppService 提供检索能力
- 共享向量存储配置（PGVector/Milvus）
- 复用 RAG 管理的缓存和性能优化
- 遵循 RAG 管理的数据隔离和安全策略

### 4. 与 MCP 工具集成
- 内置工具与 MCP 工具命名空间隔离
- 支持 MCP 协议版本 1.0+
- 内置工具优先级高于 MCP 工具
- 避免工具名称冲突（使用前缀区分，如 rag_、sys_）

## 性能要求

### 1. 响应时间
- **工具查询响应时间**：< 50ms（P95）
- **工具注册延迟**：< 100ms（单个工具）
- **RAG 检索响应时间**：< 500ms（P95，包含向量检索和 RRF 融合）
- **工具调用响应时间**：< 200ms（P95，不含外部依赖）

### 2. 并发能力
- **最大并发调用数**：1000 QPS
- **并发执行上限**：100 个并发任务（可配置）
- **线程池大小**：CPU 核心数 * 2 + 1（默认 17）
- **异步任务队列长度**：10000（超出拒绝）

### 3. 缓存性能
- **缓存命中率**：> 80%（常用工具定义）
- **缓存过期时间**：5 分钟（可配置）
- **缓存刷新机制**：LRU 淘汰 + TTL

### 4. 可用性
- **服务可用性**：> 99.9%
- **工具注册成功率**：> 99.5%
- **工具调用成功率**：> 98%

### 5. 资源限制
- **内存占用**：< 500MB（注册表 + 缓存）
- **CPU 使用率**：< 70%（峰值）
- **数据库连接数**：< 50（连接池）

## 安全要求

### 1. 参数注入防护
- **JSON Schema 严格校验**：所有输入参数必须通过 JSON Schema 验证
- **命令注入防护**：禁止执行系统命令（os.system, subprocess 等）
- **SQL 注入防护**：使用参数化查询，禁止字符串拼接 SQL
- **路径遍历防护**：文件操作工具限制访问目录范围
- **XSS 防护**：过滤 HTML/JavaScript 内容

### 2. 工具权限控制
- **权限分级**：PUBLIC（公开）、USER（登录用户）、ADMIN（管理员）
- **权限校验**：每次工具调用前校验用户权限
- **最小权限原则**：工具只授予完成功能所需的最小权限
- **权限审计**：记录所有权限相关操作

### 3. 沙箱执行
- **文件系统隔离**：限制工具访问的文件路径（使用 chroot 或 pathlib 限制）
- **网络访问控制**：禁止工具访问外部网络（除白名单域名）
- **资源限制**：限制 CPU、内存、磁盘使用量
- **超时强制终止**：超时工具调用强制终止并释放资源

### 4. 敏感信息保护
- **参数脱敏**：日志中记录的参数需脱敏（密钥、密码、身份证号等）
- **结果过滤**：过滤结果中的敏感信息（银行卡号、手机号等）
- **加密存储**：敏感配置使用加密存储（AES-256）
- **密钥管理**：使用环境变量或密钥管理服务

### 5. 黑名单机制
- **工具黑名单**：支持禁用特定工具（全局或针对用户）
- **提供者黑名单**：禁用来自特定提供者的所有工具
- **动态更新**：黑名单支持热更新，无需重启系统
- **黑名单检查**：每次工具调用前检查黑名单

### 6. 审计日志
- **调用日志**：记录所有工具调用的详细信息（工具名、参数、结果、耗时、用户 ID）
- **安全日志**：记录所有安全相关事件（权限拒绝、参数非法、黑名单命中）
- **审计追踪**：支持按用户、工具、时间范围查询审计日志
- **日志保留**：审计日志保留至少 180 天

### 7. 异常处理
- **异常捕获**：所有工具调用必须捕获异常并返回标准化错误
- **错误信息脱敏**：错误信息不包含堆栈轨迹和敏感信息
- **失败降级**：关键工具失败时提供降级方案（如返回缓存数据）
- **重试机制**：支持有限次数的自动重试（最多 3 次）

## 监控与告警

### 1. 监控指标
- **工具调用指标**：
  - 调用次数（按工具、提供者、用户维度统计）
  - 平均响应时间（P50、P95、P99）
  - 成功率/失败率
  - 超时次数
- **RAG 检索指标**：
  - 检索请求数
  - 平均检索时间
  - 平均返回结果数
  - 缓存命中率
- **注册表指标**：
  - 注册工具总数
  - 活跃提供者数量
  - 缓存命中率
  - 注册表健康状态

### 2. 告警规则
- **工具调用失败率过高**：> 5%（5 分钟内）触发告警
- **RAG 检索延迟过高**：P95 > 1s 触发告警
- **参数验证失败频繁**：> 100 次/分钟触发告警
- **工具超时率过高**：> 10% 触发告警
- **注册表异常**：注册表不可用立即触发 P0 告警

### 3. 日志记录
- **结构化日志**：使用 JSON 格式记录所有日志
- **日志级别**：DEBUG、INFO、WARNING、ERROR、CRITICAL
- **日志聚合**：集成 ELK 或 Loki 进行日志聚合分析
- **日志采样**：高频日志支持采样（如 10%）

### 4. 链路追踪
- **分布式追踪**：集成 OpenTelemetry 实现链路追踪
- **Trace ID**：每次工具调用生成唯一 Trace ID
- **Span 记录**：记录工具调用的关键 Span（参数验证、执行、结果返回）
- **性能分析**：支持链路性能瓶颈分析

## 附录 A：工具定义完整示例

### A.1 RAG 检索工具定义
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ToolType(str, Enum):
    RAG_SEARCH = "RAG_SEARCH"
    FILE_OPERATION = "FILE_OPERATION"
    DATA_PROCESSING = "DATA_PROCESSING"
    SYSTEM = "SYSTEM"

class PermissionLevel(str, Enum):
    PUBLIC = "PUBLIC"
    USER = "USER"
    ADMIN = "ADMIN"

class RagSearchParameters(BaseModel):
    query: str = Field(..., description="检索查询文本", min_length=1)
    dataset_id: str = Field(..., description="数据集 ID")
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="相似度阈值")
    use_rerank: bool = Field(default=False, description="是否启用重排序")
    use_hybrid: bool = Field(default=True, description="是否使用混合检索")

class RagSearchResult(BaseModel):
    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="相似度分数")
    metadata: dict = Field(default_factory=dict, description="元数据")
    document_id: str = Field(..., description="文档 ID")

class RagSearchToolDefinition(BaseModel):
    name: str = "rag_search"
    description: str = "基于向量相似度的知识库检索"
    type: ToolType = ToolType.RAG_SEARCH
    version: str = "1.0.0"
    provider_id: str = "rag_builtin_provider"
    tags: List[str] = ["rag", "search", "vector"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = RagSearchParameters
    output: type = List[RagSearchResult]
```

### A.2 文件读取工具定义
```python
class FileReadParameters(BaseModel):
    file_path: str = Field(..., description="文件路径", pattern=r"^[a-zA-Z0-9_/.\-]+$")
    max_size: int = Field(default=1048576, description="最大文件大小（字节）", ge=1)
    encoding: str = Field(default="utf-8", description="文件编码")

class FileReadResult(BaseModel):
    content: str = Field(..., description="文件内容")
    size: int = Field(..., description="文件大小（字节）")
    lines: int = Field(..., description="文件行数")

class FileReadToolDefinition(BaseModel):
    name: str = "file_read"
    description: str = "读取文件内容"
    type: ToolType = ToolType.FILE_OPERATION
    version: str = "1.0.0"
    provider_id: str = "system_builtin_provider"
    tags: List[str] = ["file", "read", "io"]
    permission: PermissionLevel = PermissionLevel.USER
    parameters: type = FileReadParameters
    output: type = FileReadResult
```

## 附录 B：相关模块

- **007-tool-integration**：MCP 工具集成，提供第三方工具接入能力
- **008-rag-management**：RAG 管理模块，提供向量检索和文档处理能力
- **010-agent-management**：Agent 管理模块，使用内置工具构建 Agent
- **014-agent-workflow**：Agent 工作流，调用内置工具执行复杂任务
- **019-account-billing**：计费模块，记录工具调用用量

## 附录 C：技术术语

| 术语 | 说明 |
|-----|------|
| Provider Pattern | 提供者模式，用于解耦工具的提供和使用 |
| Registry Pattern | 注册表模式，集中管理所有工具的定义和信息 |
| JSON Schema | JSON 数据结构规范，用于定义工具参数和返回值格式 |
| Pydantic | Python 数据验证库，支持自动生成 JSON Schema |
| RRF（Reciprocal Rank Fusion） | 倒数排名融合算法，用于混合检索结果排序 |
| HyDE（Hypothetical Document Embeddings） | 假设性文档嵌入，提升向量检索效果 |
| SemVer | 语义化版本号规范，格式为 MAJOR.MINOR.PATCH |
| QPS | Queries Per Second，每秒查询次数 |
| LRU | Least Recently Used，最近最少使用缓存淘汰策略 |
| TTL | Time To Live，缓存生存时间 |
