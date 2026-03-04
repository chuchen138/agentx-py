# Agent Authentication Capability Specification

本规范定义了 Agent 操作的认证和授权需求。

## ADDED Requirements

### Requirement: JWT Token 认证

系统必须使用 JWT Bearer Token 进行 API 认证。

**验收标准:**
- 所有 Agent 相关 API (除公开查询外) 都需要认证
- 使用 Authorization Header 携带 Token
- Token 格式：`Bearer <token>`
- 过期 Token 自动拒绝

#### Scenario: 认证成功
- **WHEN** 请求携带有效的 JWT Token
- **THEN** 系统允许访问并识别用户身份

#### Scenario: 缺少 Token
- **WHEN** 请求未携带 Authorization Header
- **THEN** 系统返回 401 Unauthorized

#### Scenario: Token 过期
- **WHEN** 请求携带过期的 JWT Token
- **THEN** 系统返回 401 Unauthorized

#### Scenario: Token 无效
- **WHEN** 请求携带伪造或损坏的 Token
- **THEN** 系统返回 401 Unauthorized

### Requirement: 基于所有权的授权

系统必须验证用户只能操作自己创建的 Agent。

**验收标准:**
- 创建 Agent 时记录 user_id
- 查询、更新、删除时验证所有权
- 管理员可以绕过所有权检查 (预留)

#### Scenario: 所有者操作自己的 Agent
- **WHEN** 用户操作自己创建的 Agent
- **THEN** 系统允许操作

#### Scenario: 非所有者尝试操作
- **WHEN** 用户尝试操作其他用户的 Agent
- **THEN** 系统返回 403 Forbidden 或 404 Not Found

#### Scenario: 未登录用户尝试操作
- **WHEN** 未认证用户尝试操作 Agent
- **THEN** 系统返回 401 Unauthorized

### Requirement: 安全的 Token 管理

系统必须安全地管理和存储 JWT Token。

**验收标准:**
- 使用强密钥签名 (至少 32 字符)
- Token 有过期时间
- 支持 Token 刷新机制
- 密钥存储在环境变量中

#### Scenario: Token 生成
- **WHEN** 用户成功登录
- **THEN** 系统生成带有过期时间的 JWT Token

#### Scenario: Token 刷新
- **WHEN** Token 即将过期但 refresh token 有效
- **THEN** 系统颁发新的 access token

#### Scenario: 弱密钥保护
- **WHEN** 配置的 JWT 密钥强度不足
- **THEN** 系统在启动时发出警告
