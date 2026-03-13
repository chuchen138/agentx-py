# 用户管理 (User Management) 技术设计

## 1. 技术架构

用户管理模块采用标准的领域驱动设计（DDD）分层架构，分为应用层、领域层和基础设施层。

### 1.1 架构层次

#### 应用层（Application Layer）

应用层负责协调领域服务，处理应用级业务逻辑，组装 DTO 数据，对外暴露服务接口。

**核心组件**：
- `UserAppService`：用户信息管理应用服务
- `LoginAppService`：登录注册应用服务
- `SsoAppService`：第三方登录应用服务
- `UserSettingsAppService`：用户设置应用服务

**职责**：
- 接收外部请求（来自接口层）
- 参数校验和转换
- 协调领域服务完成业务逻辑
- 组装返回 DTO
- 应用级异常处理
- 事务控制


#### 领域层（Domain Layer）

领域层是核心业务逻辑的承载层，封装业务规则和领域模型，维护领域模型的完整性。

**核心组件**：
- `UserDomainService`：用户领域服务
- `UserSettingsDomainService`：用户设置领域服务
- `UserEntity`：用户实体
- `UserSettingsEntity`：用户设置实体
- `UserSettingsConfig`：用户设置配置模型
- `FallbackConfig`：降级配置模型
- `UserRepository`：用户仓储
- `UserSettingsRepository`：用户设置仓储

**职责**：
- 封装核心业务逻辑
- 维护领域模型的一致性
- 业务规则验证
- 领域事件的触发和处理


#### 基础设施层（Infrastructure Layer）

基础设施层提供技术能力支持，包括数据持久化、外部服务集成等。

**核心组件**：
- `EmailService`：邮件发送服务
- `VerificationCodeService`：验证码管理服务
- `SsoServiceFactory`：SSO 服务工厂
- `JwtUtils`：JWT 工具类
- `PasswordUtils`：密码加密工具

**职责**：
- 数据持久化
- 外部服务集成
- 技术能力提供
- 配置管理

### 1.2 分层职责清晰划分

| 层级 | 职责 | 不负责 |
|-----|------|--------|
| 应用层 | 流程编排、DTO组装、事务管理 | 核心业务逻辑、数据持久化 |
| 领域层 | 业务逻辑、领域模型、业务规则 | HTTP、数据库等技术细节 |
| 基础设施层 | 技术实现、外部集成 | 业务逻辑 |

## 2. 技术选型

### 2.1 核心技术栈

| 技术组件 | Python 技术选型 | 版本 | 用途说明 |
|---------|----------------|------|----------|
| **Web 框架** | FastAPI | 0.104+ | 高性能异步 Web 框架，支持自动 OpenAPI 文档 |
| **ORM 框架** | SQLAlchemy | 2.0+ | 异步 ORM，支持现代 Python 特性 |
| **数据验证** | Pydantic | 2.0+ | 数据验证和序列化，支持 JSON Schema |
| **认证授权** | PyJWT + python-jose | 2.8+ | JWT Token 生成和验证 |
| **密码加密** | Passlib (bcrypt) | 1.7+ | 密码哈希和验证 |
| **OAuth2** | Authlib | 1.2+ | OAuth 2.0 客户端和服务端支持 |
| **缓存** | Redis (redis-py) | 5.0+ | 分布式缓存和会话存储 |
| **数据库迁移** | Alembic | 1.12+ | 数据库版本管理 |
| **异步任务** | Celery + RabbitMQ | 5.3+ | 异步任务队列（可选） |
| **测试框架** | pytest + pytest-asyncio | 7.4+ | 单元测试和集成测试 |

### 2.2 关键技术说明

**FastAPI 优势**:
- 原生异步支持，性能优异
- 自动生成 OpenAPI/Swagger 文档
- 基于类型注解的自动验证
- 依赖注入系统灵活可扩展

**SQLAlchemy 2.0 新特性**:
- 统一的 Core 和 ORM API
- 完全异步支持
- 改进的类型提示
- 更高效的查询构建

**Pydantic v2 改进**:
- 基于 Rust 的 core，性能提升 5-50 倍
- 更严格的类型验证
- 改进的错误信息
- 支持序列化配置

**安全组件**:
- bcrypt: 自适应哈希函数，抗彩虹表攻击
- PyJWT: 完整的 JWT 实现，支持多种算法
- Authlib: 统一的 OAuth 客户端，支持多提供商


## 3. 核心设计

### 3.1 实体模型设计

#### UserModel（用户 ORM 模型）

用户 ORM 模型是用户信息的核心数据持久化模型，映射到数据库的 users 表。

**关键字段**:
- `id`: UUID 主键，自动生成
- `email`: 唯一邮箱地址，带索引
- `nickname`: 用户昵称
- `password_hash`: bcrypt 加密后的密码
- `phone`: 可选手机号
- `avatar_url`: 头像 URL
- `github_id`: GitHub ID（第三方登录使用）
- `login_platform`: 登录平台标识（normal/github）
- `is_admin`: 是否管理员
- `created_at` / `updated_at`: 自动时间戳

**设计要点**:
- 使用 UUID 作为主键，避免 ID 泄露和枚举攻击
- email 和 github_id 唯一约束，防止重复注册
- 复合索引优化常用查询
- 自动时间戳（created_at, updated_at）
- 类型注解增强代码可读性和 IDE 支持

#### UserSettingsModel（用户设置 ORM 模型）

用户设置 ORM 模型维护用户的个性化配置，映射到 user_settings 表。

**关键字段**:
- `id`: UUID 主键
- `user_id`: 外键关联 users.id，级联删除
- `setting_config`: JSONB 字段，存储灵活配置
- `created_at` / `updated_at`: 自动时间戳

**设计要点**:
- 使用 JSONB 存储复杂配置，支持嵌套结构
- 级联删除：用户删除时自动删除设置
- 一对一关系：每个用户只有一个设置记录

#### Pydantic 数据模型（数据传输对象）

用于 API 数据传输和验证的 Pydantic 模型，分为以下几类：

**UserCreate** - 创建用户请求模型:
- 验证邮箱格式（EmailStr）
- 密码强度要求（最小 8 字符，包含大小写字母和数字）
- 昵称长度限制（2-100 字符）
- 手机号格式验证（可选）

**UserResponse** - 用户响应模型:
- 包含用户基本信息（id, email, nickname 等）
- 排除敏感字段（password_hash）
- 支持从 ORM 模型直接转换

**UserSettingsConfig** - 用户设置配置模型:
- default_model: 默认聊天模型 ID
- default_ocr_model: 默认 OCR 模型 ID  
- default_embedding_model: 默认嵌入模型 ID
- fallback_config: 降级配置（嵌套模型）
- theme: 主题（light/dark）
- language: 语言（zh-CN/en-US）

**FallbackConfig** - 降级配置模型:
- enabled: 是否启用降级
- fallback_chain: 降级模型 ID 列表
- max_retries: 最大重试次数（1-10）

**设计要点**:
- 使用 Field 定义验证规则
- 自定义验证器确保密码强度
- ConfigDict(from_attributes=True) 支持 ORM 模式
- 分离创建、更新、响应模型，精细化控制



### 3.2 认证流程设计

#### 普通登录流程（Python 异步实现）

**流程说明**:

```
┌─────────────┐
│  客户端请求  │
└──────┬──────┘
       │ 1. POST /api/v1/auth/login {email, password}
       ▼
┌─────────────────────────┐
│  LoginAppService.login  │
└──────┬──────────────────┘
       │
       ├─ 2. 检查 IP 限流 (Redis)
       │    └─ 超过 5 次/5 分钟 → 429 Too Many Requests
       │
       ├─ 3. 查找用户 (UserRepository.find_by_email)
       │    └─ 不存在 → 401 Unauthorized
       │
       ├─ 4. 验证密码 (bcrypt.verify)
       │    └─ 失败 → 记录失败尝试 → 401 Unauthorized
       │
       ├─ 5. 检查登录方式是否启用 (AuthSettingDomainService)
       │    └─ 禁用 → 403 Forbidden
       │
       ├─ 6. 生成 JWT Token 对
       │    ├─ Access Token (15 分钟)
       │    └─ Refresh Token (7 天) + Redis 存储
       │
       └─ 7. 异步记录登录日志
            └─ 不阻塞响应
            
返回：{access_token, refresh_token, token_type, expires_in}
```

**关键组件**:
- **LoginAppService**: 应用服务，编排登录流程
- **UserRepository**: 数据访问层，查询用户
- **AuthSettingDomainService**: 领域服务，检查登录开关
- **Redis**: 限流计数器和 Token 存储
- **JWT Utils**: Token 生成和验证工具

**安全措施**:
1. IP 限流：防止暴力破解（5 次/5 分钟）
2. 密码加密：bcrypt 强哈希
3. Token 黑名单：Refresh Token 存储到 Redis，支持撤销
4. 审计日志：所有登录尝试记录详细日志

**性能优化**:
- 异步数据库查询（SQLAlchemy Async）
- Redis 缓存限流计数器
- 异步日志写入，不阻塞主流程
- 响应时间目标：< 200ms (P95)


#### 注册流程

**流程说明**:

```
┌─────────────┐
│  客户端请求  │
└──────┬──────┘
       │ 1. POST /api/v1/auth/register {email, password, code}
       ▼
┌─────────────────────────────┐
│  RegisterAppService.register│
└──────┬──────────────────────┘
       │
       ├─ 2. 检查注册功能是否启用
       │    └─ 禁用 → 403 Forbidden
       │
       ├─ 3. 检查 IP 限流
       │    └─ 超过 5 次/小时 → 429 Too Many Requests
       │
       ├─ 4. 验证邮箱验证码 (VerificationCodeService)
       │    └─ 无效 → 400 Bad Request
       │
       ├─ 5. 检查邮箱是否已存在
       │    └─ 已存在 → 409 Conflict
       │
       ├─ 6. 密码加密 (bcrypt.hash)
       │
       ├─ 7. 创建用户记录
       │    └─ 自动生成随机昵称
       │
       ├─ 8. 创建用户设置记录（默认配置）
       │
       └─ 9. 异步发送欢迎邮件
            
返回：{user_id, email, nickname}
```

**关键组件**:
- **RegisterAppService**: 应用服务，编排注册流程
- **VerificationCodeService**: 验证码服务，验证邮箱验证码
- **UserRepository**: 创建用户记录
- **UserSettingsService**: 创建默认用户设置

**安全措施**:
1. 邮箱验证码：确认邮箱所有权
2. 密码强度验证：最小 8 字符，包含大小写字母和数字
3. IP 限流：防止批量注册（5 次/小时）
4. 邮箱唯一性：数据库 UNIQUE 约束

**边缘案例处理**:
- 并发注册：数据库事务保证原子性
- 验证码过期：5 分钟有效期，超时自动失效
- 昵称重复：使用 UUID 前缀或时间戳生成唯一昵称


#### SSO 登录流程（以 GitHub 为例）

**流程说明**:

```
┌─────────────┐
│  客户端请求  │
└──────┬──────┘
       │ 1. GET /api/v1/auth/github/authorize
       ▼
┌──────────────────────────┐
│  SsoAppService.get_url   │
└──────┬───────────────────┘
       │
       ├─ 2. 生成 OAuth2 授权 URL
       │    └─ 包含 state 参数防 CSRF
       │
       └─ 3. 返回授权 URL
            
客户端跳转到 GitHub 授权页面 → 用户授权 → 回调到系统

       │ 4. GET /api/v1/auth/github/callback?code=xxx&state=yyy
       ▼
┌─────────────────────────────┐
│  SsoAppService.handle_callback│
└──────┬──────────────────────┘
       │
       ├─ 5. 验证 state 参数
       │    └─ 不匹配 → 400 Bad Request
       │
       ├─ 6. 用 code 交换 access_token
       │
       ├─ 7. 获取 GitHub 用户信息
       │    └─ email, login, avatar_url
       │
       ├─ 8. 查找或创建本地用户
       │    ├─ 优先通过 github_id 查找
       │    ├─ 未找到则通过 email 查找
       │    └─ 都未找到则创建新用户
       │
       ├─ 9. 更新用户信息（头像、昵称）
       │
       ├─ 10. 生成 JWT Token 对
       │
       └─ 11. 异步同步到第三方平台
            
返回：{access_token, refresh_token}（重定向到前端）
```

**关键组件**:
- **SsoAppService**: 编排 SSO 流程
- **SsoServiceFactory**: SSO 服务工厂，根据 provider 获取对应服务
- **GitHubSsoProvider**: GitHub OAuth2 实现（可扩展其他提供商）
- **UserRepository**: 查找或创建用户

**扩展性设计**:
- 抽象 SsoProvider 基类，易于添加新提供商（Google、微信等）
- 工厂模式统一管理多个 SSO 提供商
- 配置驱动，支持动态启用/禁用提供商

**边缘案例处理**:
- 邮箱冲突：第三方邮箱已注册时，自动关联现有账户
- 用户拒绝授权：回调时返回 error 参数，重定向到错误页面
- state 过期：设置合理 TTL（10 分钟），超时重新发起授权


#### 密码重置流程

**流程说明**:

```
步骤 1: 发送重置密码验证码

┌─────────────┐
│  客户端请求  │
└──────┬──────┘
       │ 1. POST /api/v1/auth/password/reset/send-code {email, captcha}
       ▼
┌─────────────────────────────────┐
│  PasswordResetAppService.send_code│
└──────┬──────────────────────────┘
       │
       ├─ 2. 检查普通登录是否启用
       │    └─ 禁用 → 403 Forbidden
       │
       ├─ 3. 验证图形验证码
       │    └─ 错误 → 400 Bad Request
       │
       ├─ 4. 查找用户
       │    └─ 不存在 → 404 Not Found（模糊处理）
       │
       ├─ 5. 检查发送频率
       │    └─ 5 分钟内已发送 → 429 Too Many Requests
       │
       ├─ 6. 生成 6 位数字验证码
       │
       ├─ 7. 存储验证码到 Redis（10 分钟有效期）
       │
       └─ 8. 发送重置密码邮件
            
返回：{message: "验证码已发送"}


步骤 2: 验证并重置密码

       │ 1. POST /api/v1/auth/password/reset {email, code, new_password}
       ▼
┌─────────────────────────────────┐
│  PasswordResetAppService.reset  │
└──────┬──────────────────────────┘
       │
       ├─ 2. 验证邮箱验证码
       │    └─ 无效或过期 → 400 Bad Request
       │
       ├─ 3. 验证新密码强度
       │    └─ 不满足要求 → 400 Bad Request
       │
       ├─ 4. 检查密码历史
       │    └─ 最近 3 次用过 → 400 Bad Request
       │
       ├─ 5. 密码加密并更新
       │
       ├─ 6. 使所有 Refresh Token 失效（Redis 删除）
       │
       ├─ 7. 记录密码历史
       │
       ├─ 8. 发送密码修改成功通知邮件
       │
       └─ 9. 记录审计日志
            
返回：{message: "密码重置成功"}
```

**关键组件**:
- **PasswordResetAppService**: 编排密码重置流程
- **VerificationCodeService**: 生成和验证验证码
- **EmailService**: 发送重置密码邮件
- **PasswordHistoryService**: 管理密码历史，防止重复使用

**安全措施**:
1. 双重验证：图形验证码 + 邮箱验证码
2. 发送频率限制：同一邮箱 5 分钟内只能发送一次
3. 密码强度：遵循与注册相同的密码规则
4. Token 失效：重置后使所有已颁发的 Token 立即失效
5. 安全响应：用户不存在时也返回成功，防止枚举

**边缘案例处理**:
- 验证码重试：允许错误 5 次，超过后需要重新发送
- 并发重置：数据库乐观锁防止覆盖
- 邮件发送失败：异步重试机制（最多 3 次）

### 3.5 自定义认证处理器设计

为了支持灵活的认证策略，系统提供自定义认证处理器扩展点。通过实现标准接口，可以定制认证逻辑而不修改核心代码。

#### 抽象接口定义

**AuthenticationHandler（认证处理器基类）**

```python
# app/domain/auth/authentication_handler.py
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any

class AuthenticationHandler(ABC):
    """认证处理器抽象接口"""
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> Optional[UserModel]:
        """
        执行认证
        
        Args:
            credentials: 认证凭据（如邮箱、密码等）
            
        Returns:
            认证成功返回用户模型，失败返回 None
            
        Raises:
            AuthenticationError: 认证失败时抛出
        """
        pass
    
    @abstractmethod
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """
        验证凭据格式
        
        Args:
            credentials: 待验证的凭据
            
        Returns:
            格式有效返回 True，否则 False
        """
        pass
    
    @abstractmethod
    def get_handler_type(self) -> str:
        """获取处理器类型标识"""
        pass
```

**实现示例：普通登录处理器**

```python
class NormalLoginHandler(AuthenticationHandler):
    """普通登录认证处理器"""
    
    def __init__(self, user_repo: UserRepository, settings: Settings):
        self.user_repo = user_repo
        self.settings = settings
    
    async def authenticate(
        self, 
        credentials: Dict[str, Any]
    ) -> Optional[UserModel]:
        email = credentials.get('email')
        password = credentials.get('password')
        
        # 1. 查找用户
        user = await self.user_repo.find_by_email(email)
        if not user:
            return None
        
        # 2. 验证密码
        if not verify_password(password, user.password_hash):
            return None
        
        # 3. 检查账户状态
        if not self._is_account_active(user):
            raise AuthenticationError("账户已被禁用")
        
        return user
    
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """验证邮箱和密码格式"""
        email = credentials.get('email')
        password = credentials.get('password')
        
        if not email or not password:
            return False
        
        # 验证邮箱格式
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return False
        
        # 验证密码长度
        if len(password) < 8:
            return False
        
        return True
    
    def get_handler_type(self) -> str:
        return "normal_login"
```

**实现示例：GitHub SSO 处理器**

```python
class GitHubSsoHandler(AuthenticationHandler):
    """GitHub SSO 认证处理器"""
    
    def __init__(self, sso_service: SsoService, user_repo: UserRepository):
        self.sso_service = sso_service
        self.user_repo = user_repo
    
    async def authenticate(
        self, 
        credentials: Dict[str, Any]
    ) -> Optional[UserModel]:
        auth_code = credentials.get('auth_code')
        state = credentials.get('state')
        
        # 1. 验证 state 参数（防 CSRF）
        if not self._verify_state(state):
            return None
        
        # 2. 用 code 交换 access_token
        token_response = await self.sso_service.exchange_token(auth_code)
        
        # 3. 获取 GitHub 用户信息
        github_user = await self.sso_service.get_user_info(token_response.access_token)
        
        # 4. 查找或创建本地用户
        user = await self._find_or_create_user(github_user)
        
        return user
    
    async def validate_credentials(self, credentials: Dict[str, Any]) -> bool:
        """验证授权码和 state 格式"""
        return bool(credentials.get('auth_code')) and bool(credentials.get('state'))
    
    def get_handler_type(self) -> str:
        return "github_sso"
```

#### 处理器注册与使用

**工厂模式管理处理器**

```python
# app/application/auth/authentication_factory.py
class AuthenticationFactory:
    """认证处理器工厂"""
    
    def __init__(self):
        self._handlers: Dict[str, AuthenticationHandler] = {}
    
    def register(self, handler: AuthenticationHandler):
        """注册处理器"""
        handler_type = handler.get_handler_type()
        self._handlers[handler_type] = handler
    
    def get_handler(self, handler_type: str) -> AuthenticationHandler:
        """获取处理器"""
        handler = self._handlers.get(handler_type)
        if not handler:
            raise ValueError(f"Unsupported handler type: {handler_type}")
        return handler
    
    def list_handlers(self) -> List[str]:
        """列出所有已注册的处理器类型"""
        return list(self._handlers.keys())

# 初始化时注册处理器
factory = AuthenticationFactory()
factory.register(NormalLoginHandler(user_repo, settings))
factory.register(GitHubSsoHandler(sso_service, user_repo))
# 未来可以轻松添加其他提供商
# factory.register(GoogleSsoHandler(...))
# factory.register(WechatSsoHandler(...))
```

**在 API 路由中使用**

```python
# app/api/v1/routes/auth.py
@router.post("/login")
async def login(
    request: LoginRequest,
    factory: AuthenticationFactory = Depends(get_auth_factory),
    token_service: TokenService = Depends(get_token_service)
):
    # 根据登录类型选择处理器
    handler = factory.get_handler(request.login_type)
    
    # 验证凭据格式
    if not await handler.validate_credentials(request.credentials):
        raise HTTPException(400, "Invalid credentials format")
    
    # 执行认证
    user = await handler.authenticate(request.credentials)
    if not user:
        raise HTTPException(401, "Authentication failed")
    
    # 生成 Token
    tokens = await token_service.generate_tokens(user)
    return tokens
```

#### 扩展性说明

**添加新的认证方式只需 3 步**:

1. **实现 AuthenticationHandler 接口**:
   ```python
   class GoogleSsoHandler(AuthenticationHandler):
       async def authenticate(self, credentials): ...
       async def validate_credentials(self, credentials): ...
       def get_handler_type(self): ...
   ```

2. **在工厂中注册**:
   ```python
   factory.register(GoogleSsoHandler(...))
   ```

3. **配置启用**:
   ```python
   AUTH_HANDLERS = ["normal_login", "github_sso", "google_sso"]
   ```

**优势**:
- **开闭原则**: 对扩展开放，对修改封闭
- **单一职责**: 每个处理器只负责一种认证方式
- **可测试性**: 各个处理器独立，易于单元测试
- **动态配置**: 支持运行时启用/禁用特定处理器

## 4. 接口设计

### 4.1 用户管理接口

#### GET /api/v1/users/me - 获取当前用户信息

**请求**:
- 方法：GET
- 认证：Bearer Token（必需）
- 参数：无

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "nickname": "张三",
  "phone": "+8613800138000",
  "avatar_url": "https://example.com/avatar.jpg",
  "login_platform": "normal",
  "is_admin": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**异常**:
- 401 Unauthorized: 未认证或 Token 无效
- 404 Not Found: 用户不存在

---

#### PUT /api/v1/users/me - 更新当前用户信息

**请求**:
- 方法：PUT
- 认证：Bearer Token（必需）
- Body: `UpdateUserRequest`
  ```json
  {
    "nickname": "新昵称",
    "phone": "+8613800138000",
    "avatar_url": "https://example.com/new-avatar.jpg"
  }
  ```

**响应**: 更新后的用户信息

**异常**:
- 400 Bad Request: 数据验证失败
- 409 Conflict: 手机号已被使用

---

#### POST /api/v1/users/me/change-password - 修改密码

**请求**:
- 方法：POST
- 认证：Bearer Token（必需）
- Body: `ChangePasswordRequest`
  ```json
  {
    "current_password": "旧密码",
    "new_password": "新密码",
    "confirm_password": "确认密码"
  }
  ```

**响应**: `{message: "密码修改成功"}`

**异常**:
- 400 Bad Request: 密码强度不足或两次输入不一致
- 401 Unauthorized: 当前密码错误

---

#### GET /api/v1/users/me/settings - 获取用户设置

**请求**:
- 方法：GET
- 认证：Bearer Token（必需）

**响应**:
```json
{
  "id": "...",
  "user_id": "...",
  "setting_config": {
    "default_model": "gpt-4",
    "default_ocr_model": "azure-ocr",
    "fallback_config": {
      "enabled": true,
      "fallback_chain": ["gpt-3.5-turbo", "claude-instant"]
    },
    "theme": "light",
    "language": "zh-CN"
  }
}
```

---

#### PUT /api/v1/users/me/settings - 更新用户设置

**请求**:
- 方法：PUT 或 PATCH
- 认证：Bearer Token（必需）
- Body: `UpdateUserSettingsRequest`（支持部分字段）
  ```json
  {
    "default_model": "claude-3",
    "fallback_config": {
      "enabled": true,
      "fallback_chain": ["gpt-4", "gpt-3.5-turbo"]
    }
  }
  ```

**响应**: 更新后的设置

**异常**:
- 400 Bad Request: 配置验证失败（如降级链循环引用）

### 4.2 认证接口

#### POST /api/v1/auth/login - 用户登录

**请求**:
- 方法：POST
- Body: `LoginRequest`
  ```json
  {
    "email": "user@example.com",
    "password": "SecurePass123!",
    "captcha_code": "ABCD"  // 可选，连续失败后必需
  }
  ```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**异常**:
- 401 Unauthorized: 邮箱或密码错误
- 403 Forbidden: 登录方式已禁用
- 429 Too Many Requests: 登录尝试次数过多

---

#### POST /api/v1/auth/register - 用户注册

**请求**:
- 方法：POST
- Body: `RegisterRequest`
  ```json
  {
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "nickname": "新用户",
    "verification_code": "123456"
  }
  ```

**响应**:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "newuser@example.com",
  "nickname": "新用户"
}
```

**异常**:
- 400 Bad Request: 验证码无效或密码强度不足
- 403 Forbidden: 注册功能已禁用
- 409 Conflict: 邮箱已被注册

---

#### GET /api/v1/auth/github/authorize - GitHub SSO 授权

**请求**:
- 方法：GET
- 参数：redirect_uri（可选）

**响应**:
```json
{
  "authorize_url": "https://github.com/login/oauth/authorize?client_id=xxx&redirect_uri=yyy&state=zzz"
}
```

---

#### GET /api/v1/auth/github/callback - GitHub SSO 回调

**请求**:
- 方法：GET
- 参数：code, state

**响应**: 重定向到前端页面，携带 Token 参数

**异常**:
- 400 Bad Request: state 不匹配或授权失败
- 404 Not Found: 用户不存在且自动创建失败

---

#### POST /api/v1/auth/password/reset/send-code - 发送重置密码验证码

**请求**:
- 方法：POST
- Body: `SendResetCodeRequest`
  ```json
  {
    "email": "user@example.com",
    "captcha_code": "ABCD"
  }
  ```

**响应**: `{message: "验证码已发送"}`

**异常**:
- 400 Bad Request: 图形验证码错误
- 429 Too Many Requests: 发送频率过高

---

#### POST /api/v1/auth/password/reset - 重置密码

**请求**:
- 方法：POST
- Body: `ResetPasswordRequest`
  ```json
  {
    "email": "user@example.com",
    "verification_code": "123456",
    "new_password": "NewSecurePass123!"
  }
  ```

**响应**: `{message: "密码重置成功"}`

**异常**:
- 400 Bad Request: 验证码无效或密码强度不足
- 403 Forbidden: 普通登录已禁用

---

#### POST /api/v1/auth/refresh - 刷新 Token

**请求**:
- 方法：POST
- 认证：Bearer Token（Refresh Token）
- Body: `RefreshTokenRequest`
  ```json
  {
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }
  ```

**响应**: 新的 access_token 和 refresh_token

**异常**:
- 401 Unauthorized: Refresh Token 无效或已过期
- 403 Forbidden: Token 已被撤销


### 4.3 SSO 接口

#### GET /api/v1/auth/sso/{provider}/authorize - 获取 SSO 授权 URL

**请求**:
- 方法：GET
- 路径参数：provider (github/google/wechat)
- 查询参数：redirect_uri（可选）

**响应**:
```json
{
  "authorize_url": "https://accounts.google.com/oauth/authorize?..."
}
```

**异常**:
- 400 Bad Request: 不支持的 SSO 提供商
- 403 Forbidden: 该 SSO 提供商已禁用

---

#### GET /api/v1/auth/sso/{provider}/callback - SSO 回调处理

**请求**:
- 方法：GET
- 路径参数：provider
- 查询参数：code, state

**响应**: 重定向到前端，携带 Token

**异常**:
- 400 Bad Request: 授权码无效或 state 不匹配
- 404 Not Found: 用户不存在且创建失败

### 4.4 用户设置接口

用户设置接口已在 **4.1 用户管理接口** 中定义：
- `GET /api/v1/users/me/settings` - 获取用户设置
- `PUT /api/v1/users/me/settings` - 更新用户设置

**说明**: 用户设置相关接口已集成到用户管理接口中，不再单独列出。

## 5. 集成设计

### 5.1 与 AuthSettingDomainService 集成

用户管理模块依赖 AuthSettingDomainService 进行认证开关控制。

**集成点**:
- 普通登录开关（AuthFeatureKey.NORMAL_LOGIN）
- 用户注册开关（AuthFeatureKey.USER_REGISTER）
- 第三方登录开关（AuthFeatureKey.SSO_LOGIN）

**用途**:
- 灵活控制登录方式的启用/禁用
- 管理员可以根据需要关闭注册功能
- 支持运维层面的认证策略调整

**Python 实现示例**:
```python
# app/application/auth/auth_setting_domain_service.py
class AuthSettingDomainService:
    """认证设置领域服务"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def is_feature_enabled(self, feature_key: str) -> bool:
        """检查特性是否启用"""
        settings = await self._load_settings()
        return settings.get(feature_key, True)
    
    async def _load_settings(self) -> Dict[str, bool]:
        """从 Redis 加载认证设置"""
        settings_json = await self.redis.get("auth:settings")
        return json.loads(settings_json) if settings_json else {}

# 使用示例
if not await auth_settings.is_feature_enabled(AuthFeatureKey.NORMAL_LOGIN):
    raise HTTPException(403, "普通登录已禁用")
```

---

### 5.2 与 EmailService 集成

用户管理模块依赖 EmailService 发送验证邮件。

**集成点**:
- 注册验证码邮件
- 重置密码验证码邮件
- 密码修改成功通知

**用途**:
- 验证用户邮箱所有权
- 完成注册和密码重置流程的安全验证
- 安全事件通知

**Python 实现示例**:
```python
# app/infrastructure/external/email_service.py
class EmailService:
    """邮件发送服务"""
    
    def __init__(self, smtp_config: SMTPConfig):
        self.smtp_config = smtp_config
    
    async def send_verification_code(
        self, 
        email: str, 
        code: str,
        purpose: str  # "registration" or "password_reset"
    ):
        """发送验证码邮件"""
        subject = f"AgentX - {'注册' if purpose == 'registration' else '重置密码'}验证码"
        body = f"您的验证码是：{code}，有效期 5 分钟。"
        
        await self._send_email(email, subject, body)
```

---

### 5.3 与 VerificationCodeService 集成

用户管理模块依赖 VerificationCodeService 管理验证码。

**集成点**:
- 验证码生成（6 位数字）
- 验证码验证
- 验证码过期管理（Redis TTL）
- 业务类型区分（注册、重置密码）

**用途**:
- 防止恶意注册
- 验证用户邮箱所有权
- 防止验证码滥用

**Python 实现示例**:
```python
# app/domain/auth/verification_code_service.py
class VerificationCodeService:
    """验证码管理服务"""
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
    
    async def generate_and_send(
        self, 
        email: str, 
        business_type: str
    ) -> str:
        """生成并发送验证码"""
        code = self._generate_code()
        key = f"verification:{business_type}:{email}"
        
        # 存储到 Redis，5 分钟有效期
        await self.redis.setex(key, timedelta(minutes=5), code)
        
        # 异步发送邮件
        asyncio.create_task(
            email_service.send_verification_code(email, code, business_type)
        )
        
        return code
    
    async def verify(self, email: str, code: str, business_type: str) -> bool:
        """验证验证码"""
        key = f"verification:{business_type}:{email}"
        stored_code = await self.redis.get(key)
        
        if stored_code and stored_code == code:
            # 验证成功后立即删除，防止重用
            await self.redis.delete(key)
            return True
        
        return False
    
    def _generate_code(self) -> str:
        """生成 6 位数字验证码"""
        return ''.join(random.choices('0123456789', k=6))
```

---

### 5.4 与 SsoServiceFactory 集成

用户管理模块依赖 SsoServiceFactory 处理第三方登录。

**集成点**:
- 获取 SSO 登录 URL
- 获取 SSO 用户信息
- 支持多种 SSO 提供商（GitHub、Google 等）

**用途**:
- 提供第三方登录能力
- 统一管理不同 SSO 提供商
- 便于扩展新的 SSO 提供商

**工厂模式实现**:
```python
# app/infrastructure/external/sso/sso_service_factory.py
class SsoServiceFactory:
    """SSO 服务工厂"""
    
    def __init__(self):
        self._providers: Dict[str, BaseSsoProvider] = {}
    
    def register_provider(self, provider: BaseSsoProvider):
        """注册 SSO 提供商"""
        name = provider.get_provider_name()
        self._providers[name] = provider
    
    def get_provider(self, provider_name: str) -> BaseSsoProvider:
        """获取 SSO 提供商服务"""
        provider = self._providers.get(provider_name)
        if not provider:
            raise ValueError(f"Unsupported provider: {provider_name}")
        return provider
    
    def list_providers(self) -> List[str]:
        """列出所有支持的提供商"""
        return list(self._providers.keys())

# 初始化时注册
factory = SsoServiceFactory()
factory.register_provider(GitHubSsoProvider(github_config))
factory.register_provider(GoogleSsoProvider(google_config))
# 未来可以轻松添加更多提供商
```

**使用示例**:
```python
# 在 SsoAppService 中使用
class SsoAppService:
    def __init__(self, sso_factory: SsoServiceFactory):
        self.sso_factory = sso_factory
    
    async def get_authorization_url(
        self, 
        provider_name: str, 
        redirect_uri: str
    ) -> str:
        provider = self.sso_factory.get_provider(provider_name)
        return await provider.get_authorization_url(redirect_uri)
```

## 6. 数据流程图

### 6.1 登录流程图（已在前文描述）

详见 **3.2 认证流程设计 - 普通登录流程**

---

### 6.2 注册流程图（已在前文描述）

详见 **3.2 认证流程设计 - 注册流程**

---

### 6.3 SSO 流程图（已在前文描述）

详见 **3.2 认证流程设计 - SSO 登录流程**

---

### 6.4 密码重置流程图（已在前文描述）

详见 **3.2 认证流程设计 - 密码重置流程**

---

**说明**: 所有流程图已在第 3 章详细描述，此处不再重复。

---

## 7. 附录

### 7.1 错误码定义

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| AUTH_001 | 401 | 邮箱或密码错误 |
| AUTH_002 | 403 | 登录方式已禁用 |
| AUTH_003 | 429 | 登录尝试次数过多 |
| AUTH_004 | 400 | 验证码无效或过期 |
| AUTH_005 | 403 | 注册功能已禁用 |
| AUTH_006 | 409 | 邮箱已被注册 |
| AUTH_007 | 400 | 密码强度不足 |
| AUTH_008 | 401 | 当前密码错误 |
| AUTH_009 | 400 | SSO 授权失败 |
| AUTH_010 | 400 | 不支持的 SSO 提供商 |
| USER_001 | 404 | 用户不存在 |
| USER_002 | 409 | 资源冲突（如手机号重复） |
| USER_003 | 400 | 数据验证失败 |

### 7.2 依赖模块交叉引用

- **文件存储模块**: 头像上传功能依赖 ([spec](../002-file-storage/spec.md))
- **LLM 管理模块**: 默认模型配置依赖 ([spec](../004-llm-management/spec.md))
- **计费模块**: 用户配额和余额检查 ([spec](../019-account-billing/spec.md))
- **Auth 设置模块**: 认证开关配置 ([spec](../003-auth-settings/spec.md))

### 7.3 核心文档引用

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - 整体架构设计
- [开发规范](../../docs/develop_document.md) - Python 开发标准
- [API 设计规范](../../specs/001-user-management/spec.md) - RESTful API 规范

---

*文档版本：2.0 | 最后更新：2026-03-13 | 技术栈：Python/FastAPI*
