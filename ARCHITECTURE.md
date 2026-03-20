# AgentX 架构设计文档

## 1. 整体架构

AgentX 采用分层架构设计，将系统分为前端、后端 API、服务层和数据层四个主要部分。系统通过 MCP (Model Context Protocol) 实现工具和服务的集成，通过容器化技术实现用户隔离的运行环境，通过高可用网关实现 LLM 服务的智能路由和故障转移。

### 1.1 架构层次

```
┌─────────────────────────────────────────┐
│         前端应用层                       │
│  (React 18 + TypeScript + Ant Design)   │
└────────────────┬────────────────────────┘
                 │ HTTPS
┌────────────────▼────────────────────────┐
│         API 网关层                        │
│  (FastAPI + JWT 认证 + 限流)             │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         业务服务层                       │
│  ┌─────────────────────────────────┐    │
│  │ 用户管理 | Agent 管理 | 对话管理  │    │
│  │ LLM 管理 | 工具集成 | RAG 管理    │    │
│  │ 记忆管理 | 容器管理 | 计费管理    │    │
│  │ MCP 支持 | 高可用 | 定时任务      │    │
│  └─────────────────────────────────┘    │
└────────────────┬────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  数据持久层   │  │  容器运行层   │
│  PostgreSQL  │  │  Docker       │
│  Redis 缓存   │  │  MCP Gateway  │
│  向量数据库   │  │  用户隔离     │
└──────────────┘  └──────────────┘
        │                 │
        ▼                 ▼
┌──────────────┐  ┌──────────────┐
│  消息队列     │  │  外部服务     │
│  RabbitMQ    │  │  LLM 服务商    │
│  异步任务     │  │  GitHub       │
│  事件驱动     │  │  支付平台     │
└──────────────┘  └──────────────┘
```

### 1.2 核心架构特性

- **多租户隔离**：用户数据严格隔离，每个用户拥有独立的容器运行环境
- **事件驱动架构**：基于领域事件的解耦设计，支持异步处理和扩展
- **高可用设计**：LLM 服务支持故障转移、负载均衡和健康检查
- **容器化部署**：基于 Docker 的容器化管理，支持动态创建和清理
- **MCP 协议集成**：遵循 Model Context Protocol 标准化工具接口
- **微服务就绪**：模块化设计，支持向微服务架构演进

## 2. 核心模块设计

### 2.1 用户管理模块 (User Management)

- **功能**：用户账户全生命周期管理，包括注册、登录、认证、个性化设置等
- **核心能力**：
  - **用户账户管理**：用户信息的 CRUD、角色管理、资料维护
  - **登录认证**：支持普通登录（邮箱/手机）、第三方登录（GitHub OAuth2）
  - **用户注册**：邮箱/手机号注册、验证码验证、密码加密存储
  - **密码找回**：邮箱验证码验证、安全重置密码
  - **用户设置**：默认模型配置、降级链策略、个性化偏好设置
- **安全机制**：
  - JWT Token 会话管理
  - BCrypt 密码加密
  - 多因素认证支持
  - 登录方式可配置开关
- **数据流**：
  1. 用户提交登录/注册请求
  2. 认证服务验证凭据
  3. 生成 JWT Token
  4. 后续请求携带 token 进行权限验证

### 2.2 Agent 管理模块 (Agent Management)

- **功能**：AI 智能体全生命周期管理，包括创建、配置、版本控制、发布审核、Widget 嵌入等
- **核心能力**：
  - **智能体基础管理**：创建、查询、更新、删除、状态管理
  - **版本管理与发布审核**：语义化版本号、版本快照、审核流程、状态机流转
  - **Widget 配置与嵌入**：Agent/RAG 类型 Widget、域名白名单、调用限制、嵌入代码生成
  - **工作空间管理**：添加 Agent 到工作区、LLM 模型参数配置、Token 溢出策略
  - **系统提示词生成**：AI 辅助生成高质量系统提示词
  - **能力集成**：工具集成、知识库集成、多模态支持
- **版本规范**：
  - 版本号遵循 `x.y.z` 格式（如 1.0.0）
  - 每个版本保存完整配置快照
  - 发布到市场需经过审核流程（审核中→已发布→拒绝→下架）
- **安全控制**：
  - 基于用户 ID 的数据隔离
  - Widget 域名白名单访问控制
  - 每日调用次数限制
  - 工具和知识库引用权限验证

### 2.3 LLM 管理模块 (LLM Management)

- **功能**：管理多服务商支持、协议适配、模型配置和高可用切换
- **核心能力**：
  - **多服务商支持**：官方服务商、用户自定义服务商、混合模式
  - **协议适配器**：OpenAI 协议、Moonshot 协议、Azure OpenAI 协议等
  - **模型管理**：对话模型 (CHAT)、嵌入模型 (EMBEDDING)、服务商 - 模型聚合根
  - **高可用网关**：智能路由、会话亲和性、负载均衡、故障转移、降级机制
  - **性能监控**：调用结果上报、健康度评估、动态调整路由策略
  - **模型同步**：创建/更新/删除时同步到高可用网关、批量操作支持
- **领域事件**：
  - ModelCreatedEvent、ModelUpdatedEvent、ModelDeletedEvent
  - ModelStatusChangedEvent、ModelsBatchDeletedEvent
- **配置管理**：
  - API Key 加密存储、掩码显示
  - 协议验证、必填校验、格式校验
- **权限与安全**：
  - 用户级资源隔离（仅创建者可见）
  - 官方资源对所有用户可见
  - 管理员可管理所有资源

### 2.4 对话管理模块 (Conversation Management)

- **功能**：管理和处理用户与智能体之间的所有交互，支持多种聊天模式、会话管理、消息处理
- **核心能力**：
  - **多种聊天模式**：
    - 标准对话模式：基于 LLM 的基础问答，自动维护上下文
    - Agent 智能体模式：支持工具调用的复杂任务处理、工作流管理
    - RAG 检索增强模式：知识库问答、智能文档检索、重排序
    - 预览模式：智能体预览测试、快速验证配置
  - **会话管理**：会话创建/初始化、消息持久化、上下文管理、Token 追踪、摘要生成
  - **消息处理**：文本消息、工具调用消息、任务执行消息、RAG 处理消息
  - **流式响应**：SSE 协议支持、逐 Token 输出、低延迟响应、中断控制
  - **记忆管理**：从对话中提取关键信息、语义相似度检索、记忆注入到系统提示
  - **执行跟踪**：Agent 执行过程追踪、模型调用记录、工具调用详情、Token 统计
  - **多模态支持**：文件上传、图片等多模态内容理解、文件 URL 管理
  - **高可用支持**：模型故障转移、服务商高可用策略、故障恢复
  - **计费与配额**：Token 使用量统计、实时余额检查、用量记录持久化
- **消息类型**：TEXT、TOOL\_CALL、TASK\_EXEC、RAG 各阶段状态消息
- **消息角色**：USER、SYSTEM、ASSISTANT、SUMMARY（历史消息）

### 2.5 工具集成模块 (Tool Integration)

- **功能**：第三方工具接入能力，支持用户上传管理自定义工具，通过 MCP 协议实现工具发现、部署、审核和发布
- **核心能力**：
  - **工具接入流程**：GitHub 仓库接入、MCP 协议兼容、自动化部署
  - **GitHub 验证**：仓库存在性、引用有效性、路径有效性、MCP 规范验证
  - **工具部署**：解析安装命令、部署到审核容器、获取工具定义列表
  - **工具审核**：自动化检查（GitHub 验证、部署、工具定义获取）、人工审核
  - **工具发布**：版本管理（语义化版本号）、版本快照、发布到工具市场
  - **工具安装与卸载**：一键安装、版本升级、卸载限制（不可卸载自己创建的工具）
- **状态机流转**：
  WAITING\_REVIEW → GITHUB\_URL\_VALIDATE → DEPLOYING → FETCHING\_TOOLS → MANUAL\_REVIEW → APPROVED/FAILED
- **异步处理能力**：
  - 长期运行操作（部署、获取工具列表）采用异步处理
  - 使用线程池异步执行状态处理器
  - 失败时自动更新状态为 FAILED 并记录错误信息
- **审核容器隔离**：
  - 工具部署到专用审核容器，与生产环境隔离
  - 确保审核过程安全稳定
- **工具市场**：
  - 工具列表分页展示、搜索、推荐
  - 工具详情查看（版本历史、安装数量）
  - 一键安装/卸载工具

### 2.6 RAG 管理模块 (RAG Management)

- **功能**：从知识库构建到智能检索的完整解决方案，支持文档上传、OCR 识别、向量化、混合检索
- **核心能力**：
  - **知识库构建**：
    - 数据集管理：多个独立 RAG 数据集、版本管理、统计信息
    - 文档上传与处理：PDF/Word/TXT/Markdown、OCR 识别、文本提取、分段处理
    - 文档单元管理：手动编辑内容、重新向量化、OCR/向量化状态记录
  - **向量检索**：
    - 向量化存储：多种 Embedding 模型、自动批量向量化、向量数据库存储
    - 向量相似度检索：余弦相似度、阈值过滤、多数据集联合检索
  - **混合检索**：
    - 三种检索类型：VECTOR（向量）、KEYWORD（关键词）、HYBRID（混合）
    - RRF 融合算法：Reciprocal Rank Fusion、去重、参数调优
    - 重排序（Rerank）：二次优化排序、提高精确度
    - HyDE 技术：Hypothetical Document Embeddings、提升复杂查询理解
  - **文档处理状态机**：
    UPLOADED → OCR\_PROCESSING → OCR\_COMPLETED → EMBEDDING\_PROCESSING → COMPLETED
  - **版本与发布**：
    - 语义化版本管理、版本快照、审核机制
    - RAG 市场：浏览、安装市场中的 RAG 版本
  - **RAG 搜索与对话**：
    - 灵活检索参数配置（最大结果数、相似度阈值、重排序开关）
    - 流式检索对话：实时进度反馈、持续检索和响应
    - 检索结果展示：相似度分数、来源信息、原文预览
- **性能要求**：
  - 检索响应 < 1 秒（1000 个文档单元以内）
  - 支持单数据集至少 10 万个文档单元
  - 支持并发检索 ≥ 100 QPS

### 2.7 记忆管理模块 (Memory Management)

- **功能**：长期记忆存储、检索、去重和重要性加权，提升多轮对话连贯性和个性化体验
- **核心能力**：
  - **长期记忆存储**：
    - 自动提取：从对话中智能识别并提取有价值的记忆点
    - 类型分类：PROFILE（偏好）、TASK（目标）、FACT（事实）、EPISODIC（情景）
    - 重要性评分：0.0-1.0 分数，用于写入阈值和读取加权
    - 标签体系：支持记忆标签添加和管理
  - **记忆检索**：
    - 向量相似度检索：使用用户专属嵌入模型进行语义匹配
    - 重要性加权：综合计算相似度和重要性分值
    - 多租户隔离：严格按用户级别隔离记忆数据
    - Top-K 定制：灵活调整召回条目数量
  - **去重/合并**：
    - 语义去重：SHA-256 哈希值生成
    - 智能合并策略：重要性取最大值、标签合并、文本选用更丰富版本
  - **记忆管理**：分页查询、手动创建、归档删除、类型过滤
- **记忆类型详解**：
  - **PROFILE**：用户稳定的偏好（如"用简体中文回答"）
  - **TASK**：中长期目标或持续性计划（如"一周内完成 Agent 项目"）
  - **FACT**：稳定不变的事实（如"主要编程语言是 Python"）
  - **EPISODIC**：短期有帮助的情节信息（如"刚才讨论了 Kafka 配置"）
- **不抽取场景**：一次性操作、临时数据、隐私敏感信息
- **性能指标**：
  - 抽取响应 < 5 秒（异步处理）
  - 相似度检索 < 500ms（Top 16）
  - 单用户建议 < 1000 条记忆

### 2.8 容器管理模块 (Container Management)

- **功能**：基于 Docker 的容器化运行环境，支持用户隔离的 MCP 网关容器和工具审核容器
- **核心能力**：
  - **容器创建与生命周期管理**：
    - 用户容器创建：每个用户独立的 MCP 网关容器、按需创建、端口分配（30000-40000）
    - 审核容器创建：全系统共享的审核容器、动态管理、管理员专用
    - 生命周期状态：CREATING、RUNNING、STOPPED、ERROR、DELETING、DELETED、SUSPENDED
  - **容器监控与健康检查**：
    - 实时状态监控：容器状态、Docker 状态、网络连通性、资源使用（CPU/内存）
    - 智能健康检查：数据库状态检查、Docker 容器检查、网络连通性检查
    - 监控策略：状态检查（每 5 分钟）、资源监控（每 2 分钟）、请求时快速验证
  - **容器智能恢复**：
    - Docker 容器重启：强制启动已存在的容器
    - 容器信息修正：重新获取网络信息并更新数据库
    - 完全重建容器：标记旧容器删除，基于模板创建新容器
  - **容器自动清理**：
    - 暂停策略：24 小时未访问 → 停止容器 → SUSPENDED 状态
    - 删除策略：5 天未访问 → 删除 Docker 容器 → DELETED 状态
    - 定时任务：每小时执行一次清理
  - **容器类型策略**：
    - 用户容器（USER）：每个用户一个、长期保留、支撑 Agent 对话和工具部署
    - 审核容器（REVIEW）：全系统一个、按需创建、仅管理员访问
  - **端口与网络管理**：
    - 端口范围：30000-40000、动态分配、冲突检测
    - 网络模式：bridge、容器隔离、端口映射、DNS 解析
  - **容器模板管理**：
    - MCP 网关模板：`ghcr.io/lucky-aeon/mcp-gateway:latest`
    - 配置：内部端口 8080、CPU 1.0 核、内存 512MB
- **性能特性**：
  - 按需资源：仅在需要时创建容器
  - 弹性伸缩：根据访问量和使用时间动态调整
  - 快速恢复：容器异常时快速恢复，最小化业务影响

### 2.9 MCP 支持模块 (MCP Support)

- **功能**：提供对 Model Context Protocol 协议的支持，包括 MCP 服务器 URL 管理、工具参数预设、容器化工具服务
- **核心能力**：
  - **MCP 协议支持**：协议适配、工具发现、工具调用、事件处理
  - **MCP 服务器 URL 管理**：URL 获取、智能判断（全局/用户/直接连接）、URL 构建与验证
  - **工具类型判断**：根据工具名称和 isGlobal 标记判断类型（全局工具/用户工具）
  - **容器集成**：
    - 容器自动创建：工具需要时自动创建并启动容器
    - 容器状态检查：检查容器运行状态
    - 容器 URL 构建：基于容器信息构建 SSE 连接 URL
    - 容器自动清理：不再使用时自动清理
  - **工具参数预设**：参数定义、参数模板、参数验证、参数序列化（JSON Schema 格式）
  - **SSE 连接管理**：SSE URL 构建、连接建立、事件接收、连接维护
- **容器类型**：审核容器（全局工具）、用户容器（用户工具）、临时容器
- **事件类型**：工具列表事件、工具调用事件、结果返回事件、错误和状态事件
- **性能要求**：
  - MCP 工具 URL 获取 < 100ms
  - SSE 连接建立 < 1s
  - 容器启动 < 30s
  - 工具调用 < 5s（不包括容器启动）

### 2.10 高可用模块 (High Availability)

- **功能**：LLM 模型的故障切换、健康检查和负载均衡，确保服务持续可用性
- **核心能力**：
  - **LLM 模型故障切换**：
    - 支持配置多个备用模型
    - 自动检测故障（超时、错误率过高）
    - 故障切换透明化，对上层无感知
    - 支持故障模型自动恢复
  - **健康检查**：
    - 主动健康检查（主动探测）
    - 被动健康检查（基于调用结果）
    - 检查内容：响应时间、错误率、可用性、Quota 余额
    - 可配置策略（间隔、阈值）
  - **负载均衡**：
    - 多种策略：轮询、随机、最少连接、响应时间、加权轮询
    - 支持实例权重配置和动态调整
    - 剔除不健康实例
  - **高可用网关集成**：
    - 模型实例注册和发现
    - 最佳实例选择
    - 调用结果上报和统计分析
    - 实例激活和停用
  - **模型同步管理**：
    - 创建/更新/删除模型时同步到网关
    - 支持批量同步和删除
    - 异步同步，避免阻塞主流程
  - **会话亲和性**：
    - 基于 SessionId 绑定实例
    - 会话期间使用同一实例
    - 实例不可用时降级
  - **降级策略**：
    - 网关不可用时降级到本地逻辑
    - 使用默认模型和 Provider
    - 记录降级日志和告警
  - **调用结果监控**：
    - 成功率、响应时间、错误分布、调用量统计
    - 实时上报、批量上报、定期上报
- **性能要求**：
  - 模型选择延迟 < 50ms
  - 故障切换时间 < 1s
  - 健康检查间隔可配置（默认 30s）
  - 系统可用性 ≥ 99.9%

### 2.11 计费管理模块 (Account Billing)

- **功能**：账户余额管理、充值消费、订单管理、支付流程，为平台各项服务提供统一计费基础
- **核心能力**：
  - **账户余额管理**：
    - 用户账户创建：注册时自动创建
    - 账户余额查询：余额、信用额度、总消费金额
    - 可用余额计算：余额 + 信用额度
    - 余额充足性检查：消费前检查
  - **充值功能**：
    - 多支付平台：支付宝、微信支付、Stripe
    - 多支付方式：网页支付、二维码支付、移动端支付、H5 支付、小程序支付
    - 支付成功自动到账
    - 支付状态查询
  - **消费计费**：
    - 自动扣费：使用服务后自动扣费
    - 多种计费策略：按 Token、按次、按时长、存储费等
    - 最低计费保障：小额归整为 0.01 元
    - 消费记录：详细计费信息
  - **订单管理**：
    - 订单类型：充值订单、购买订单、订阅订单、续费订单
    - 订单状态：待支付、已支付、已取消、已退款、已过期
    - 订单查询和筛选
  - **支付流程**：
    - 支付发起：调用第三方支付平台 API
    - 支付回调：接收回调通知
    - 状态同步：同步支付状态
    - 事件触发：支付成功后触发业务处理
- **计费类型**：
  - **MODEL\_USAGE**：按输入输出 Token 计费
  - **AGENT\_CREATION**：按创建次数计费
  - **AGENT\_USAGE**：按使用次数或资源消耗计费
  - **API\_CALL**：按 API 调用次数计费
  - **STORAGE\_USAGE**：按存储容量和时长计费
- **事件驱动**：
  - PurchaseSuccessEvent：支付成功事件
  - 异步事件机制提升解耦和可扩展性
- **幂等保障**：基于请求 ID 防止重复计费

### 2.12 Agent 工作流模块 (Agent Workflow)

- **功能**：复杂任务的自动化编排，支持任务拆分、并行执行、工具调用、摘要生成
- **核心能力**：
  - **复杂任务编排**：
    - 任务识别：分析用户请求是否需要复杂处理
    - 任务拆分：分解为可执行的子任务
    - 任务依赖管理：处理任务间依赖关系
    - 并行执行：无依赖任务并行执行
  - **任务执行**：
    - 任务调度：调度子任务到执行队列
    - 任务监控：监控执行状态和进度
    - 错误处理：失败重试机制
    - 结果收集：收集子任务执行结果
  - **摘要生成**：
    - 自动摘要：根据配置生成对话摘要
    - 摘要触发：Token 超阈值、任务链完成、对话轮次达标
    - 摘要存储和恢复
    - 摘要策略：基于重要性、时间窗口、任务边界
  - **工具调用管理**：
    - 工具注册：内置工具和用户工具
    - 工具选择：根据任务需求选择
    - 工具调用和执行结果处理
  - **工作流状态管理**：
    - 状态机：INIT、ANALYZING、SPLITTING、EXECUTING、SUMMARIZING、COMPLETED、FAILED
    - 状态转换触发条件
    - 状态持久化
    - 工作流暂停和恢复
  - **事件总线**：
    - 事件类型：任务创建、完成、失败、工具调用、摘要生成
    - 异步事件处理
    - 事件订阅和取消
- **性能要求**：
  - 任务拆分 < 1s
  - 单个任务执行 < 10s
  - 工作流完成 < 30s
  - 支持同时执行 100+ 工作流

### 2.13 定时任务模块 (Scheduled Task)

- **功能**：管理 Agent 的定时任务，包括任务调度、执行器、任务模型
- **核心组件**：
  - 任务调度器：根据 cron 表达式调度任务
  - 任务执行器：执行具体的 Agent 任务
  - 任务模型：定义任务属性、配置、触发器
- **数据流**：
  1. 用户配置 Agent 定时任务
  2. 任务调度器根据 cron 表达式调度
  3. 任务执行器执行 Agent 任务
  4. 记录任务执行结果和日志

## 3. 技术栈选择

### 3.1 后端技术栈

| 技术           | 版本     | 用途               |
| ------------ | ------ | ---------------- |
| Java         | 17+    | 主要开发语言           |
| Spring Boot  | 3.x    | 应用框架             |
| FastAPI      | 0.104+ | Python 服务 API 框架 |
| PostgreSQL   | 14+    | 关系型数据库           |
| PGVector     | 0.5+   | 向量数据库插件          |
| RabbitMQ     | 3.10+  | 消息队列             |
| Redis        | 7.0+   | 缓存、会话存储          |
| Docker       | 24+    | 容器化运行时           |
| MyBatis-Plus | 3.5+   | ORM 框架           |
| LangChain4j  | 0.24+  | LLM 集成框架         |
| JWT          | -      | 身份认证             |
| MapStruct    | 1.5+   | DTO 映射           |
| Lombok       | 1.18+  | 代码简化             |

### 3.2 前端技术栈

| 技术            | 版本   | 用途       |
| ------------- | ---- | -------- |
| React         | 18+  | 前端框架     |
| TypeScript    | 5.0+ | 类型系统     |
| Ant Design    | 5.0+ | UI 组件库   |
| Axios         | 1.6+ | HTTP 客户端 |
| Redux/Zustand | 4.2+ | 状态管理     |
| React Router  | 6+   | 路由管理     |

### 3.3 基础设施

| 组件     | 技术                          | 用途           |
| ------ | --------------------------- | ------------ |
| 容器编排   | Docker Compose / Kubernetes | 容器部署和管理      |
| 服务发现   | Consul / Nacos              | 服务注册与发现      |
| API 网关 | Kong / APISIX               | API 路由、限流、认证 |
| 监控告警   | Prometheus + Grafana        | 系统监控和告警      |
| 日志系统   | ELK Stack                   | 日志收集和分析      |
| 链路追踪   | SkyWalking / Zipkin         | 分布式链路追踪      |
| 配置中心   | Apollo / Nacos              | 集中化配置管理      |

## 4. 数据库设计

### 4.1 核心表结构

#### 4.1.1 users 用户表

| 字段名             | 数据类型         | 约束              | 描述                   |
| --------------- | ------------ | --------------- | -------------------- |
| id              | UUID         | PRIMARY KEY     | 用户唯一标识               |
| nickname        | VARCHAR(100) | NOT NULL        | 用户昵称                 |
| email           | VARCHAR(255) | UNIQUE NOT NULL | 邮箱                   |
| phone           | VARCHAR(20)  | <br />          | 手机号                  |
| password        | VARCHAR(255) | NOT NULL        | BCrypt 加密密码          |
| avatar\_url     | VARCHAR(500) | <br />          | 头像 URL               |
| github\_id      | VARCHAR(100) | UNIQUE          | GitHub 用户 ID         |
| github\_login   | VARCHAR(100) | <br />          | GitHub 登录名           |
| login\_platform | VARCHAR(20)  | NOT NULL        | 登录平台 (normal/github) |
| is\_admin       | BOOLEAN      | DEFAULT FALSE   | 是否管理员                |
| created\_at     | TIMESTAMP    | DEFAULT NOW()   | 创建时间                 |
| updated\_at     | TIMESTAMP    | DEFAULT NOW()   | 更新时间                 |

#### 4.1.2 user\_settings 用户设置表

| 字段名                       | 数据类型         | 约束                   | 描述           |
| ------------------------- | ------------ | -------------------- | ------------ |
| id                        | UUID         | PRIMARY KEY          | 设置 ID        |
| user\_id                  | UUID         | REFERENCES users(id) | 用户 ID        |
| default\_model            | VARCHAR(100) | <br />               | 默认聊天模型 ID    |
| default\_ocr\_model       | VARCHAR(100) | <br />               | 默认 OCR 模型 ID |
| default\_embedding\_model | VARCHAR(100) | <br />               | 默认嵌入模型 ID    |
| fallback\_config          | JSONB        | <br />               | 降级链配置        |
| created\_at               | TIMESTAMP    | DEFAULT NOW()        | 创建时间         |
| updated\_at               | TIMESTAMP    | DEFAULT NOW()        | 更新时间         |

#### 4.1.3 llm\_providers LLM 服务商表

| 字段名          | 数据类型         | 约束                   | 描述                           |
| ------------ | ------------ | -------------------- | ---------------------------- |
| id           | UUID         | PRIMARY KEY          | 服务商 ID                       |
| name         | VARCHAR(100) | NOT NULL             | 服务商名称                        |
| protocol     | VARCHAR(50)  | NOT NULL             | 协议类型 (openai/moonshot/azure) |
| api\_key     | TEXT         | NOT NULL             | API Key（加密存储）                |
| base\_url    | VARCHAR(255) | <br />               | 自定义 Base URL                 |
| is\_official | BOOLEAN      | DEFAULT FALSE        | 是否官方服务商                      |
| user\_id     | UUID         | REFERENCES users(id) | 创建者 ID（用户级资源）                |
| status       | VARCHAR(20)  | DEFAULT 'ACTIVE'     | 状态 (ACTIVE/INACTIVE)         |
| created\_at  | TIMESTAMP    | DEFAULT NOW()        | 创建时间                         |
| updated\_at  | TIMESTAMP    | DEFAULT NOW()        | 更新时间                         |

#### 4.1.4 llm\_models LLM 模型表

| 字段名             | 数据类型         | 约束                            | 描述                    |
| --------------- | ------------ | ----------------------------- | --------------------- |
| id              | UUID         | PRIMARY KEY                   | 模型 ID                 |
| provider\_id    | UUID         | REFERENCES llm\_providers(id) | 所属服务商 ID              |
| name            | VARCHAR(100) | NOT NULL                      | 模型名称                  |
| model\_endpoint | VARCHAR(100) | NOT NULL                      | 模型部署名称                |
| type            | VARCHAR(20)  | NOT NULL                      | 模型类型 (CHAT/EMBEDDING) |
| is\_official    | BOOLEAN      | DEFAULT FALSE                 | 是否官方模型                |
| status          | VARCHAR(20)  | DEFAULT 'ACTIVE'              | 状态 (ACTIVE/INACTIVE)  |
| created\_at     | TIMESTAMP    | DEFAULT NOW()                 | 创建时间                  |
| updated\_at     | TIMESTAMP    | DEFAULT NOW()                 | 更新时间                  |

#### 4.1.5 agents 智能体表

| 字段名                  | 数据类型         | 约束                   | 描述                    |
| -------------------- | ------------ | -------------------- | --------------------- |
| id                   | UUID         | PRIMARY KEY          | Agent ID              |
| user\_id             | UUID         | REFERENCES users(id) | 创建者 ID                |
| name                 | VARCHAR(100) | NOT NULL             | Agent 名称              |
| avatar\_url          | VARCHAR(500) | <br />               | 头像 URL                |
| description          | TEXT         | <br />               | 描述                    |
| system\_prompt       | TEXT         | <br />               | 系统提示词                 |
| welcome\_message     | TEXT         | <br />               | 欢迎消息                  |
| tool\_ids            | UUID\[]      | <br />               | 关联的工具 ID 列表           |
| knowledge\_base\_ids | UUID\[]      | <br />               | 关联的知识库 ID 列表          |
| tool\_presets        | JSONB        | <br />               | 工具预设参数                |
| multimodal\_config   | JSONB        | <br />               | 多模态配置                 |
| status               | VARCHAR(20)  | DEFAULT 'ENABLED'    | 状态 (ENABLED/DISABLED) |
| created\_at          | TIMESTAMP    | DEFAULT NOW()        | 创建时间                  |
| updated\_at          | TIMESTAMP    | DEFAULT NOW()        | 更新时间                  |

#### 4.1.6 agent\_versions 智能体版本表

| 字段名             | 数据类型        | 约束                    | 描述          |
| --------------- | ----------- | --------------------- | ----------- |
| id              | UUID        | PRIMARY KEY           | 版本 ID       |
| agent\_id       | UUID        | REFERENCES agents(id) | Agent ID    |
| version         | VARCHAR(20) | NOT NULL              | 版本号 (x.y.z) |
| change\_log     | TEXT        | <br />                | 变更日志        |
| snapshot        | JSONB       | NOT NULL              | 版本快照（完整配置）  |
| publish\_status | VARCHAR(20) | DEFAULT 'REVIEWING'   | 发布状态        |
| published\_at   | TIMESTAMP   | <br />                | 发布时间        |
| created\_at     | TIMESTAMP   | DEFAULT NOW()         | 创建时间        |

#### 4.1.7 agent\_widgets 智能体 Widget 表

| 字段名                  | 数据类型         | 约束                    | 描述                |
| -------------------- | ------------ | --------------------- | ----------------- |
| id                   | UUID         | PRIMARY KEY           | Widget ID         |
| agent\_id            | UUID         | REFERENCES agents(id) | Agent ID          |
| public\_id           | VARCHAR(100) | UNIQUE NOT NULL       | 公开 ID（嵌入使用）       |
| name                 | VARCHAR(100) | NOT NULL              | Widget 名称         |
| type                 | VARCHAR(20)  | NOT NULL              | 类型 (AGENT/RAG)    |
| model\_id            | UUID         | <br />                | 使用的模型 ID          |
| allowed\_domains     | TEXT\[]      | <br />                | 域名白名单             |
| daily\_limit         | INTEGER      | DEFAULT -1            | 每日调用限制 (-1 无限制)   |
| knowledge\_base\_ids | UUID\[]      | <br />                | 知识库 ID 列表（RAG 类型） |
| enabled              | BOOLEAN      | DEFAULT TRUE          | 启用状态              |
| created\_at          | TIMESTAMP    | DEFAULT NOW()         | 创建时间              |

#### 4.1.8 workspace\_agents 工作区 Agent 表

| 字段名                | 数据类型        | 约束                    | 描述         |
| ------------------ | ----------- | --------------------- | ---------- |
| id                 | UUID        | PRIMARY KEY           | ID         |
| user\_id           | UUID        | REFERENCES users(id)  | 用户 ID      |
| agent\_id          | UUID        | REFERENCES agents(id) | Agent ID   |
| model\_id          | UUID        | <br />                | 自定义模型 ID   |
| temperature        | DOUBLE      | DEFAULT 0.7           | 温度参数       |
| top\_p             | DOUBLE      | DEFAULT 0.7           | Top P 参数   |
| top\_k             | INTEGER     | DEFAULT 50            | Top K 参数   |
| max\_tokens        | INTEGER     | <br />                | 最大 Token 数 |
| strategy\_type     | VARCHAR(20) | DEFAULT 'NONE'        | Token 溢出策略 |
| reserve\_ratio     | DOUBLE      | <br />                | 预留缓冲比例     |
| summary\_threshold | INTEGER     | <br />                | 摘要触发阈值     |
| created\_at        | TIMESTAMP   | DEFAULT NOW()         | 创建时间       |
| updated\_at        | TIMESTAMP   | DEFAULT NOW()         | 更新时间       |

#### 4.1.9 tools 工具表

| 字段名                 | 数据类型         | 约束                        | 描述            |
| ------------------- | ------------ | ------------------------- | ------------- |
| id                  | UUID         | PRIMARY KEY               | 工具 ID         |
| user\_id            | UUID         | REFERENCES users(id)      | 创建者 ID        |
| name                | VARCHAR(100) | NOT NULL                  | 工具名称          |
| description         | TEXT         | <br />                    | 描述            |
| github\_repo\_url   | VARCHAR(500) | NOT NULL                  | GitHub 仓库 URL |
| install\_command    | TEXT         | <br />                    | 安装命令          |
| mcp\_server\_config | JSONB        | <br />                    | MCP 服务器配置     |
| status              | VARCHAR(20)  | DEFAULT 'WAITING\_REVIEW' | 状态机状态         |
| is\_global          | BOOLEAN      | DEFAULT FALSE             | 是否全局工具        |
| tools\_definition   | JSONB        | <br />                    | 工具定义列表        |
| created\_at         | TIMESTAMP    | DEFAULT NOW()             | 创建时间          |
| updated\_at         | TIMESTAMP    | DEFAULT NOW()             | 更新时间          |

#### 4.1.10 tool\_versions 工具版本表

| 字段名           | 数据类型        | 约束                   | 描述    |
| ------------- | ----------- | -------------------- | ----- |
| id            | UUID        | PRIMARY KEY          | 版本 ID |
| tool\_id      | UUID        | REFERENCES tools(id) | 工具 ID |
| version       | VARCHAR(20) | NOT NULL             | 版本号   |
| change\_log   | TEXT        | <br />               | 更新日志  |
| is\_published | BOOLEAN     | DEFAULT FALSE        | 是否已发布 |
| created\_at   | TIMESTAMP   | DEFAULT NOW()        | 创建时间  |

#### 4.1.11 user\_tools 用户工具安装表

| 字段名               | 数据类型         | 约束                            | 描述        |
| ----------------- | ------------ | ----------------------------- | --------- |
| id                | UUID         | PRIMARY KEY                   | ID        |
| user\_id          | UUID         | REFERENCES users(id)          | 用户 ID     |
| tool\_id          | UUID         | REFERENCES tools(id)          | 工具 ID     |
| version\_id       | UUID         | REFERENCES tool\_versions(id) | 版本 ID     |
| mcp\_server\_name | VARCHAR(100) | <br />                        | MCP 服务器名称 |
| installed\_at     | TIMESTAMP    | DEFAULT NOW()                 | 安装时间      |

#### 4.1.12 rag\_datasets RAG 数据集表

| 字段名                  | 数据类型         | 约束                   | 描述              |
| -------------------- | ------------ | -------------------- | --------------- |
| id                   | UUID         | PRIMARY KEY          | 数据集 ID          |
| user\_id             | UUID         | REFERENCES users(id) | 创建者 ID          |
| name                 | VARCHAR(100) | NOT NULL             | 数据集名称           |
| description          | TEXT         | <br />               | 描述              |
| embedding\_model\_id | UUID         | <br />               | Embedding 模型 ID |
| document\_count      | INTEGER      | DEFAULT 0            | 文档数量            |
| unit\_count          | INTEGER      | DEFAULT 0            | 文档单元数量          |
| status               | VARCHAR(20)  | DEFAULT 'ACTIVE'     | 状态              |
| created\_at          | TIMESTAMP    | DEFAULT NOW()        | 创建时间            |
| updated\_at          | TIMESTAMP    | DEFAULT NOW()        | 更新时间            |

#### 4.1.13 rag\_documents RAG 文档表

| 字段名               | 数据类型         | 约束                           | 描述                     |
| ----------------- | ------------ | ---------------------------- | ---------------------- |
| id                | UUID         | PRIMARY KEY                  | 文档 ID                  |
| dataset\_id       | UUID         | REFERENCES rag\_datasets(id) | 数据集 ID                 |
| file\_name        | VARCHAR(255) | NOT NULL                     | 文件名                    |
| file\_url         | VARCHAR(500) | NOT NULL                     | 文件存储 URL               |
| file\_type        | VARCHAR(20)  | NOT NULL                     | 文件类型 (PDF/DOCX/TXT/MD) |
| ocr\_status       | VARCHAR(20)  | DEFAULT 'UPLOADED'           | OCR 状态                 |
| embedding\_status | VARCHAR(20)  | DEFAULT 'PENDING'            | 向量化状态                  |
| word\_count       | INTEGER      | <br />                       | 字数统计                   |
| created\_at       | TIMESTAMP    | DEFAULT NOW()                | 创建时间                   |
| updated\_at       | TIMESTAMP    | DEFAULT NOW()                | 更新时间                   |

#### 4.1.14 rag\_document\_units RAG 文档单元表

| 字段名               | 数据类型         | 约束                            | 描述      |
| ----------------- | ------------ | ----------------------------- | ------- |
| id                | UUID         | PRIMARY KEY                   | 文档单元 ID |
| document\_id      | UUID         | REFERENCES rag\_documents(id) | 文档 ID   |
| content           | TEXT         | NOT NULL                      | 文本内容    |
| page\_number      | INTEGER      | <br />                        | 页码（PDF） |
| embedding\_vector | VECTOR(1536) | <br />                        | 向量数据    |
| created\_at       | TIMESTAMP    | DEFAULT NOW()                 | 创建时间    |

#### 4.1.15 memory\_items 记忆条目表

| 字段名                 | 数据类型        | 约束                   | 描述                                |
| ------------------- | ----------- | -------------------- | --------------------------------- |
| id                  | UUID        | PRIMARY KEY          | 记忆 ID                             |
| user\_id            | UUID        | REFERENCES users(id) | 用户 ID                             |
| type                | VARCHAR(20) | NOT NULL             | 记忆类型 (PROFILE/TASK/FACT/EPISODIC) |
| text                | TEXT        | NOT NULL             | 记忆文本内容                            |
| data                | JSONB       | <br />               | 结构化数据                             |
| importance          | DOUBLE      | DEFAULT 0.0          | 重要性评分 (0.0-1.0)                   |
| tags                | TEXT\[]     | <br />               | 标签列表                              |
| source\_session\_id | UUID        | <br />               | 来源会话 ID                           |
| dedupe\_hash        | VARCHAR(64) | <br />               | 去重 SHA-256 哈希值                    |
| status              | INTEGER     | DEFAULT 1            | 状态 (1=active, 0=archived)         |
| created\_at         | TIMESTAMP   | DEFAULT NOW()        | 创建时间                              |
| updated\_at         | TIMESTAMP   | DEFAULT NOW()        | 更新时间                              |

#### 4.1.16 containers 容器表

| 字段名                   | 数据类型         | 约束                 | 描述               |
| --------------------- | ------------ | ------------------ | ---------------- |
| id                    | UUID         | PRIMARY KEY        | 容器 ID            |
| user\_id              | UUID         | <br />             | 用户 ID（用户容器）      |
| type                  | VARCHAR(20)  | NOT NULL           | 类型 (USER/REVIEW) |
| docker\_container\_id | VARCHAR(100) | <br />             | Docker 容器 ID     |
| ip\_address           | VARCHAR(50)  | <br />             | 容器 IP 地址         |
| external\_port        | INTEGER      | <br />             | 外部端口             |
| internal\_port        | INTEGER      | DEFAULT 8080       | 内部端口             |
| status                | VARCHAR(20)  | DEFAULT 'CREATING' | 状态               |
| last\_accessed\_at    | TIMESTAMP    | <br />             | 最后访问时间           |
| config                | JSONB        | <br />             | 容器配置             |
| created\_at           | TIMESTAMP    | DEFAULT NOW()      | 创建时间             |
| updated\_at           | TIMESTAMP    | DEFAULT NOW()      | 更新时间             |

#### 4.1.17 accounts 账户表

| 字段名                   | 数据类型          | 约束                          | 描述     |
| --------------------- | ------------- | --------------------------- | ------ |
| id                    | UUID          | PRIMARY KEY                 | 账户 ID  |
| user\_id              | UUID          | REFERENCES users(id) UNIQUE | 用户 ID  |
| balance               | DECIMAL(10,4) | DEFAULT 0.00                | 账户余额   |
| credit                | DECIMAL(10,4) | DEFAULT 0.00                | 信用额度   |
| total\_consumed       | DECIMAL(10,4) | DEFAULT 0.00                | 总消费金额  |
| last\_transaction\_at | TIMESTAMP     | <br />                      | 最后交易时间 |
| created\_at           | TIMESTAMP     | DEFAULT NOW()               | 创建时间   |
| updated\_at           | TIMESTAMP     | DEFAULT NOW()               | 更新时间   |

#### 4.1.18 orders 订单表

| 字段名               | 数据类型          | 约束                   | 描述                                            |
| ----------------- | ------------- | -------------------- | --------------------------------------------- |
| id                | UUID          | PRIMARY KEY          | 订单 ID                                         |
| order\_no         | VARCHAR(100)  | UNIQUE NOT NULL      | 订单号                                           |
| user\_id          | UUID          | REFERENCES users(id) | 用户 ID                                         |
| type              | VARCHAR(20)   | NOT NULL             | 订单类型 (RECHARGE/PURCHASE/SUBSCRIPTION/RENEWAL) |
| amount            | DECIMAL(10,4) | NOT NULL             | 金额                                            |
| status            | VARCHAR(20)   | DEFAULT 'PENDING'    | 状态                                            |
| payment\_platform | VARCHAR(20)   | <br />               | 支付平台 (ALIPAY/WECHAT/STRIPE)                   |
| payment\_type     | VARCHAR(20)   | <br />               | 支付类型 (WEB/QR\_CODE/MOBILE/H5/MINI\_PROGRAM)   |
| paid\_at          | TIMESTAMP     | <br />               | 支付时间                                          |
| created\_at       | TIMESTAMP     | DEFAULT NOW()        | 创建时间                                          |
| updated\_at       | TIMESTAMP     | DEFAULT NOW()        | 更新时间                                          |

#### 4.1.19 sessions 会话表

| 字段名                   | 数据类型         | 约束                    | 描述          |
| --------------------- | ------------ | --------------------- | ----------- |
| id                    | UUID         | PRIMARY KEY           | 会话 ID       |
| user\_id              | UUID         | REFERENCES users(id)  | 用户 ID       |
| agent\_id             | UUID         | REFERENCES agents(id) | Agent ID    |
| title                 | VARCHAR(255) | <br />                | 会话标题        |
| context\_token\_count | INTEGER      | DEFAULT 0             | 上下文 Token 数 |
| summary               | TEXT         | <br />                | 会话摘要        |
| status                | VARCHAR(20)  | DEFAULT 'ACTIVE'      | 状态          |
| created\_at           | TIMESTAMP    | DEFAULT NOW()         | 创建时间        |
| updated\_at           | TIMESTAMP    | DEFAULT NOW()         | 更新时间        |

#### 4.1.20 messages 消息表

| 字段名            | 数据类型         | 约束                      | 描述                         |
| -------------- | ------------ | ----------------------- | -------------------------- |
| id             | UUID         | PRIMARY KEY             | 消息 ID                      |
| session\_id    | UUID         | REFERENCES sessions(id) | 会话 ID                      |
| role           | VARCHAR(20)  | NOT NULL                | 角色 (USER/SYSTEM/ASSISTANT) |
| type           | VARCHAR(20)  | DEFAULT 'TEXT'          | 消息类型                       |
| content        | TEXT         | <br />                  | 消息内容                       |
| token\_count   | INTEGER      | <br />                  | Token 数量                   |
| provider\_name | VARCHAR(100) | <br />                  | 服务提供商                      |
| model\_name    | VARCHAR(100) | <br />                  | 模型名称                       |
| files          | JSONB        | <br />                  | 关联文件 URL 列表                |
| metadata       | JSONB        | <br />                  | 自定义元数据                     |
| created\_at    | TIMESTAMP    | DEFAULT NOW()           | 创建时间                       |

#### 4.1.21 scheduled\_tasks 定时任务表

| 字段名                 | 数据类型         | 约束                    | 描述       |
| ------------------- | ------------ | --------------------- | -------- |
| id                  | UUID         | PRIMARY KEY           | 任务 ID    |
| agent\_id           | UUID         | REFERENCES agents(id) | Agent ID |
| name                | VARCHAR(100) | NOT NULL              | 任务名称     |
| cron\_expression    | VARCHAR(100) | NOT NULL              | Cron 表达式 |
| config              | JSONB        | <br />                | 任务配置     |
| status              | VARCHAR(20)  | DEFAULT 'ACTIVE'      | 状态       |
| last\_execution\_at | TIMESTAMP    | <br />                | 最后执行时间   |
| next\_execution\_at | TIMESTAMP    | <br />                | 下次执行时间   |
| created\_at         | TIMESTAMP    | DEFAULT NOW()         | 创建时间     |
| updated\_at         | TIMESTAMP    | DEFAULT NOW()         | 更新时间     |

## 5. API 设计

### 5.1 认证与用户 API

#### 认证 API

| 端点                        | 方法   | 功能               | 请求体                                                        | 响应                           |
| ------------------------- | ---- | ---------------- | ---------------------------------------------------------- | ---------------------------- |
| /api/auth/login           | POST | 用户登录             | `{"account": "...", "password": "..."}`                    | `{access_token, token_type}` |
| /api/auth/register        | POST | 用户注册             | `{"email": "...", "password": "..."}`                      | `{user_id, email}`           |
| /api/auth/github          | GET  | 获取 GitHub 登录 URL | -                                                          | `{authorize_url}`            |
| /api/auth/github/callback | GET  | GitHub 回调        | `code`                                                     | `{access_token}`             |
| /api/auth/password/reset  | POST | 密码重置             | `{"email": "...", "captcha": "...", "newPassword": "..."}` | -                            |
| /api/auth/me              | GET  | 获取当前用户           | -                                                          | `UserDTO`                    |

#### 用户管理 API

| 端点                      | 方法  | 功能     | 说明         |
| ----------------------- | --- | ------ | ---------- |
| GET /api/users/profile  | GET | 获取用户资料 | 返回完整用户信息   |
| PUT /api/users/profile  | PUT | 更新用户资料 | 更新昵称、头像等   |
| PUT /api/users/password | PUT | 修改密码   | 需要验证当前密码   |
| GET /api/users/settings | GET | 获取用户设置 | 默认模型、降级配置等 |
| PUT /api/users/settings | PUT | 更新用户设置 | 更新个性化配置    |

### 5.2 LLM 管理 API

| 端点                             | 方法     | 功能      | 说明                     |
| ------------------------------ | ------ | ------- | ---------------------- |
| GET /api/llm/providers         | GET    | 获取服务商列表 | 支持按类型筛选（官方/自定义）        |
| POST /api/llm/providers        | POST   | 创建服务商   | 需要验证协议类型               |
| GET /api/llm/providers/{id}    | GET    | 获取服务商详情 | 包含模型列表和 API Key 掩码     |
| PUT /api/llm/providers/{id}    | PUT    | 更新服务商   | 更新配置信息                 |
| DELETE /api/llm/providers/{id} | DELETE | 删除服务商   | 级联删除下属模型               |
| GET /api/llm/models            | GET    | 获取模型列表  | 按服务商类型和模型类型筛选          |
| POST /api/llm/models           | POST   | 创建模型    | 指定所属服务商                |
| PUT /api/llm/models/{id}       | PUT    | 更新模型    | 更新模型配置                 |
| DELETE /api/llm/models/{id}    | DELETE | 删除模型    | 支持批量删除                 |
| GET /api/llm/protocols         | GET    | 获取支持的协议 | 返回 ProviderProtocol 列表 |

### 5.3 Agent 管理 API

| 端点                               | 方法     | 功能          | 说明               |
| -------------------------------- | ------ | ----------- | ---------------- |
| GET /api/agents                  | GET    | 获取 Agent 列表 | 支持名称、状态过滤        |
| POST /api/agents                 | POST   | 创建 Agent    | 自动创建默认 LLM 配置    |
| GET /api/agents/{id}             | GET    | 获取 Agent 详情 | 需权限验证            |
| PUT /api/agents/{id}             | PUT    | 更新 Agent    | 支持基本信息和配置更新      |
| DELETE /api/agents/{id}          | DELETE | 删除 Agent    | 级联删除版本、Widget 等  |
| POST /api/agents/{id}/publish    | POST   | 发布新版本       | 创建版本快照并提交审核      |
| GET /api/agents/{id}/versions    | GET    | 获取版本历史      | 查询所有版本或已发布版本     |
| GET /api/agents/market           | GET    | 获取已上架 Agent | 市场上公开的 Agent 列表  |
| POST /api/agents/widget          | POST   | 创建 Widget   | 为 Agent 创建嵌入配置   |
| GET /api/agents/workspace        | GET    | 获取工作区 Agent | 用户工作区中的 Agent 列表 |
| PUT /api/agents/workspace/{id}   | PUT    | 更新工作区配置     | 更新 LLM 模型参数      |
| POST /api/agents/prompt/generate | POST   | 生成系统提示词     | AI 辅助生成提示词       |

### 5.4 工具集成 API

| 端点                             | 方法     | 功能      | 说明             |
| ------------------------------ | ------ | ------- | -------------- |
| GET /api/tools/market          | GET    | 获取工具市场  | 已发布的工具列表       |
| POST /api/tools                | POST   | 上传工具    | 提交 GitHub 仓库信息 |
| PUT /api/tools/{id}            | PUT    | 更新工具    | 重新验证和部署        |
| DELETE /api/tools/{id}         | DELETE | 删除工具    | 仅创建者可删除        |
| POST /api/tools/{id}/install   | POST   | 安装工具    | 安装到用户空间        |
| POST /api/tools/{id}/uninstall | POST   | 卸载工具    | 从用户空间移除        |
| GET /api/tools/my              | GET    | 我的工具列表  | 已安装的工具列表       |
| GET /api/tools/review          | GET    | 待审核工具列表 | 管理员审核入口        |
| POST /api/tools/{id}/review    | POST   | 审核工具    | 通过/拒绝审核        |
| POST /api/tools/{id}/release   | POST   | 发布版本    | 发布到工具市场        |

### 5.5 RAG 管理 API

| 端点                                    | 方法     | 功能       | 说明                   |
| ------------------------------------- | ------ | -------- | -------------------- |
| GET /api/rag/datasets                 | GET    | 获取数据集列表  | 支持分页和筛选              |
| POST /api/rag/datasets                | POST   | 创建数据集    | 创建 RAG 数据集           |
| GET /api/rag/datasets/{id}            | GET    | 获取数据集详情  | 包含统计信息               |
| PUT /api/rag/datasets/{id}            | PUT    | 更新数据集    | 更新配置信息               |
| DELETE /api/rag/datasets/{id}         | DELETE | 删除数据集    | 级联删除文档               |
| POST /api/rag/datasets/{id}/files     | POST   | 上传文档     | 批量上传 PDF/Word/TXT/MD |
| GET /api/rag/datasets/{id}/documents  | GET    | 获取文档列表   | 文档列表及处理状态            |
| PUT /api/rag/documents/{id}           | PUT    | 编辑文档单元   | 手动编辑内容               |
| POST /api/rag/documents/{id}/re-embed | POST   | 重新向量化    | 重新生成向量               |
| POST /api/rag/search                  | POST   | 检索文档     | 支持向量/关键词/混合检索        |
| POST /api/rag/chat                    | POST   | RAG 流式对话 | 基于检索结果的对话            |
| POST /api/rag/datasets/{id}/versions  | POST   | 创建版本     | 创建数据集版本              |
| POST /api/rag/datasets/{id}/publish   | POST   | 发布版本     | 提交发布申请               |
| GET /api/rag/market                   | GET    | RAG 市场   | 已发布的 RAG 版本          |

### 5.6 对话管理 API

| 端点                                     | 方法     | 功能     | 说明          |
| -------------------------------------- | ------ | ------ | ----------- |
| GET /api/conversations                 | GET    | 获取会话列表 | 分页查询        |
| POST /api/conversations                | POST   | 创建会话   | 指定 Agent    |
| DELETE /api/conversations              | DELETE | 批量删除会话 | 支持多个会话 ID   |
| GET /api/conversations/{id}            | GET    | 获取会话详情 | 包含消息列表      |
| GET /api/conversations/{id}/messages   | GET    | 获取历史消息 | 分页加载        |
| POST /api/conversations/{id}/chat      | POST   | 发送消息   | 支持文本和文件     |
| POST /api/conversations/{id}/stream    | POST   | 流式对话   | SSE 实时响应    |
| POST /api/conversations/{id}/interrupt | POST   | 中断对话   | 停止当前处理      |
| GET /api/memory/list                   | GET    | 获取记忆列表 | 分页查询，支持类型筛选 |
| POST /api/memory/create                | POST   | 手动创建记忆 | 添加记忆条目      |
| DELETE /api/memory/delete/{id}         | DELETE | 删除记忆   | 归档记忆        |

### 5.7 容器管理 API

| 端点                                | 方法     | 功能     | 说明        |
| --------------------------------- | ------ | ------ | --------- |
| GET /api/containers/user          | GET    | 获取用户容器 | 自动处理创建和恢复 |
| POST /api/containers/user         | POST   | 创建用户容器 | 手动触发创建    |
| GET /api/containers/user/health   | GET    | 健康检查   | 全面健康检查    |
| GET /admin/containers             | GET    | 容器列表查询 | 管理员分页查询   |
| GET /admin/containers/statistics  | GET    | 容器统计   | 按状态和类型统计  |
| POST /admin/containers/review     | POST   | 创建审核容器 | 管理员专用     |
| POST /admin/containers/{id}/start | POST   | 启动容器   | 管理员操作     |
| POST /admin/containers/{id}/stop  | POST   | 停止容器   | 管理员操作     |
| DELETE /admin/containers/{id}     | DELETE | 删除容器   | 管理员操作     |

### 5.8 计费管理 API

| 端点                                 | 方法   | 功能     | 说明             |
| ---------------------------------- | ---- | ------ | -------------- |
| GET /api/billing/account           | GET  | 获取账户信息 | 余额、信用额度、总消费    |
| GET /api/billing/orders            | GET  | 订单列表   | 分页查询，支持筛选      |
| GET /api/billing/orders/{id}       | GET  | 订单详情   | 订单详细信息         |
| POST /api/billing/recharge         | POST | 创建充值订单 | 指定金额和支付方式      |
| GET /api/billing/payment/{orderId} | GET  | 获取支付链接 | 返回支付 URL 或二维码  |
| GET /api/billing/usage             | GET  | 用量统计   | Token 使用量、消费明细 |

### 5.9 定时任务 API

| 端点                                     | 方法     | 功能     | 说明             |
| -------------------------------------- | ------ | ------ | -------------- |
| GET /api/scheduled-tasks               | GET    | 获取任务列表 | 支持 Agent ID 筛选 |
| POST /api/scheduled-tasks              | POST   | 创建任务   | 指定 cron 表达式    |
| PUT /api/scheduled-tasks/{id}          | PUT    | 更新任务   | 更新配置           |
| DELETE /api/scheduled-tasks/{id}       | DELETE | 删除任务   | 删除定时任务         |
| POST /api/scheduled-tasks/{id}/trigger | POST   | 手动触发   | 立即执行一次         |

## 6. 部署架构

### 6.1 容器化部署

使用 Docker 和 Docker Compose 进行容器化部署，主要服务组件：

```yaml
services:
  # 前端应用
  agentx-frontend:
    image: agentx/frontend:latest
    ports:
      - "80:80"
    depends_on:
      - agentx-backend
  
  # 后端 API 服务
  agentx-backend:
    image: agentx/backend:latest
    ports:
      - "8080:8080"
    environment:
      - SPRING_PROFILES_ACTIVE=prod
      - DATABASE_URL=postgresql://agentx-db:5432/agentx
      - REDIS_URL=redis://agentx-redis:6379
      - RABBITMQ_URL=amqp://agentx-rabbitmq:5672
    depends_on:
      - agentx-db
      - agentx-redis
      - agentx-rabbitmq
  
  # PostgreSQL 数据库
  agentx-db:
    image: postgres:14
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=agentx
      - POSTGRES_USER=agentx
      - POSTGRES_PASSWORD=secure_password
  
  # Redis 缓存
  agentx-redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data
  
  # RabbitMQ 消息队列
  agentx-rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "15672:15672"  # 管理界面
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
  
  # Docker Daemon (用于容器管理)
  docker-dind:
    image: docker:dind
    privileged: true
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
```

### 6.2 Kubernetes 部署

生产环境推荐使用 Kubernetes 进行编排:

```yaml
# Deployment 示例
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agentx-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: agentx-backend
  template:
    spec:
      containers:
      - name: backend
        image: agentx/backend:latest
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /actuator/health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
```

### 6.3 环境配置

| 环境        | 用途    | 特点                            |
| --------- | ----- | ----------------------------- |
| **开发环境**  | 本地开发  | 代码热重载、详细日志、H2 内存数据库、Mock 外部服务 |
| **测试环境**  | 集成测试  | 模拟生产配置、完整依赖服务、自动化测试脚本         |
| **预发布环境** | 上线前验证 | 与生产环境一致、真实数据脱敏、性能压测           |
| **生产环境**  | 正式服务  | 高可用配置、性能优化、安全加固、监控告警          |

### 6.4 扩展性设计

#### 水平扩展

- **无状态服务**：后端 API 服务无状态，支持快速扩容
- **负载均衡**：Nginx/Kubernetes Service 负载均衡
- **会话共享**：Redis 集中存储会话，支持多实例

#### 数据库扩展

- **读写分离**：主从复制，读操作分流到从库
- **数据分片**：按用户 ID 分片，支持海量数据
- **向量数据库**：PGVector 独立部署，支持 GPU 加速

#### 缓存策略

- **多级缓存**：本地缓存 (Caffeine) + 分布式缓存 (Redis)
- **热点数据**：高频访问数据预热到缓存
- **缓存更新**：基于事件的缓存失效机制

#### 消息队列

- **异步解耦**：耗时操作异步处理
- **削峰填谷**：高峰期请求排队处理
- **事件驱动**：领域事件发布订阅模式

## 7. 安全性设计

### 7.1 认证与授权

#### 身份认证

- **JWT Token 认证**：
  - Access Token（短期，15 分钟）
  - Refresh Token（长期，7 天）
  - Token 黑名单机制
- **多因素认证**：
  - 邮箱验证码
  - 图形验证码（防刷）
  - 支持 TOTP（未来扩展）
- **第三方登录**：
  - GitHub OAuth2
  - 支持 Google、微信（扩展）

#### 权限控制

- **RBAC 角色访问控制**：
  - 普通用户（USER）：基础功能使用
  - 管理员（ADMIN）：系统管理、审核权限
  - 超级管理员（SUPER\_ADMIN）：所有权限
- **数据权限隔离**：
  - 用户级数据隔离（user\_id 过滤）
  - 官方资源全局可见
  - 审核资源仅管理员可见
- **API 权限校验**：
  - 基于注解的权限控制
  - 方法级权限校验
  - 数据访问审计日志

### 7.2 数据安全

#### 加密存储

- **密码加密**：BCrypt 强哈希（cost factor=10）
- **敏感信息加密**：
  - API Key 使用 AES-256 加密存储
  - 加密密钥使用 KMS 管理
  - 运行时解密，内存不留存
- **数据传输加密**：
  - HTTPS（TLS 1.3）
  - 内部服务间 mTLS
  - 数据库连接 SSL

#### 数据保护

- **SQL 注入防护**：
  - MyBatis 参数化查询
  - 禁止动态 SQL 拼接
  - SQL 审计日志
- **XSS 防护**：
  - 前端输入验证和转义
  - Content Security Policy (CSP)
  - HTTP Only Cookie
- **CSRF 防护**：
  - CSRF Token 验证
  - SameSite Cookie 属性
  - Referer 检查

#### 隐私保护

- **数据脱敏**：
  - 前端展示脱敏（手机号、邮箱）
  - 日志脱敏处理
  - API Key 掩码显示
- **隐私信息过滤**：
  - 记忆抽取过滤隐私（身份证、银行卡、密码等）
  - 用户数据导出支持
  - 被遗忘权支持（删除账户）

### 7.3 网络安全

#### 边界安全

- **API 网关**：
  - 统一入口，集中鉴权
  - IP 白名单/黑名单
  - 地域访问控制
- **防火墙规则**：
  - 最小权限原则
  - 仅开放必要端口
  - 安全组隔离

#### 访问控制

- **限流熔断**：
  - 单用户 QPS 限制
  - 单 IP 请求频率限制
  - 熔断降级保护
- **DDoS 防护**：
  - 流量清洗
  - CDN 加速
  - 负载均衡分散攻击

#### 容器安全

- **容器隔离**：
  - Docker 命名空间隔离
  - 网络策略（NetworkPolicy）
  - 安全上下文（SecurityContext）
- **镜像安全**：
  - 官方基础镜像
  - 镜像漏洞扫描
  - 镜像签名验证
- **运行时安全**：
  - 只读文件系统
  - 非 root 用户运行
  - 资源限制（CPU/Memory）

### 7.4 审计与合规

#### 审计日志

- **操作审计**：
  - 用户关键操作记录
  - 管理员操作审计
  - 敏感数据访问日志
- **系统审计**：
  - 登录认证日志
  - 权限变更日志
  - 配置修改日志

#### 合规性

- **数据保留策略**：
  - 日志保留 180 天
  - 审计日志永久保存
  - 过期数据自动清理
- **数据主权**：
  - 数据本地化存储
  - 跨境数据传输合规
  - GDPR 合规支持

## 8. 监控与日志

### 8.1 监控体系

#### 应用监控（Application Monitoring）

- **业务指标**：
  - API 请求量、响应时间（P50/P90/P99）
  - 错误率和失败请求数
  - 活跃用户数、会话数
  - Agent 创建数、工具安装数
  - Token 消耗量、计费金额
- **JVM 监控**：
  - Heap/Non-Heap 内存使用
  - GC 次数和时间
  - 线程池状态
  - 类加载统计
- **依赖服务监控**：
  - 数据库连接池（HikariCP）
  - Redis 连接和命中率
  - RabbitMQ 队列深度
  - LLM API 调用成功率

#### 系统监控（System Monitoring）

- **节点资源**：
  - CPU 使用率和负载
  - 内存使用率
  - 磁盘使用率和 I/O
  - 网络带宽和流量
- **容器监控**：
  - 容器运行状态
  - 容器资源使用（CPU/Memory）
  - 容器重启次数
  - 容器网络连通性
- **Kubernetes 监控**：
  - Pod 状态和重启
  - Node 健康度
  - 资源配额使用
  - HPA 自动扩缩容

#### 数据库监控

- **PostgreSQL**：
  - QPS/TPS
  - 慢查询统计
  - 连接数和等待
  - 锁等待和死锁
  - 复制延迟（主从）
- **PGVector**：
  - 向量检索延迟
  - 索引构建进度
  - 向量数据量增长
- **Redis**：
  - 命中率和未命中数
  - Key 数量和过期数
  - 内存碎片率
  - 持久化状态

#### 消息队列监控

- **RabbitMQ**：
  - 队列深度和消息积压
  - 生产者和消费者速率
  - 消息确认和重试
  - 死信队列消息数
- **事件处理**：
  - 领域事件发布量
  - 事件处理延迟
  - 事件失败重试次数

#### 链路追踪（Distributed Tracing）

- **调用链追踪**：
  - 全链路 TraceID 传递
  - Span 耗时分析
  - 依赖服务调用拓扑
  - 慢调用定位
- **关键链路**：
  - 对话请求完整链路
  - 工具调用链路
  - RAG 检索链路
  - 支付流程链路

### 8.2 日志系统

#### 日志分级

```java
ERROR  - 系统错误，需要立即处理（如数据库连接失败）
WARN   - 警告信息，可能影响功能（如 API 调用超时）
INFO   - 重要业务信息（如用户登录、订单创建）
DEBUG  - 调试信息，开发环境使用
TRACE  - 详细追踪信息，问题排查使用
```

#### 日志分类

- **应用日志**：
  - 业务日志：用户操作、订单流转、状态变更
  - 访问日志：API 请求、响应时间、状态码
  - 错误日志：异常堆栈、错误上下文
- **系统日志**：
  - 操作系统日志：系统事件、安全审计
  - Docker 日志：容器启动停止、资源事件
  - Kubernetes 日志：Pod 调度、事件日志
- **审计日志**：
  - 用户行为审计：登录、权限变更、敏感操作
  - 管理员审计：配置修改、审核操作
  - 数据访问审计：敏感数据查询、导出

#### 日志收集与分析

- **收集方案**：
  - Filebeat 收集文件日志
  - Fluentd 统一日志管道
  - Logstash 日志处理和过滤
- **存储方案**：
  - Elasticsearch 全文检索
  - 冷热数据分离（热数据 SSD，冷数据 HDD）
  - 日志索引生命周期管理（ILM）
- **分析展示**：
  - Kibana 日志可视化
  - 自定义仪表盘
  - 告警规则配置

#### 日志规范

```java
// 推荐格式
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "service": "agentx-backend",
  "trace_id": "abc123def456",
  "user_id": "uuid",
  "action": "AGENT_CREATED",
  "message": "Agent created successfully",
  "data": {"agent_id": "uuid", "agent_name": "客服助手"}
}
```

### 8.3 告警系统

#### 告警级别

- **P0 - 紧急**：系统不可用，需立即响应（5 分钟内）
  - 核心服务宕机
  - 数据库不可用
  - 大面积用户无法访问
- **P1 - 严重**：核心功能受损，需快速响应（15 分钟内）
  - 支付失败率 > 5%
  - LLM 调用失败率 > 20%
  - 容器批量失败
- **P2 - 警告**：部分功能异常，需及时处理（1 小时内）
  - API 响应时间 > 3s
  - 单点故障风险
  - 资源使用率 > 80%
- **P3 - 提示**：需要关注的问题（24 小时内）
  - 非核心功能异常
  - 性能轻微下降
  - 配置变更通知

#### 告警渠道

- **即时通知**：企业微信、钉钉、Slack
- **电话短信**：P0/P1 级别电话通知
- **邮件通知**：日报、周报、汇总告警
- **值班轮岗**：On-call 排班制度

#### 告警收敛

- **告警合并**：相同根因告警合并
- **静默期**：避免重复告警（5-15 分钟）
- **依赖抑制**：下游故障不触发上游告警
- **智能降噪**：基于 AI 的告警分组和优先级调整

## 9. 性能优化

### 9.1 后端性能优化

#### 数据库优化

- **索引优化**：
  - 为高频查询字段创建索引（user\_id, status, created\_at）
  - 向量数据库索引（HNSW、IVFFLAT）
  - 复合索引优化多条件查询
  - 定期分析索引使用情况
- **查询优化**：
  - 避免 N+1 查询（使用 JOIN FETCH）
  - 分页查询限制最大页数
  - 慢查询日志和分析
  - SQL 执行计划分析
- **连接池优化**：
  - HikariCP 参数调优
  - 合理设置最大/最小连接数
  - 连接超时和空闲回收

#### 缓存策略

- **多级缓存架构**：
  ```
  L1 Cache (Caffeine) - 本地内存缓存，纳秒级访问
       ↓
  L2 Cache (Redis) - 分布式缓存，毫秒级访问
       ↓
  Database - 持久化存储
  ```
- **缓存场景**：
  - 用户信息、配置信息
  - Agent 基础数据
  - LLM 服务商和模型列表
  - Token 余额和配额
  - 会话上下文
- **缓存更新策略**：
  - Cache-Aside（旁路缓存）
  - Write-Through（写穿透）
  - 基于事件的缓存失效
  - 定时刷新热点数据

#### 异步处理

- **线程池优化**：
  - 核心线程池（CPU 密集型）
  - IO 线程池（IO 密集型）
  - 定时任务线程池
  - 异步事件处理线程池
- **异步场景**：
  - 文件上传和处理（OCR、向量化）
  - 工具部署和审核
  - 记忆抽取和向量化
  - 邮件和通知发送
  - 计费扣费处理
- **消息队列异步**：
  - RabbitMQ 削峰填谷
  - 领域事件异步处理
  - 批量操作队列

#### 批处理优化

- **批量操作**：
  - 批量插入消息（MyBatis Batch）
  - 批量删除会话
  - 批量同步模型到网关
- **流式处理**：
  - 大文件分块上传
  - 流式响应（SSE）
  - Reactor 响应式编程（可选）

### 9.2 前端性能优化

#### 加载性能

- **代码分割**：
  - 路由级别懒加载
  - 组件级别动态导入
  - 第三方库分离打包
- **资源优化**：
  - Tree Shaking 移除无用代码
  - 图片懒加载和 WebP 格式
  - CSS 压缩和提取
  - JavaScript 压缩和混淆
- **预加载策略**：
  - DNS Prefetch
  - Resource Hints（preload, prefetch）
  - 关键资源提前加载

#### 渲染性能

- **React 优化**：
  - React.memo 避免不必要重渲染
  - useMemo/useCallback 缓存
  - Virtual List 虚拟滚动
  - 防抖节流优化
- **状态管理优化**：
  - 细粒度状态更新
  - 避免全局状态滥用
  - 状态选择器优化

#### 网络优化

- **HTTP 优化**：
  - HTTP/2 多路复用
  - Gzip/Brotli 压缩
  - 长连接 Keep-Alive
- **CDN 加速**：
  - 静态资源 CDN 分发
  - 边缘节点缓存
  - 智能 DNS 解析
- **请求优化**：
  - 请求合并
  - GraphQL 按需查询
  - 接口数据裁剪

### 9.3 LLM 调用优化

#### Token 优化

- **上下文管理**：
  - 滑动窗口保留最近对话
  - 摘要压缩历史消息
  - Token 溢出策略（NONE/SLIDING\_WINDOW/SUMMARY）
- **Prompt 优化**：
  - Prompt 模板化
  - Few-shot 示例精选
  - 系统提示词精简

#### 调用优化

- **智能路由**：
  - 高可用网关选择最优实例
  - 会话亲和性减少切换
  - 负载均衡分散压力
- **缓存机制**：
  - 常见问题答案缓存
  - Embedding 结果缓存
  - 相似查询复用

#### 降级策略

- **故障转移**：主模型失败自动切换备用模型
- **降级链**：按优先级依次尝试
- **限流保护**：超过阈值拒绝或排队

### 9.4 容器性能优化

#### 资源优化

- **CPU/Memory 限制**：
  - 防止单容器占用过多资源
  - OOM Killer 保护
  - CPU Throttling 控制
- **弹性伸缩**：
  - 基于负载自动扩缩容
  - 闲置容器暂停/删除
  - 高峰期提前扩容

#### 启动优化

- **镜像优化**：
  - 多层镜像缓存
  - 减小镜像体积
  - 分层构建
- **快速启动**：
  - 预热容器池
  - 快照恢复
  - 并行启动多个容器

### 9.5 性能指标目标

| 指标         | 目标值     | 测量方式                 |
| ---------- | ------- | -------------------- |
| API P99 延迟 | < 500ms | Prometheus + Grafana |
| 首 Token 时间 | < 3s    | 链路追踪                 |
| 页面加载时间     | < 2s    | Lighthouse           |
| 数据库查询 P95  | < 100ms | PG Stat Statements   |
| Redis 命中率  | > 90%   | Redis INFO           |
| 容器启动时间     | < 30s   | Docker Events        |
| 向量检索延迟     | < 500ms | 基准测试                 |
| 系统可用性      | > 99.9% | SLA 监控               |

## 10. 未来规划

### 10.1 短期规划（3-6 个月）

#### 功能增强

- **多语言支持**：
  - 前端国际化（i18n）支持中英文切换
  - Agent 多语言界面和响应
  - 文档和帮助中心多语言版本
- **高级 RAG 能力**：
  - 表格和图片内容理解
  - 多跳检索（Multi-hop Retrieval）
  - 自动查询改写和优化
- **Agent 能力提升**：
  - 代码执行沙箱环境
  - 文件生成和下载
  - 语音交互支持（TTS/ASR）

#### 技术升级

- **性能优化**：
  - 向量检索 GPU 加速
  - 数据库读写分离
  - CDN 全球加速
- **可观测性提升**：
  - 全链路追踪完善
  - 业务指标仪表盘
  - 智能告警和根因分析

### 10.2 中期规划（6-12 个月）

#### 生态建设

- **工具市场繁荣**：
  - 吸引更多开发者上传工具
  - 建立工具质量评分体系
  - 热门工具推荐和排行榜
- **RAG 市场运营**：
  - 优质知识库模板
  - 行业解决方案包
  - 知识共享和交易机制
- **Agent 商店**：
  - 精品 Agent 推荐
  - Agent 评分和评论
  - Agent 分润机制

#### 架构演进

- **微服务化**：
  - 核心服务拆分（用户、Agent、对话、计费独立部署）
  - Service Mesh（Istio）服务网格
  - 分布式事务管理（Seata）
- **云原生升级**：
  - Kubernetes 全面编排
  - Serverless 函数计算
  - 混合云部署支持

### 10.3 长期愿景（1-2 年）

#### 智能化升级

- **AI 辅助开发**：
  - Agent 自动生成和调试
  - Prompt 自动优化
  - 工作流智能编排
- **多 Agent 协作**：
  - Agent 间通信协议
  - 任务自动分配和协调
  - 群体智能涌现
- **自主学习能力**：
  - 基于反馈的持续优化
  - 用户偏好自动学习
  - 知识库自动更新

#### 平台开放

- **Open API 生态**：
  - 完善的开发者文档
  - SDK 和 CLI 工具
  - 第三方应用集成
- **插件系统**：
  - 自定义认证提供者
  - 自定义存储后端
  - 自定义消息处理器
- **行业解决方案**：
  - 企业私有化部署
  - 行业定制版本（教育、医疗、金融）
  - 白标解决方案

#### 全球化布局

- **多区域部署**：
  - 全球多数据中心
  - 数据本地化合规
  - 跨区域容灾备份
- **合规认证**：
  - ISO 27001 信息安全认证
  - SOC 2 Type II 审计
  - GDPR 合规认证
  - 等保三级认证

### 10.4 技术债务与改进

#### 当前技术债务

- 异步处理机制待完善
- 部分模块单元测试覆盖率低
- 文档需要持续更新
- 性能基准测试不足

#### 持续改进方向

- **代码质量**：
  - 提高测试覆盖率（目标 > 80%）
  - 代码审查流程规范化
  - 静态代码分析集成
- **工程效能**：
  - CI/CD 流水线优化
  - 自动化测试覆盖
  - 灰度发布和 A/B 测试
- **技术预研**：
  - 新 LLM 模型快速集成
  - 向量数据库选型优化
  - 容器编排新技术跟踪

***

## 附录

### A. 术语表

| 术语        | 英文                                 | 说明                  |
| --------- | ---------------------------------- | ------------------- |
| Agent     | Agent                              | AI 智能体，能够自主完成任务     |
| MCP       | Model Context Protocol             | 模型上下文协议，标准化工具接口     |
| RAG       | Retrieval-Augmented Generation     | 检索增强生成，结合检索和生成的问答技术 |
| LLM       | Large Language Model               | 大型语言模型              |
| Embedding | Embedding                          | 将文本转换为向量的技术         |
| Token     | Token                              | LLM 处理文本的基本单位       |
| SSE       | Server-Sent Events                 | 服务器推送事件协议           |
| JWT       | JSON Web Token                     | 身份认证令牌              |
| RBAC      | Role-Based Access Control          | 基于角色的访问控制           |
| HNSW      | Hierarchical Navigable Small World | 高效近似最近邻搜索算法         |

### B. 参考文档

- [Spec 规范目录](./specs/)
- [OpenSpec 变更管理](./openspec/)
- [开发文档](./docs/develop_document.md)
- [Token 溢出策略](./docs/token_overflow_strategy.md)
- [计费系统文档](./docs/billing/)

### C. 版本历史

| 版本  | 日期      | 作者                | 变更说明            |
| --- | ------- | ----------------- | --------------- |
| 1.0 | 2024-01 | Architecture Team | 初始版本            |
| 2.0 | 2026-03 | Architecture Team | 基于 specs 目录全面重构 |

***

*本文档最后更新：2026 年 3 月*
