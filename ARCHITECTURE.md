# AgentX 架构设计文档

## 1. 整体架构

AgentX 采用分层架构设计，将系统分为前端、后端 API、服务层和数据层四个主要部分。系统通过 MCP (Multi-Capability Platform) 实现能力的扩展和管理，通过消息队列实现异步任务处理，通过 PostgreSQL 存储结构化数据。

### 1.1 架构层次

```
┌─────────────────────┐
│     前端应用        │
│  (React + Antd)     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│     后端 API        │
│  (FastAPI)          │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    服务层           │
│  (业务逻辑)         │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│    数据层           │
│  (PostgreSQL)       │
└─────────────────────┘

┌─────────────────────┐
│  消息队列           │
│  (RabbitMQ)         │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  异步任务处理       │
└─────────────────────┘
```

## 2. 核心模块设计

### 2.1 Agent 管理模块

- **功能**：创建、编辑、发布、管理 Agent
- **核心组件**：
  - Agent 模型：定义 Agent 的基本属性和配置
  - Agent 服务：处理 Agent 的业务逻辑
  - Agent API：提供 Agent 相关的 API 接口
- **数据流**：
  1. 前端请求创建 Agent
  2. API 层接收请求并验证
  3. 服务层处理业务逻辑
  4. 数据层存储 Agent 信息
  5. 返回创建结果

### 2.2 LLM 上下文管理模块

- **功能**：管理 Agent 与大模型的交互上下文，包括滑动窗口和摘要算法
- **核心组件**：
  - 上下文管理器：处理上下文的存储和更新
  - 摘要生成器：生成上下文摘要
  - 窗口管理器：维护滑动窗口
- **数据流**：
  1. Agent 与用户交互产生新的消息
  2. 上下文管理器更新上下文
  3. 检查上下文长度，超过阈值时生成摘要
  4. 维护滑动窗口，保留最近的交互

### 2.3 MCP (Multi-Capability Platform) 模块

- **功能**：管理 Agent 的能力和策略
- **核心组件**：
  - MCP 服务注册：注册和管理 MCP 服务
  - MCP 网关：统一管理 MCP 服务的调用
  - MCP 策略：定义 Agent 使用 MCP 服务的策略
- **数据流**：
  1. MCP 服务注册到系统
  2. Agent 配置使用 MCP 服务的策略
  3. Agent 执行时根据策略调用 MCP 服务
  4. MCP 网关路由请求到相应的服务

### 2.4 用户管理模块

- **功能**：管理用户账号、认证和权限
- **核心组件**：
  - 用户模型：定义用户属性和权限
  - 认证服务：处理用户登录和 JWT 生成
  - 权限管理器：控制用户访问权限
- **数据流**：
  1. 用户登录请求
  2. 认证服务验证用户凭据
  3. 生成 JWT token
  4. 后续请求携带 token 进行权限验证

### 2.5 工具市场模块

- **功能**：管理和提供工具给 Agent 使用
- **核心组件**：
  - 工具模型：定义工具的属性和参数
  - 工具注册：注册和管理工具
  - 工具调用：执行工具并返回结果
- **数据流**：
  1. 工具开发者注册工具
  2. Agent 配置使用工具
  3. Agent 执行时调用工具
  4. 工具执行并返回结果给 Agent

### 2.6 定时任务模块

- **功能**：管理 Agent 的定时任务
- **核心组件**：
  - 任务调度器：调度定时任务
  - 任务执行器：执行定时任务
  - 任务模型：定义任务属性和配置
- **数据流**：
  1. 用户配置 Agent 定时任务
  2. 任务调度器根据配置调度任务
  3. 任务执行器执行 Agent 任务
  4. 记录任务执行结果

### 2.7 RAG (Retrieval-Augmented Generation) 模块

- **功能**：增强 Agent 的生成能力，通过检索相关信息
- **核心组件**：
  - 向量数据库：存储和检索向量嵌入
  - 检索器：根据查询检索相关信息
  - 生成器：结合检索结果生成响应
- **数据流**：
  1. 用户查询 Agent
  2. 检索器根据查询检索相关信息
  3. 生成器结合检索结果和上下文生成响应
  4. 返回响应给用户

## 3. 技术栈选择

### 3.1 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主要开发语言 |
| FastAPI | 0.104+ | API 框架 |
| PostgreSQL | 14+ | 关系型数据库 |
| RabbitMQ | 3.10+ | 消息队列 |
| Redis | 7.0+ | 缓存（可选） |
| JWT | - | 认证 |
| SQLAlchemy | 2.0+ | ORM |
| Pydantic | 2.0+ | 数据验证 |
| Celery | 5.3+ | 异步任务处理 |

### 3.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| React | 18+ | 前端框架 |
| Redux | 4.2+ | 状态管理 |
| Ant Design | 5.0+ | UI 组件库 |
| Axios | 1.6+ | HTTP 客户端 |
| TypeScript | 5.0+ | 类型系统 |

## 4. 数据库设计

### 4.1 核心表结构

#### 4.1.1 users 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | SERIAL | PRIMARY KEY | 用户 ID |
| email | VARCHAR(255) | UNIQUE NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| name | VARCHAR(100) | NOT NULL | 用户名 |
| role | VARCHAR(20) | NOT NULL | 角色 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.2 agents 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | SERIAL | PRIMARY KEY | Agent ID |
| name | VARCHAR(100) | NOT NULL | Agent 名称 |
| description | TEXT | | 描述 |
| user_id | INTEGER | REFERENCES users(id) | 创建者 ID |
| config | JSONB | NOT NULL | 配置信息 |
| status | VARCHAR(20) | NOT NULL | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.3 mcp_services 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | SERIAL | PRIMARY KEY | 服务 ID |
| name | VARCHAR(100) | NOT NULL | 服务名称 |
| description | TEXT | | 描述 |
| endpoint | VARCHAR(255) | NOT NULL | 服务端点 |
| config | JSONB | NOT NULL | 配置信息 |
| status | VARCHAR(20) | NOT NULL | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.4 tools 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | SERIAL | PRIMARY KEY | 工具 ID |
| name | VARCHAR(100) | NOT NULL | 工具名称 |
| description | TEXT | | 描述 |
| function_name | VARCHAR(100) | NOT NULL | 函数名称 |
| parameters | JSONB | NOT NULL | 参数定义 |
| status | VARCHAR(20) | NOT NULL | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

#### 4.1.5 tasks 表

| 字段名 | 数据类型 | 约束 | 描述 |
|--------|----------|------|------|
| id | SERIAL | PRIMARY KEY | 任务 ID |
| agent_id | INTEGER | REFERENCES agents(id) | Agent ID |
| name | VARCHAR(100) | NOT NULL | 任务名称 |
| schedule | VARCHAR(100) | NOT NULL | 调度表达式 |
| config | JSONB | NOT NULL | 配置信息 |
| status | VARCHAR(20) | NOT NULL | 状态 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

## 5. API 设计

### 5.1 认证 API

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/auth/login | POST | 用户登录 | `{"email": "...", "password": "..."}` | `{"access_token": "...", "token_type": "bearer"}` |
| /api/auth/register | POST | 用户注册 | `{"email": "...", "password": "...", "name": "..."}` | `{"id": 1, "email": "...", "name": "..."}` |
| /api/auth/me | GET | 获取当前用户信息 | N/A | `{"id": 1, "email": "...", "name": "..."}` |

### 5.2 Agent API

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/agents | GET | 获取 Agent 列表 | N/A | `[{"id": 1, "name": "...", "description": "..."}]` |
| /api/agents | POST | 创建 Agent | `{"name": "...", "description": "...", "config": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/agents/{id} | GET | 获取 Agent 详情 | N/A | `{"id": 1, "name": "...", "description": "...", "config": {...}}` |
| /api/agents/{id} | PUT | 更新 Agent | `{"name": "...", "description": "...", "config": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/agents/{id} | DELETE | 删除 Agent | N/A | `{"message": "Agent deleted"}` |
| /api/agents/{id}/publish | POST | 发布 Agent | N/A | `{"message": "Agent published"}` |

### 5.3 MCP API

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/mcp/services | GET | 获取 MCP 服务列表 | N/A | `[{"id": 1, "name": "...", "description": "..."}]` |
| /api/mcp/services | POST | 注册 MCP 服务 | `{"name": "...", "description": "...", "endpoint": "...", "config": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/mcp/services/{id} | GET | 获取 MCP 服务详情 | N/A | `{"id": 1, "name": "...", "description": "...", "endpoint": "...", "config": {...}}` |
| /api/mcp/services/{id} | PUT | 更新 MCP 服务 | `{"name": "...", "description": "...", "endpoint": "...", "config": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/mcp/services/{id} | DELETE | 删除 MCP 服务 | N/A | `{"message": "Service deleted"}` |

### 5.4 Tool API

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/tools | GET | 获取工具列表 | N/A | `[{"id": 1, "name": "...", "description": "..."}]` |
| /api/tools | POST | 注册工具 | `{"name": "...", "description": "...", "function_name": "...", "parameters": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/tools/{id} | GET | 获取工具详情 | N/A | `{"id": 1, "name": "...", "description": "...", "function_name": "...", "parameters": {...}}` |
| /api/tools/{id} | PUT | 更新工具 | `{"name": "...", "description": "...", "function_name": "...", "parameters": {...}}` | `{"id": 1, "name": "...", "description": "..."}` |
| /api/tools/{id} | DELETE | 删除工具 | N/A | `{"message": "Tool deleted"}` |

### 5.5 Task API

| 端点 | 方法 | 功能 | 请求体 | 响应 |
|------|------|------|--------|------|
| /api/tasks | GET | 获取任务列表 | N/A | `[{"id": 1, "name": "...", "agent_id": 1, "schedule": "..."}]` |
| /api/tasks | POST | 创建任务 | `{"agent_id": 1, "name": "...", "schedule": "...", "config": {...}}` | `{"id": 1, "name": "...", "agent_id": 1, "schedule": "..."}` |
| /api/tasks/{id} | GET | 获取任务详情 | N/A | `{"id": 1, "name": "...", "agent_id": 1, "schedule": "...", "config": {...}}` |
| /api/tasks/{id} | PUT | 更新任务 | `{"name": "...", "schedule": "...", "config": {...}}` | `{"id": 1, "name": "...", "agent_id": 1, "schedule": "..."}` |
| /api/tasks/{id} | DELETE | 删除任务 | N/A | `{"message": "Task deleted"}` |

## 6. 部署架构

### 6.1 容器化部署

使用 Docker 和 Docker Compose 进行容器化部署，包括以下服务：

- **agentx-frontend**：前端应用
- **agentx-backend**：后端 API 服务
- **agentx-db**：PostgreSQL 数据库
- **agentx-rabbitmq**：RabbitMQ 消息队列
- **agentx-gateway**：高可用网关（可选）

### 6.2 环境配置

- **开发环境**：本地开发，代码热重载，详细日志
- **测试环境**：模拟生产环境，用于测试
- **生产环境**：正式部署，优化性能，安全配置

### 6.3 扩展性考虑

- **水平扩展**：支持多实例部署，通过负载均衡分发请求
- **服务拆分**：可将核心服务拆分为独立微服务
- **数据分片**：支持数据库水平分片，应对大数据量

## 7. 安全性设计

### 7.1 认证与授权

- **JWT 认证**：使用 JSON Web Token 进行身份验证
- **密码加密**：使用 bcrypt 对密码进行哈希处理
- **权限控制**：基于角色的访问控制 (RBAC)
- **API 限流**：防止 API 滥用

### 7.2 数据安全

- **数据加密**：敏感数据加密存储
- **SQL 注入防护**：使用参数化查询
- **XSS 防护**：前端输入验证
- **CSRF 防护**：使用 CSRF token

### 7.3 网络安全

- **HTTPS**：使用 SSL/TLS 加密传输
- **防火墙**：配置防火墙规则
- **网络隔离**：容器网络隔离

## 8. 监控与日志

### 8.1 监控

- **应用监控**：监控 API 响应时间、错误率
- **系统监控**：监控服务器 CPU、内存、磁盘使用
- **数据库监控**：监控数据库性能、连接数
- **消息队列监控**：监控队列长度、处理速度

### 8.2 日志

- **应用日志**：记录 API 请求、错误信息
- **系统日志**：记录系统事件、异常
- **审计日志**：记录用户操作、权限变更

## 9. 性能优化

### 9.1 后端优化

- **缓存**：使用 Redis 缓存热点数据
- **数据库优化**：索引优化、查询优化
- **异步处理**：使用 Celery 处理耗时任务
- **代码优化**：减少不必要的计算和 I/O 操作

### 9.2 前端优化

- **代码分割**：按需加载代码
- **资源压缩**：压缩 JS、CSS、图片
- **缓存策略**：合理设置缓存头
- **CDN**：使用 CDN 加速静态资源

## 10. 未来规划

- **多语言支持**：支持多语言界面和 Agent
- **更多大模型集成**：集成更多大模型服务
- **更丰富的工具生态**：扩展工具市场
- **AI 辅助开发**：使用 AI 辅助 Agent 开发
- **边缘部署**：支持边缘设备部署
- **更智能的 Agent 协作**：多 Agent 协同工作