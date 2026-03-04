# AgentX - 智能 Agent 构建平台

AgentX 是一个基于大模型 (LLM) 和多能力平台 (MCP) 的智能 Agent 构建平台。它致力于简化 Agent 的创建流程，让用户无需复杂的流程节点或拖拽操作，仅通过自然语言和工具集成即可打造个性化的智能 Agent。

## 功能特性

- **Agent 管理**：创建、发布和管理智能 Agent
- **LLM 上下文管理**：滑动窗口、摘要算法
- **Agent 策略**：基于 MCP (Multi-Capability Platform) 的策略管理
- **大模型服务商集成**：支持多种大模型服务
- **用户管理**：用户认证、权限控制
- **工具市场**：丰富的工具生态
- **MCP Server Community**：社区贡献的 MCP 服务
- **MCP Gateway**：MCP 服务统一管理
- **预先设置工具**：常用工具的预设配置
- **Agent 定时任务**：自动化任务调度
- **Agent OpenAPI**：开放 API 接口
- **模型高可用组件**：确保服务稳定运行
- **RAG (Retrieval-Augmented Generation)**：增强生成能力
- **计费系统**：使用统计和计费
- **Agent 监控**：性能和状态监控
- **嵌入网站组件**：易于集成到现有网站
- **Multi Agent**：多 Agent 协作
- **知识图谱**：结构化知识管理
- **长期记忆**：Agent 记忆能力

## 技术架构

### 后端架构

- **语言**：Python
- **API 框架**：FastAPI
- **数据库**：PostgreSQL
- **消息队列**：RabbitMQ
- **认证**：JWT
- **缓存**：Redis (可选)
- **部署**：Docker

### 前端架构

- **框架**：React
- **状态管理**：Redux
- **UI 组件**：Ant Design
- **API 调用**：Axios

## 快速开始

### 一键部署（推荐）

适用于想要快速体验完整功能的用户，无需下载源码，一个命令启动所有服务：

1. **准备配置文件**

```bash
# 下载配置文件模板
curl -O https://raw.githubusercontent.com/lucky-aeon/AgentX/master/.env.example
# 复制并编辑配置
cp .env.example .env
# 根据需要修改 .env 文件中的配置
```

2. **启动服务**

```bash
docker run -d \
  --name agentx \
  -p 3000:3000 \
  -p 8088:8088 \
  -p 5432:5432 \
  -p 5672:5672 \
  -p 15672:15672 \
  --env-file .env \
  -v agentx-data:/var/lib/postgresql/data \
  -v agentx-storage:/app/storage \
  -v /var/run/docker.sock:/var/run/docker.sock\
  --add-host=localhost:host-gateway \
  ghcr.nju.edu.cn/lucky-aeon/agentx:latest
```

### 开发环境部署

适用于需要修改代码或定制功能的开发者：

1. **克隆项目**

```bash
git clone https://github.com/lucky-aeon/AgentX.git
cd AgentX/deploy
```

2. **启动开发环境**

- Linux/macOS:
  ```bash
  ./start.sh
  ```

- Windows:
  ```bash
  start.bat
  ```

## 服务访问

| 服务 | 地址 | 说明 |
|------|------|------|
| 主应用 | http://localhost:3000 | 前端界面 |
| 后端API | http://localhost:8088 | API服务 |
| 数据库 | http://localhost:5432 | PostgreSQL（可选） |
| RabbitMQ | http://localhost:5672 | 消息队列（可选） |
| RabbitMQ管理 | http://localhost:15672 | 队列管理界面（可选） |

### 高可用网关（可选）

如需API高可用功能，可额外部署：

```bash
docker run -d \
  --name agentx-gateway \
  -p 8081:8081 \
  ghcr.io/lucky-aeon/api-premium-gateway:latest
```

## 默认登录账号

- **管理员**：admin@agentx.ai / admin123
- **测试用户**：test@agentx.ai / test123

## 环境变量配置

AgentX使用.env配置文件进行环境变量管理，支持丰富的自定义配置：

### 配置文件说明

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| **基础服务** | | |
| SERVER_PORT | 后端API端口 | 8088 |
| DB_PASSWORD | 数据库密码 | agentx_pass |
| RABBITMQ_PASSWORD | 消息队列密码 | guest |
| **安全配置** | | |
| JWT_SECRET | JWT密钥（必须修改） | 需要设置 |
| AGENTX_ADMIN_PASSWORD | 管理员密码 | admin123 |
| **外部服务** | | |
| EXTERNAL_DB_HOST | 外部数据库地址 | 空（使用内置） |
| EXTERNAL_RABBITMQ_HOST | 外部消息队列地址 | 空（使用内置） |

### 快速配置

1. **获取配置模板**

```bash
curl -O https://raw.githubusercontent.com/lucky-aeon/AgentX/main/.env.example
```

2. **创建配置文件**

```bash
cp .env.example .env
```

3. **编辑配置（必改项）**

```bash
vim .env
```

**必须修改的配置项**：
- JWT_SECRET: 设置安全的JWT密钥（至少32字符）
- AGENTX_ADMIN_PASSWORD: 修改管理员密码
- DB_PASSWORD: 修改数据库密码

## 项目结构

```
agentx-py/
├── app/
│   ├── api/             # API路由
│   ├── core/            # 核心功能
│   ├── models/          # 数据模型
│   ├── services/        # 业务逻辑
│   ├── schemas/         # 数据验证
│   ├── utils/           # 工具函数
│   └── main.py          # 应用入口
├── config/              # 配置文件
├── migrations/          # 数据库迁移
├── tests/               # 测试代码
├── Dockerfile           # Docker配置
├── docker-compose.yml   # Docker Compose配置
├── requirements.txt     # 依赖包
├── .env.example         # 环境变量模板
├── README.md            # 项目说明
└── TODO.md              # 待办事项
```

## 开发指南

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行开发服务器

```bash
uvicorn app.main:app --reload
```

### 运行测试

```bash
pytest
```

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 开启 Pull Request

## 许可证

MIT License

## 联系方式

- GitHub: [https://github.com/lucky-aeon/AgentX](https://github.com/lucky-aeon/AgentX)
- 项目教程: B站视频教程
- 详细教学: 敲鸭社区 - code.xhyovo.cn
- 项目演示: 在线PPT介绍