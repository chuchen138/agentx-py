## Context

**背景:**
AgentX 平台目前处于初始化阶段，需要构建核心的 Agent 管理功能。根据项目架构文档，系统采用 FastAPI + PostgreSQL + SQLAlchemy 技术栈，需要实现完整的 CRUD 操作和 JWT 认证集成。

**当前状态:**
- 项目目录结构已建立 (ARCHITECTURE.md, README.md, TODO.md)
- openspec 配置已完成
- 缺少实际的代码实现
- 数据库表结构仅存在于设计文档中

**约束条件:**
- 必须遵循 PEP 8 代码规范
- 需要使用类型注解
- 必须包含完整的文档字符串
- 需要集成 JWT 认证
- 使用 Pydantic 进行数据验证

**利益相关者:**
- 后端开发团队
- 前端开发团队 (将消费这些 API)
- 最终用户 (需要稳定可靠的 Agent 管理功能)

## Goals / Non-Goals

**Goals:**
- 实现完整的 Agent CRUD API 端点
- 设计合理的数据库表结构
- 集成 JWT 认证保护 API
- 提供清晰的数据验证和错误处理
- 为后续模块开发提供范例

**Non-Goals:**
- 前端界面实现
- Agent 与 LLM 的实际交互逻辑
- 复杂的业务规则验证
- 性能优化和缓存策略
- 监控和日志系统

## Decisions

### 1. 项目分层架构

**决策:** 采用经典的三层架构
```
┌─────────────────┐
│   API Layer     │  (routes/)
├─────────────────┤
│  Service Layer  │  (services/)
├─────────────────┤
│  Data Layer     │  (models/)
└─────────────────┘
```

**理由:**
- 清晰的职责分离
- 便于测试和维护
- 符合 FastAPI 最佳实践
- 与 ARCHITECTURE.md 保持一致

**替代方案考虑:**
- 使用 Repository 模式：增加了一层抽象，但对于当前复杂度可能过度设计
- 使用 DDD 领域驱动设计：对于初期项目过于复杂

### 2. 数据库设计

**决策:** 使用 SQLAlchemy ORM + Alembic 迁移

```sql
-- agents 表结构
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id),
    config JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_agents_user_id ON agents(user_id);
CREATE INDEX idx_agents_status ON agents(status);
```

**理由:**
- SQLAlchemy 提供强大的 ORM 功能
- Alembic 支持数据库版本控制
- JSONB 字段提供灵活的配置存储
- 索引优化查询性能

### 3. API 设计

**决策:** RESTful API 风格

```
GET    /api/agents          # 获取 Agent 列表
POST   /api/agents          # 创建 Agent
GET    /api/agents/{id}     # 获取 Agent 详情
PUT    /api/agents/{id}     # 更新 Agent
DELETE /api/agents/{id}     # 删除 Agent
POST   /api/agents/{id}/publish  # 发布 Agent
```

**响应格式:**
```json
{
  "id": 1,
  "name": "My Agent",
  "description": "...",
  "user_id": 1,
  "config": {...},
  "status": "draft",
  "created_at": "2026-03-05T01:00:00Z",
  "updated_at": "2026-03-05T01:00:00Z"
}
```

**理由:**
- RESTful 是业界标准
- 易于理解和消费
- 与前端框架良好集成
- 支持未来的版本演进

### 4. 认证策略

**决策:** JWT Bearer Token 认证

```python
# 依赖注入示例
from fastapi import Depends
from app.core.security import get_current_user

@router.get("/agents")
async def list_agents(current_user: User = Depends(get_current_user)):
    ...
```

**理由:**
- 无状态认证，适合分布式部署
- 支持细粒度的权限控制
- 与现有架构文档一致
- 成熟的生态和库支持

### 5. 数据验证

**决策:** 使用 Pydantic v2 Schema

```python
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    config: dict = Field(default_factory=dict)
```

**理由:**
- 与 FastAPI 深度集成
- 强大的验证能力
- 自动生成 OpenAPI 文档
- 良好的类型支持

## Risks / Trade-offs

### [风险] 数据库连接池配置不当

**影响:** 可能导致性能问题或连接耗尽

**缓解措施:**
- 使用 SQLAlchemy 的默认连接池配置
- 在部署文档中说明调优参数
- 添加数据库监控

### [风险] JWT 密钥管理

**影响:** 密钥泄露导致安全风险

**缓解措施:**
- 使用环境变量存储密钥
- 在生产环境中使用强密钥 (至少 32 字符)
- 定期轮换密钥的计划

### [风险] 错误处理不完善

**影响:** 用户体验差，调试困难

**缓解措施:**
- 定义统一的错误响应格式
- 实现全局异常处理器
- 记录详细的错误日志

### [风险] 数据迁移复杂性

**影响:** 数据库 schema 变更可能导致数据丢失

**缓解措施:**
- 使用 Alembic 管理迁移
- 每个迁移脚本都要可回滚
- 在生产环境变更前备份数据

## Migration Plan

### 阶段 1: 基础结构搭建 (Day 1)
1. 创建项目目录结构
2. 配置依赖包 (requirements.txt)
3. 设置环境变量配置

### 阶段 2: 数据层实现 (Day 2)
1. 定义 SQLAlchemy 模型
2. 创建 Alembic 迁移脚本
3. 编写单元测试

### 阶段 3: 服务层实现 (Day 3)
1. 实现 Agent 服务类
2. 添加业务逻辑验证
3. 编写服务层测试

### 阶段 4: API 层实现 (Day 4)
1. 创建 FastAPI 路由
2. 集成 JWT 认证
3. 实现错误处理
4. 编写 API 测试

### 阶段 5: 测试和优化 (Day 5)
1. 端到端测试
2. 性能测试
3. 代码审查
4. 文档完善

### 回滚策略
- 保留所有 Alembic 迁移的回滚脚本
- API 保持向后兼容
- 使用特性开关控制新功能
- 分阶段部署，快速回滚

## Open Questions

1. **Agent 配置的 JSON Schema**: 是否需要预定义配置的 schema 进行验证？
   - 倾向：初期保持灵活，后期根据需求收敛

2. **软删除 vs 硬删除**: Agent 删除是否应该使用软删除？
   - 倾向：初期使用硬删除，简化实现

3. **批量操作**: 是否需要支持批量创建/更新？
   - 倾向：初期不支持，保持 API 简单

4. **分页策略**: 列表接口使用哪种分页方式？
   - 倾向：使用 offset/limit 分页，简单易用

5. **审计日志**: 是否需要记录 Agent 的操作历史？
   - 倾向：不在本次实现，作为后续增强功能
