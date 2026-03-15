# 高可用（High Availability）

## 概述

高可用模块提供 LLM 模型的故障切换、健康检查和负载均衡能力，确保系统在模型服务异常时能够自动切换到备用模型，保障服务的持续可用性。

## 功能需求

### 1. LLM 模型故障切换

**描述**：当主模型出现故障时，自动切换到备用模型进行服务。

**要求**：
- 支持配置多个备用模型
- 自动检测模型故障（超时、错误率过高等）
- 故障切换透明化，对上层调用方无感知
- 支持故障模型的自动恢复

### 2. 健康检查

**描述**：定期检查模型的健康状态，及时发现不可用的模型实例。

**检查内容**：
- 模型响应时间
- 模型错误率
- 模型可用性
- Quota 余额

**要求**：
- 支持主动健康检查（主动探测）
- 支持被动健康检查（基于调用结果）
- 可配置健康检查策略（间隔、阈值等）
- 支持健康状态变更事件通知

### 3. 负载均衡

**描述**：在多个可用模型之间分配请求，提高系统的整体吞吐量和响应速度。

**负载均衡策略**：
- **轮询（Round Robin）**：顺序分配请求
- **随机（Random）**：随机选择可用实例
- **最少连接（Least Connections）**：选择当前连接数最少的实例
- **响应时间（Response Time）**：优先选择响应快的实例
- **加权轮询（Weighted Round Robin）**：根据权重分配请求

**要求**：
- 支持配置负载均衡策略
- 支持实例权重配置
- 支持动态调整权重
- 支持剔除不健康实例

### 4. 高可用网关集成

**描述**：通过高可用网关实现模型服务的统一管理和调度。

**功能**：
- 模型实例注册和发现
- 最佳实例选择
- 调用结果上报和统计分析
- 实例激活和停用

### 5. 模型同步管理

**描述**：将系统中的模型配置同步到高可用网关，实现统一管理。

**同步操作**：
- 创建模型：当用户创建模型时同步到网关
- 更新模型：当模型配置变更时更新网关
- 删除模型：当模型删除时从网关移除
- 批量操作：支持模型的批量同步和删除

**要求**：
- 支持异步同步，避免阻塞主流程
- 提供同步结果反馈
- 记录同步日志，便于问题排查

### 6. 会话亲和性

**描述**：在多次交互中尽可能使用同一个模型实例，保持对话一致性。

**实现方式**：
- 基于 SessionId 进行实例绑定
- 在会话期间使用同一实例
- 实例不可用时降级到其他实例

**优势**：
- 提高上下文一致性
- 减少模型切换开销
- 提升用户体验

### 7. 降级策略

**描述**：当高可用网关不可用或选择失败时，降级到本地逻辑处理。

**降级场景**：
- 高可用功能未启用
- 网关服务不可用
- 无可用实例
- 选择超时

**降级机制**：
- 使用默认的模型和 Provider
- 记录降级日志便于监控
- 支持降级告警

### 8. 调用结果监控

**描述**：收集和上报模型调用结果，用于健康评估和决策。

**监控指标**：
- 调用成功率
- 平均响应时间
- 错误类型分布
- 调用量统计

**上报方式**：
- 实时上报：每次调用后上报结果
- 批量上报：积累一定数量后批量上报
- 定期上报：定时上报统计数据

## 技术约束

### 1. 实现方式

**部署形态**：
- **高可用网关服务**：独立 FastAPI 微服务，与主应用分离部署
- **nginx 反向代理**：使用 nginx upstream 实现负载均衡和故障转移
- **客户端侧路由**：FastAPI 中间件实现本地降级逻辑

**架构选择**：
- 主模式：独立高可用网关服务 + nginx upstream
- 降级模式：FastAPI 中间件实现本地路由
- 混合模式：两者结合，网关优先，本地降级兜底

### 2. 健康检查实现

**探测方式**：
- **HTTP Probe**：发送轻量 HTTP GET 请求到模型健康端点（如 `/health`）
- **推理探针**：发送最小化推理请求（如单 token 测试），验证实际推理能力
- **TCP 连接探测**：仅检测端口连通性，用于快速筛选

**优先级**：HTTP Probe > 推理探针 > TCP 探测

### 3. 熔断机制

**熔断器模式**：
- **错误率阈值**：默认 50%（可配置）
- **半开时间**：默认 60 秒（可配置）
- **最小请求数**：达到 10 次请求后才评估熔断
- **成功阈值**：半开状态下连续 3 次成功后恢复

### 4. 分布式协调

**分布式锁**：
- 使用 Redis RedLock 算法
- 防止多实例同时执行故障切换
- 锁超时时间：30 秒

**状态同步**：
- 健康状态存储于 Redis，TTL 5 分钟
- 事件通知通过 RabbitMQ 广播
- 配置变更使用 etcd 或 Nacos 注册中心

## 性能要求

### 1. 延迟指标（P95）

**模型选择延迟**：< 50ms（单机环境），< 100ms（集群环境）
**故障切换时间**：< 1s（检测到故障到切换完成）
**健康检查响应**：< 200ms（单次探测）
**API 响应时间**：< 200ms（不含 LLM 调用时间）

### 2. 吞吐量假设

**测试环境**：
- 单机：8 CPU, 16GB RAM, 无网络延迟
- 集群：3 节点，每节点 8 CPU, 16GB RAM，内网延迟 < 1ms

**最大 QPS**：
- 单机实例：500+ QPS
- 3 节点集群：1500+ QPS（线性扩展）

### 3. 健康检查配置

**默认间隔**：30 秒（可配置范围：5s - 300s）
**超时时间**：5 秒（HTTP Probe），10 秒（推理探针）
**并发探测**：最大并发 100 个实例
**重试策略**：失败后重试 2 次，间隔 3 秒

## 安全要求

### 1. 认证机制

**API Key 认证**：
- 网关层校验 API Key，支持按用户隔离
- API Key 加密存储（AES-256-GCM）
- 支持密钥轮换，周期建议 90 天

**mTLS（可选）**：
- 服务间通信使用 mTLS 双向认证
- 证书由平台统一颁发和管理
- 证书自动续期，过期前 30 天告警

### 2. 加密协议

**传输加密**：
- 强制 HTTPS/TLS 1.3
- 不支持 TLS 1.2 以下版本
- HSTS 头强制浏览器使用 HTTPS

**数据加密**：
- 敏感配置（API Key、密码）使用 AES-256-GCM 加密
- 密钥由 KMS（密钥管理服务）统一管理
- 支持密钥版本管理和历史追溯

### 3. 访问控制

**RBAC 权限模型**：
- 管理员：管理所有高可用配置、手动故障切换
- 普通用户：查看自己资源的健康状态
- 审计员：查看审计日志，无操作权限

**细粒度鉴权**：
- 不同用户可见不同的模型链
- 官方模型对所有用户可见
- 自定义模型仅创建者可见

### 4. 审计日志

**记录内容**：
- 所有配置变更操作（创建、更新、删除）
- 手动故障切换操作
- 权重调整操作
- 异常访问尝试

**保存期限**：至少 180 天

## 可靠性要求

### 1. 可用性指标

**系统可用性**：≥ 99.9%（年度停机时间 < 8.76 小时）
**故障恢复时间（MTTR）**：< 5 分钟
**平均无故障时间（MTBF）**：> 720 小时

### 2. 熔断参数

**熔断触发条件**（满足任一即触发）：
- 错误率 > 50%（1 分钟内）
- 连续失败次数 > 10 次
- 平均响应时间 > 10 秒（1 分钟内）

**熔断行为**：
- 立即停止向该实例分发流量
- 进入熔断状态，持续 60 秒（半开时间）
- 半开状态下放行 3 个探测请求
- 全部成功后恢复，否则继续熔断

### 3. 降级链机制

**降级配置示例**：
```json
{
  "primary_model": {
    "provider": "openai",
    "model": "gpt-4"
  },
  "fallback_chain": [
    {
      "provider": "openai",
      "model": "gpt-3.5-turbo",
      "weight": 1.0
    },
    {
      "provider": "anthropic",
      "model": "claude-3-sonnet",
      "weight": 1.0
    },
    {
      "provider": "moonshot",
      "model": "moonshot-v1-8k",
      "weight": 0.8
    }
  ],
  "trigger_conditions": {
    "consecutive_failures": 3,
    "error_rate_threshold": 0.5,
    "timeout_threshold_ms": 30000
  },
  "recovery": {
    "auto_recovery": true,
    "recovery_delay_seconds": 300,
    "health_check_interval_seconds": 30
  }
}
```

**降级策略**：
- 按配置顺序依次尝试
- 支持权重配置（0.0-1.0）
- 自动降级：满足触发条件自动切换
- 手动降级：管理员手动指定降级目标

**循环检测**：
- 定期（每 5 分钟）检测主模型健康状态
- 主模型恢复后自动切回（可配置）
- 支持手动强制锁定在降级状态

### 4. 告警规则

**告警级别**：
- P0（严重）：所有实例不可用，系统完全不可用
- P1（高）：主实例不可用，已切换到备用
- P2（中）：单个实例不健康，但不影响整体服务
- P3（低）：健康检查失败率上升，但未达阈值

**告警渠道**：
- 邮件：所有级别
- 短信/电话：P0、P1 级别
- Webhook：集成 Slack、钉钉、企业微信
- 平台内消息：所有级别

**告警收敛**：
- 相同告警 5 分钟内合并
- 告警风暴抑制（1 小时内最多发送 10 条）
- 自动恢复告警（故障恢复后自动发送恢复通知）

## 扩展性

### 1. 负载均衡策略扩展

**策略接口**：
```python
from abc import ABC, abstractmethod
from typing import List, Optional

class LoadBalanceStrategy(ABC):
    """负载均衡策略抽象基类"""
    
    @abstractmethod
    def select_instance(self, instances: List[ModelInstance]) -> Optional[ModelInstance]:
        """选择实例"""
        pass
    
    @abstractmethod
    def update_weights(self, weights: Dict[str, float]):
        """动态调整权重"""
        pass

# 内置策略
- RoundRobinStrategy (轮询)
- RandomStrategy (随机)
- LeastConnectionsStrategy (最少连接)
- ResponseTimeStrategy (响应时间优先)
- WeightedRoundRobinStrategy (加权轮询)
```

**策略注册**：
```python
# 注册自定义策略
LoadBalancerRegistry.register(
    name="custom_latency_aware",
    strategy=CustomLatencyAwareStrategy()
)
```

### 2. 健康检查算法扩展

**检查器接口**：
```python
class HealthChecker(ABC):
    """健康检查器抽象基类"""
    
    @abstractmethod
    async def check(self, instance: ModelInstance) -> HealthStatus:
        """执行健康检查"""
        pass
    
    @abstractmethod
    def get_check_interval(self) -> int:
        """获取检查间隔（秒）"""
        pass

# 内置检查器
- HTTPHealthChecker (HTTP 探测)
- InferenceHealthChecker (推理探针)
- TCPHealthChecker (TCP 连接探测)
- CompositeHealthChecker (组合检查)
```

**自定义检查器示例**：
```python
class CustomQuotaHealthChecker(HealthChecker):
    """检查 Quota 余额的健康检查器"""
    
    async def check(self, instance: ModelInstance) -> HealthStatus:
        quota = await self.query_quota_balance(instance.api_key)
        if quota < 1000:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
```

### 3. 插件式扩展

**插件机制**：
- 使用 Python entry_points 发现插件
- 支持热加载新插件，无需重启服务
- 插件版本兼容性检查

**扩展点**：
- 负载均衡策略插件
- 健康检查器插件
- 告警通知渠道插件
- 监控指标收集器插件

### 4. 模型类型支持

**支持的模型类型**：
- CHAT：对话模型（GPT-4、Claude 等）
- EMBEDDING：嵌入模型（text-embedding 等）
- IMAGE_GENERATION：图像生成模型（DALL-E 3 等）
- SPEECH_TO_TEXT：语音识别模型（Whisper 等）
- TEXT_TO_SPEECH：语音合成模型

**新增模型类型**：
只需在 ModelType 枚举中添加，无需修改核心代码
