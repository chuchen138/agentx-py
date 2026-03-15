# 内置工具技术设计

## 概述

内置工具模块采用工具提供者模式（Provider Pattern）和注册表模式（Registry Pattern），使用 Python FastAPI 技术栈实现。通过依赖注入和元类编程实现工具的自动注册和动态扩展，为 Agent 和其他模块提供结构化的工具调用能力。

## 技术架构

### 整体架构

内置工具模块由工具调用方、工具注册表、工具提供者三部分组成。BuiltInToolRegistry 作为工具注册表（单例模式），维护工具注册表和管理工具提供者。通过实现 BuiltInToolProvider 抽象基类，可以添加新的工具提供者（如 RAG、System、MCP Provider）。

**架构分层**：
- **API 层**：FastAPI 路由，处理 HTTP 请求
- **应用层**：ToolExecutor 协调工具执行
- **领域层**：BuiltInToolRegistry + BuiltInToolProvider
- **基础设施层**：缓存、监控、日志、安全沙箱

### 设计模式

#### 提供者模式（Provider Pattern）

将工具的提供和使用分离，通过 BuiltInToolProvider 抽象基类定义提供者接口，RagBuiltInToolProvider、SystemBuiltInToolProvider 等实现具体工具提供，BuiltInToolRegistry 管理注册表，支持动态添加工具提供者。

**Python 实现**：
```python
from abc import ABC, abstractmethod
from typing import List, Type

class BuiltInToolProvider(ABC):
    """工具提供者抽象基类"""
    
    @abstractmethod
    def get_tools(self) -> List[Type['BaseTool']]:
        """获取该提供者提供的所有工具类"""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """提供者名称"""
        pass
```

#### 注册表模式（Registry Pattern）

集中管理所有工具，提供统一的查找接口。BuiltInToolRegistry 作为工具注册表（使用 Borg 模式实现单例），使用线程安全的字典存储工具定义，支持工具的动态注册和查询。

**Python 实现**：
```python
import threading
from typing import Dict, Optional, List

class BuiltInToolRegistry:
    """工具注册表（单例模式）"""
    _instance = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._providers: List[BuiltInToolProvider] = []
        self._cache = LRUCache(max_size=1000)
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def register_tool(self, tool_def: ToolDefinition) -> None:
        """注册工具到注册表"""
        pass
    
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        """根据工具名称获取工具定义"""
        pass
```

#### 装饰器模式（Decorator Pattern）

使用装饰器实现工具提供者的自动发现和注册。

**Python 实现**：
```python
from functools import wraps

def register_provider(provider_class: Type[BuiltInToolProvider]) -> Type[BuiltInToolProvider]:
    """工具提供者注册装饰器"""
    @wraps(provider_class)
    def wrapper(*args, **kwargs):
        instance = provider_class(*args, **kwargs)
        registry = BuiltInToolRegistry()
        registry.register_provider(instance)
        return instance
    return wrapper
```

## 核心组件

### BuiltInToolRegistry

维护工具注册表，管理工具提供者，提供工具查询和获取接口。

**关键成员**：
- `_tools: Dict[str, ToolDefinition]` - 工具注册表（名称 -> 定义）
- `_providers: List[BuiltInToolProvider]` - 工具提供者列表
- `_cache: LRUCache` - LRU 缓存（TTL 可配置）
- `_lock: threading.RLock` - 读写锁（保证并发安全）

**关键方法**：
- `register_tool(tool_def: ToolDefinition)` - 注册工具
- `register_provider(provider: BuiltInToolProvider)` - 注册提供者
- `get_tool(tool_name: str) -> Optional[ToolDefinition]` - 获取工具
- `list_tools(filters: dict) -> List[ToolDefinition]` - 查询工具列表
- `enable_tool(tool_name: str)` - 启用工具
- `disable_tool(tool_name: str)` - 禁用工具

### BuiltInToolProvider

定义工具提供者接口，提供工具的获取和查询能力，支持提供者的动态加载。

**关键方法**：
- `get_tools() -> List[Type[BaseTool]]` - 获取所有工具类
- `get_tool(tool_name: str) -> Optional[Type[BaseTool]]` - 获取指定工具
- `provider_name() -> str` - 提供者名称

### RagBuiltInToolProvider

提供 RAG 检索工具，实现向量检索、关键词检索和混合检索。

**工具列表**：
- `rag_search` - 向量检索工具（使用 PGVector/Milvus）
- `rag_hybrid_search` - 混合检索工具（RRF 融合算法）
- `rag_keyword_search` - 关键词检索工具（BM25 算法）

**依赖**：RAGSearchAppService（应用服务）

### SystemBuiltInToolProvider

提供系统级别的内置工具。

**工具列表**：
- `file_read` - 读取文件内容
- `file_write` - 写入文件内容
- `file_delete` - 删除文件
- `file_list` - 列出目录内容
- `data_parse` - 解析 JSON/YAML 数据
- `system_info` - 查询系统信息

### ToolExecutor

定义工具调用接口，实现对参数验证、工具调用逻辑执行和结果返回。

**关键方法**：
- `execute(tool_name: str, params: dict) -> ToolResult` - 执行工具调用
- `validate_parameters(tool_name: str, params: dict) -> bool` - 验证参数合法性
- `async_execute(tool_name: str, params: dict, timeout: int) -> ToolResult` - 异步执行

**DefaultToolExecutor 实现**：
- 从 Registry 获取 ToolDefinition
- 使用 Pydantic 验证参数
- 调用工具 execute 方法
- 处理异常和超时
- 记录审计日志

## 工具注册

系统启动时，Python 自动扫描所有标记 `@register_provider` 装饰器的类并实例化，注册到 BuiltInToolRegistry。

**注册流程**：
1. Bootstrap 初始化 BuiltInToolRegistry（单例）
2. 扫描 `app.application.tool.providers` 包
3. 发现所有 `@register_provider` 装饰的类
4. 实例化提供者类
5. 调用 `provider.get_tools()` 获取工具列表
6. 逐个注册工具到 Registry（检查名称冲突）
7. 记录注册日志

**代码示例**：
```python
# app/core/bootstrap.py
def init_builtin_tools():
    registry = BuiltInToolRegistry()
    
    # 自动扫描 providers 包
    provider_module = importlib.import_module('app.application.tool.providers')
    for name, obj in inspect.getmembers(provider_module):
        if inspect.isclass(obj) and hasattr(obj, '_registered_provider'):
            provider = obj()
            tools = provider.get_tools()
            for tool_class in tools:
                tool_def = tool_class.to_definition()
                registry.register_tool(tool_def)
```

## 工具查询

通过工具名称从注册表获取工具定义，验证参数合法性，调用工具执行逻辑，返回工具结果。支持按类型列表查询工具，过滤并返回符合条件的工具列表。

**查询流程**：
1. 接收查询请求（tool_name 或 filters）
2. 检查黑名单（如果工具在黑名单中拒绝）
3. 从缓存获取工具定义（未命中则从注册表查询）
4. 验证用户权限
5. 返回工具定义或列表

**缓存策略**：
- 使用 `functools.lru_cache` 或 `aiocache`
- TTL 默认 5 分钟
- LRU 淘汰策略
- 支持手动刷新缓存

## 工具执行接口

ToolExecutor 定义工具调用接口，实现对参数验证、工具调用逻辑执行和结果返回。

**接口定义**：
```python
class ToolExecutor(ABC):
    @abstractmethod
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        """执行工具调用"""
        pass
    
    @abstractmethod
    def validate_parameters(self, tool_name: str, params: dict) -> bool:
        """验证参数合法性"""
        pass
```

**DefaultToolExecutor 实现**：
```python
class DefaultToolExecutor(ToolExecutor):
    def __init__(self, registry: BuiltInToolRegistry):
        self.registry = registry
        self.semaphore = asyncio.Semaphore(100)  # 最大并发数
    
    async def execute(self, tool_name: str, params: dict) -> ToolResult:
        # 1. 获取工具定义
        tool_def = self.registry.get_tool(tool_name)
        if not tool_def:
            raise ToolNotFoundException(tool_name)
        
        # 2. 验证参数
        self.validate_parameters(tool_name, params)
        
        # 3. 执行工具（带超时控制）
        try:
            async with self.semaphore:
                result = await asyncio.wait_for(
                    tool_def.execute(params),
                    timeout=30
                )
                return result
        except asyncio.TimeoutError:
            raise ToolTimeoutException(tool_name)
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            raise ToolExecutionException(tool_name, str(e))
```

**参数验证**：
- 使用 Pydantic 模型验证
- JSON Schema 校验
- 必需参数检查
- 值域范围验证

## 配置设计

内置工具配置使用 Pydantic Settings，支持从环境变量读取。

**配置类**：
```python
from pydantic_settings import BaseSettings

class ToolSettings(BaseSettings):
    # 工具启用开关
    enabled: bool = True
    
    # 注册表缓存配置
    cache_ttl: int = 300  # 5 分钟
    cache_size: int = 1000
    
    # RAG 检索参数配置
    rag_default_top_k: int = 5
    rag_max_top_k: int = 20
    rag_similarity_threshold: float = 0.7
    rag_use_rerank: bool = False
    rag_hybrid_weight: float = 0.5
    
    # 工具执行参数配置
    tool_timeout: int = 30  # 秒
    max_concurrency: int = 100
    retry_count: int = 3
    
    # 黑名单配置
    blacklist: List[str] = []
    
    # 日志配置
    log_level: str = "INFO"
    log_sample_rate: float = 1.0
    
    class Config:
        env_prefix = "TOOL_"
        env_file = ".env"
```

**使用方式**：
```python
settings = ToolSettings()
registry = BuiltInToolRegistry(cache_ttl=settings.cache_ttl)
executor = DefaultToolExecutor(registry, timeout=settings.tool_timeout)
```

## 关键流程

### 工具注册流程

```
系统启动
  ↓
Bootstrap 初始化 BuiltInToolRegistry
  ↓
扫描 providers 包
  ↓
发现 @register_provider 装饰的类
  ↓
实例化提供者
  ↓
调用 provider.get_tools()
  ↓
遍历工具列表
  ↓
检查名称冲突
  ↓
注册到 Registry
  ↓
记录日志
  ↓
完成注册
```

### 工具调用流程

```
Agent/用户调用工具
  ↓
API 层接收请求
  ↓
ToolExecutor.execute(tool_name, params)
  ↓
检查黑名单
  ↓
从 Registry 获取 ToolDefinition
  ↓
验证参数（Pydantic）
  ↓
检查权限
  ↓
执行工具逻辑
  ↓
处理超时/异常
  ↓
记录审计日志
  ↓
返回结果
```

## 错误处理

### 异常类型

**ToolNotFoundException**：
- 调用不存在的工具
- HTTP 状态码：404

**InvalidParameterException**：
- 缺少必需参数
- 参数类型错误
- 参数值超出范围
- HTTP 状态码：400

**ToolExecutionException**：
- 工具内部逻辑错误
- 外部依赖不可用
- HTTP 状态码：500

**ToolTimeoutException**：
- 执行超时
- HTTP 状态码：504

**ProviderRegistrationException**：
- 工具名称冲突
- 提供者初始化失败
- HTTP 状态码：500

**PermissionDeniedException**：
- 用户权限不足
- HTTP 状态码：403

### 错误处理策略

```python
try:
    result = await executor.execute(tool_name, params)
except ToolNotFoundException as e:
    return JSONResponse(status_code=404, content={"error": str(e)})
except InvalidParameterException as e:
    return JSONResponse(status_code=400, content={"error": str(e)})
except ToolTimeoutException as e:
    return JSONResponse(status_code=504, content={"error": str(e)})
except PermissionDeniedException as e:
    return JSONResponse(status_code=403, content={"error": str(e)})
except Exception as e:
    logger.exception("Unexpected error")
    return JSONResponse(status_code=500, content={"error": "Internal server error"})
```

## 性能优化

### 工具缓存

**LRU Cache**：
- 使用 `functools.lru_cache` 或 `aiocache`
- 缓存工具定义（避免重复查询）
- TTL 默认 5 分钟
- 支持手动刷新

```python
from functools import lru_cache

class BuiltInToolRegistry:
    @lru_cache(maxsize=1000)
    def get_tool(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._tools.get(tool_name)
```

### 并发执行

**Asyncio + Semaphore**：
- 使用 `asyncio.gather` 并发执行多个工具
- 使用 `asyncio.Semaphore` 限制最大并发数
- 避免资源耗尽

```python
class DefaultToolExecutor:
    def __init__(self, max_concurrency: int = 100):
        self.semaphore = asyncio.Semaphore(max_concurrency)
    
    async def execute_batch(self, tool_calls: List[dict]) -> List[ToolResult]:
        tasks = [
            self.execute(call["tool_name"], call["params"])
            for call in tool_calls
        ]
        return await asyncio.gather(*tasks, return_exceptions=True)
```

### 检索优化

**RAG 检索加速**：
- 向量检索使用索引加速（ivfflat / HNSW）
- 结果缓存（Redis）
- 批量检索减少网络往返
- RRF 融合算法优化（并行执行）

```python
async def hybrid_search(query: str, top_k: int) -> List[Result]:
    # 并发执行向量检索和关键词检索
    vector_results, keyword_results = await asyncio.gather(
        vector_search(query, top_k),
        keyword_search(query, top_k)
    )
    
    # RRF 融合
    return rrf_fusion(vector_results, keyword_results, k=60)
```

## 监控指标

### 关键指标

**工具调用指标**（Prometheus）：
```python
from prometheus_client import Counter, Histogram

# 工具调用次数
tool_invocations = Counter(
    'builtin_tool_invocations_total',
    'Total tool invocations',
    ['tool_name', 'provider', 'status']
)

# 工具调用耗时
tool_duration = Histogram(
    'builtin_tool_duration_seconds',
    'Tool execution duration',
    ['tool_name'],
    buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0]
)

# RAG 检索指标
rag_requests = Counter('rag_requests_total', 'Total RAG requests')
rag_duration = Histogram('rag_duration_seconds', 'RAG search duration')
rag_results = Histogram('rag_results_count', 'RAG results count', buckets=[1, 5, 10, 20, 50])
```

**监控仪表板**（Grafana）：
- 各工具调用次数、平均响应时间、成功/失败率
- RAG 检索请求数、平均检索时间、平均结果数
- 各提供者的健康状态、工具注册数量
- 缓存命中率、并发数

### 告警规则

```yaml
# config/alerts/tool_alerts.yaml
groups:
  - name: builtin_tools
    rules:
      - alert: HighToolFailureRate
        expr: rate(builtin_tool_invocations_total{status="error"}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "工具调用失败率过高"
          
      - alert: HighRagLatency
        expr: histogram_quantile(0.95, rate(rag_duration_seconds_bucket[5m])) > 1
        for: 5m
        annotations:
          summary: "RAG 检索延迟过高 (P95 > 1s)"
          
      - alert: HighParameterValidationFailures
        expr: rate(builtin_tool_validation_failures_total[5m]) > 100
        for: 5m
        annotations:
          summary: "参数验证失败频繁"
```

### 日志记录

**结构化日志**（JSON 格式）：
```python
import json
import logging
from pythonjsonlogger import jsonlogger

logger = logging.getLogger('tool_logger')
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(jsonlogger.JsonFormatter())
logger.addHandler(handler)

# 记录工具调用日志
def log_tool_invocation(tool_name: str, params: dict, result: dict, duration: float, user_id: str):
    logger.info({
        "event": "tool_invocation",
        "tool_name": tool_name,
        "params": sanitize_params(params),  # 脱敏
        "result": result,
        "duration_ms": duration * 1000,
        "user_id": user_id,
        "trace_id": get_trace_id()
    })
```

## 扩展性

### 新增工具提供者

**步骤**：
1. 创建类继承 `BuiltInToolProvider`
2. 实现 `get_tools()` 方法
3. 使用 `@register_provider` 装饰器
4. 系统启动时自动发现并注册

**示例**：
```python
from app.domain.tool.provider import BuiltInToolProvider, register_provider

@register_provider
class CustomToolProvider(BuiltInToolProvider):
    @property
    def provider_name(self) -> str:
        return "custom_provider"
    
    def get_tools(self) -> List[Type[BaseTool]]:
        return [CustomTool1, CustomTool2, CustomTool3]
```

### 热注册工具

**API 端点**：
```python
@app.post("/api/v1/tools/builtin/register")
async def register_tool(tool_def: ToolDefinition):
    registry = BuiltInToolRegistry()
    registry.register_tool(tool_def)
    return {"message": "Tool registered successfully"}
```

### 插件化架构

**插件接口**：
```python
class ToolPlugin(ABC):
    @abstractmethod
    def install(self) -> None:
        """安装插件"""
        pass
    
    @abstractmethod
    def uninstall(self) -> None:
        """卸载插件"""
        pass
```

未来支持从市场下载和安装工具插件，插件在沙箱环境中运行。

### 分布式扩展

**多实例部署**：
- 使用 Redis Cluster 共享工具定义缓存
- 一致性 Hash 分配工具调用
- 负载均衡（轮询、最少连接）

**服务发现**：
- 集成 Consul 或 etcd
- 健康检查
- 自动故障转移

## 安全设计

### 参数注入防护

**JSON Schema 严格校验**：
```python
from pydantic import ValidationError

def validate_parameters(self, tool_name: str, params: dict) -> bool:
    tool_def = self.registry.get_tool(tool_name)
    try:
        tool_def.parameters(**params)  # Pydantic 自动验证
        return True
    except ValidationError as e:
        raise InvalidParameterException(str(e))
```

**命令注入防护**：
- 禁止执行系统命令（os.system, subprocess）
- 使用白名单验证参数

**SQL 注入防护**：
- 使用 SQLAlchemy 参数化查询
- 禁止字符串拼接 SQL

**路径遍历防护**：
```python
from pathlib import Path

def safe_file_read(file_path: str) -> str:
    # 限制访问范围
    allowed_base = Path("/allowed/path")
    target_path = Path(file_path).resolve()
    
    if not str(target_path).startswith(str(allowed_base)):
        raise SecurityException("Path traversal detected")
    
    return target_path.read_text()
```

### 沙箱执行

**文件系统隔离**：
- 限制工具访问的文件路径
- 使用 chroot 模拟

**资源限制**：
```python
import resource

def limit_resources():
    # 限制 CPU 时间
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    # 限制内存
    resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024, 1024*1024*1024))
    # 限制文件描述符
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
```

**网络访问控制**：
- 禁止工具访问外部网络
- 白名单域名例外

### 敏感信息保护

**参数脱敏**：
```python
def sanitize_params(params: dict) -> dict:
    sensitive_keys = ['password', 'token', 'secret', 'api_key']
    sanitized = params.copy()
    
    for key in sensitive_keys:
        if key in sanitized:
            sanitized[key] = "***REDACTED***"
    
    return sanitized
```

**结果过滤**：
- 使用正则表达式过滤银行卡号、手机号等
- 防止数据泄露

### 黑名单机制

```python
class BuiltInToolRegistry:
    def __init__(self):
        self._blacklist = set(settings.blacklist)
    
    def is_blacklisted(self, tool_name: str) -> bool:
        return tool_name in self._blacklist
    
    def add_to_blacklist(self, tool_name: str) -> None:
        self._blacklist.add(tool_name)
    
    def remove_from_blacklist(self, tool_name: str) -> None:
        self._blacklist.discard(tool_name)
```

### 审计日志

**记录内容**：
- 工具调用详细信息（工具名、参数、结果、耗时）
- 用户 ID 和 Trace ID
- 安全事件（权限拒绝、参数非法、黑名单命中）

**日志保留**：
- 至少 180 天
- 支持按用户、工具、时间范围查询

## 相关模块集成

- **007-tool-integration**：MCP 工具集成，内置工具与 MCP 工具命名空间隔离
- **008-rag-management**：RAG 检索工具依赖 RAGSearchAppService
- **019-account-billing**：记录工具调用用量用于计费
- **016-execution-trace**：工具调用链路追踪

## 技术术语

| 术语 | 说明 |
|-----|------|
| Provider Pattern | 提供者模式，用于解耦工具的提供和使用 |
| Registry Pattern | 注册表模式，集中管理所有工具的定义和信息 |
| JSON Schema | JSON 数据结构规范，用于定义工具参数和返回值格式 |
| Pydantic | Python 数据验证库，支持自动生成 JSON Schema |
| RRF（Reciprocal Rank Fusion） | 倒数排名融合算法，用于混合检索结果排序 |
| LRU | Least Recently Used，最近最少使用缓存淘汰策略 |
| TTL | Time To Live，缓存生存时间 |
| QPS | Queries Per Second，每秒查询次数 |
