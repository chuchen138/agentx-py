# MCP 支持（MCP Support）- 设计文档

## 架构设计

### 整体架构

MCP 支持模块采用服务化设计，通过 McpUrlProviderService 协调容器管理和 URL 构建。McpUrlProviderService 提供 MCP 工具 URL 的统一获取接口，自动判断工具类型并选择策略，隐藏容器管理的复杂性。

### 实现结构

```
app/
├── application/
│   └── mcp/
│       └── mcp_url_provider_service.py  # MCP URL 提供服务
├── domain/
│   └── mcp/
│       ├── enums.py                    # 枚举类定义
│       ├── models.py                   # 领域模型
│       ├── protocol_adapter.py         # 协议适配器抽象基类
│       └── tool_classifier.py          # 工具类型判断器
├── api/
│   └── v1/
│       └── mcp/
│           ├── __init__.py
│           └── routes.py               # MCP 相关 API 路由
└── infrastructure/
    └── mcp/
        ├── container_service.py        # 容器服务（模拟实现）
        ├── sse_manager.py              # SSE 连接管理器
        ├── url_builder.py              # URL 构建器
        └── protocol/
            ├── adapter_factory.py      # 协议适配器工厂
            └── v1_0_adapter.py         # MCP 1.0 协议适配器
```

### 核心组件

McpUrlProviderService 职责包括 MCP 工具 URL 提供、工具类型判断（全局/用户）、容器协调和 URL 构建。关键方法包括 getSSEUrl（智能获取 URL）、buildUserContainerSSEUrl（用户容器 URL）、buildReviewContainerSSEUrl（审核容器 URL）。

**内部策略切换逻辑**:
```python
class McpUrlProviderService:
    def getSSEUrl(self, tool_name: str, user_id: str) -> str:
        tool_type = self.tool_classifier.classify(tool_name)
        
        if tool_type == ToolType.GLOBAL:
            container = self.container_service.get_review_container()
            return self.url_builder.build_review_container_url(container)
        elif tool_type == ToolType.USER:
            container = self.container_service.get_or_create_user_container(user_id)
            return self.url_builder.build_user_container_url(container)
        else:  # EXTERNAL
            server = self.server_manager.get_server_for_tool(tool_name)
            return server.server_url
```

## 设计模式

服务提供者模式通过 McpUrlProviderService 作为服务提供者，自动判断工具类型并选择策略，隐藏容器管理的复杂性。工厂模式根据工具类型创建不同类型的 URL，包括用户工具 URL 工厂、全局工具 URL 工厂和支持自定义 URL 构建器。

## 技术实现

工具类型判断通过查询工具信息判断是否为全局工具，异常时默认为用户工具。智能 URL 获取自动判断工具类型，全局工具使用审核容器，用户工具需要用户容器。

用户容器 URL 构建流程包括获取或创建用户容器、检查容器状态、容器未运行时启动容器并等待就绪、构建 SSE URL。getOrCreateUserContainer 方法查找现有容器，无则创建新容器，返回现有容器的第一个。

审核容器 URL 构建流程包括获取审核容器、验证容器状态、构建 SSE URL。

## 配置设计

MCP 支持配置包括 URL 构建配置、容器集成配置、工具判断配置、SSE 连接配置和协议配置。URL 构建配置包括默认协议、默认端口、路径前缀。容器集成配置包括集成开关、自动创建、自动启动、停止空闲超时、用户容器模板、审核容器名称、共享状态。工具判断配置包括缓存开关、缓存 TTL、默认降级为用户工具。SSE 连接配置包括连接超时、心跳间隔、最大并发连接数。协议配置包括 MCP 协议版本和支持的事件类型。

## 关键流程

工具调用流程包括 Agent/用户调用 MCP 工具、McpUrlProviderService.getSSEUrl 判断工具类型并选择连接策略、用户工具流程（getOrCreateUserContainer 查找或创建容器、检查容器状态、启动容器（如需要）、等待容器就绪、构建 SSE URL）或全局工具流程（getReviewContainer 获取共享审核容器、验证容器状态、构建 MCP 路径 URL）、建立 SSE 连接（遵循 MCP 协议）、发送工具调用请求、接收返回结果。

## 错误处理

异常类型包括工具不存在（返回 404 错误）、容器创建失败（返回 500 错误，记录详细日志）、容器启动超时（放弃并返回超时错误）、审核容器不可用（返回服务不可用错误）、SSE 连接失败（尝试重连，超过次数后返回错误）。

## 性能优化

容器复用策略包括用户工具容器复用（同一用户的同一工具复用容器）、定期清理不活跃的容器、容器预热提高响应速度。工具信息缓存包括缓存工具类型判断结果、缓存工具的服务器信息、使用合理的 TTL 策略。SSE 连接复用包括支持长连接、减少连接握手开销、连接池管理。

### 容器预热机制

**预热器触发器**:
- `@PostConstruct` 应用启动时
- `@Scheduled(cron="0 */30 * * * *")` 高峰时段 (9AM-9PM)
- 事件驱动：`ContainerPoolLowEvent` 当容器数量 < 阈值

**预热算法**:
```python
def preheat_containers():
    current_audit = count_available_review_containers()
    current_user = count_available_user_containers()
    
    if current_audit < AUDIT_MIN_POOL_SIZE:
        create_review_containers(AUDIT_MIN_POOL_SIZE - current_audit)
    
    for user in get_active_users():
        user_containers = count_user_containers(user.id)
        if user_containers < USER_MIN_PER_USER:
            create_user_container(user.id)
```

**配置参数**:
- AUDIT_MIN_POOL_SIZE: 2
- USER_MIN_PER_USER: 1
- PEAK_HOURS: 9-21 (9AM-9PM)

## 监控指标

关键监控指标包括容器创建成功率、容器启动成功率、容器平均启动时间、工具连接成功率、SSE 连接建立时间、容器资源使用情况（CPU、内存）、活跃容器数量、空闲容器清理频率、工具类型判断准确率、缓存命中率。

### 监控阈值与告警规则

**告警规则**:
- 缓存命中率 < 80% 持续 10 分钟 → WARNING
- 容器启动时间 > 30s (p95) → WARNING
- SSE 连接失败 > 10 次/分钟 → CRITICAL
- 工具调用错误率 > 5% 持续 5 分钟 → WARNING
- 连接池利用率 > 90% → CRITICAL
- 容器利用率 > 80% 持续 5 分钟 → WARNING (触发扩容)
- 服务器健康检查失败 → CRITICAL

**Dashboard 面板**:
- 实时数据：活跃连接数、活跃容器数、调用次数/分钟
- 历史趋势：成功率、延迟百分位数 (p50/p95/p99)、缓存命中率
- 资源使用：CPU 使用率、内存使用率、网络 IO

### 扩展接口设计

**协议适配器接口**:
```python
class MCPProtocolAdapter(ABC):
    @abstractmethod
    async def connect(self, server_url: str) -> Connection:
        """建立与 MCP 服务器的连接"""
        pass
    
    @abstractmethod
    async def discover_tools(self) -> List[ToolDefinition]:
        """发现可用工具列表"""
        pass
    
    @abstractmethod
    async def call_tool(self, tool_name: str, args: dict) -> ToolResult:
        """调用指定工具"""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """断开连接并清理资源"""
        pass
```

**容器模板注册**:
```python
class ContainerTemplate(BaseModel):
    name: str
    dockerfile_path: str
    env_vars: dict[str, str]
    exposed_ports: list[int]
    resource_limits: ResourceLimits
    validation_schema: dict  # JSON Schema

class TemplateRegistry:
    def register(template: ContainerTemplate):
        validate_template(template)
        save_to_db(template)
    
    def get_template(name: str) -> ContainerTemplate:
        return load_from_db(name)
```

## 安全考虑

容器隔离通过用户工具容器独立、审核容器共享但权限控制实现。访问控制限制容器操作为管理员或拥有者。SSE 连接安全使用 HTTPS、心跳验证、连接超时控制。工具验证严格检查工具名称和权限，防止非法访问。日志审计记录容器创建、启动、停止、工具连接等关键操作。

### 资源滥用防护

**配额管理**:
- 每用户最大并发容器数：5 个
- 动态配额调整基于用户等级:
  - 免费用户：2 个容器
  - 专业用户：5 个容器
  - 企业用户：20 个容器
- 速率限制器集成 (基于 Redis sliding window)

**JWT Token 刷新机制**:
- Token 嵌入在 SSE URL 查询参数中
- 每次重连时刷新 (短效 token，TTL 15 分钟)
- 用户登出时吊销 token
- 支持 token 续期 (活跃连接自动刷新)

### 容器安全加固

**运行时保护**:
- 只读文件系统
- 禁止特权模式
- 丢弃危险 capabilities
- seccomp 限制系统调用
- cgroups 资源限制

**网络安全**:
- 容器间隔离 (bridge 网络)
- 端口映射控制
- 禁止 --network=host
- 入站流量白名单
