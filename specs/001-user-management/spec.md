# 用户管理 (User Management) 规范

## 1. 概述

用户管理模块是 AgentX 系统的核心模块之一，负责用户的全生命周期管理，包括用户账户管理、登录认证、用户注册、密码找回以及个性化设置等功能。该模块为系统提供统一的用户身份管理和认证服务，支持多种登录方式和灵活的用户配置。

### 1.1 目标

- 提供安全可靠的用户身份管理服务
- 支持多种登录认证方式（普通登录、第三方登录）
- 灵活的用户个性化配置能力
- 安全的密码管理机制
- 高性能、可扩展的认证架构

### 1.2 范围

用户管理模块涵盖以下功能范围：
- 用户账户的创建、查询、更新和管理
- 用户登录认证与会话管理
- 用户注册与邮箱验证
- 第三方登录（如 GitHub）集成
- 密码找回与重置
- 用户个性化设置（默认模型、降级策略等）
- 双因素认证（2FA）支持（预留扩展）

### 1.3 技术约束

本模块基于以下 Python 技术栈实现：
- **Web 框架**: FastAPI 0.104+
- **ORM 框架**: SQLAlchemy 2.0+
- **数据验证**: Pydantic 2.0+
- **认证**: PyJWT 2.8+
- **密码加密**: Passlib (bcrypt) 1.7+
- **缓存**: Redis (redis-py 5.0+)
- **异步**: asyncio (Python 3.9+)
- **数据库**: PostgreSQL 14+ (含 PGVector)
- **OAuth2**: Authlib 1.2+

**分布式支持**:
- JWT Token 支持多实例共享验证
- Redis 集中存储验证码和会话状态
- 支持水平扩展，通过负载均衡分发请求

### 1.4 依赖模块

- **文件存储模块**: 头像上传功能依赖
- **计费模块**: 用户配额和余额检查
- **AuthSetting 模块**: 认证开关配置
- **邮件服务模块**: 验证码邮件发送

### 1.5 性能指标

- **登录响应时间**: < 200ms (P95)
- **并发支持**: ≥ 1000 并发用户
- **Token 生成延迟**: < 50ms
- **验证码验证延迟**: < 100ms
- **数据库查询延迟**: < 50ms (P95)
- **系统可用性**: ≥ 99.9%

## 2. 核心能力描述

### 2.1 用户账户管理

用户账户管理提供用户信息的基本 CRUD 操作，支持用户资料的维护和管理。

#### 功能特性

- **用户信息查询**：根据用户ID获取完整的用户信息，包括昵称、邮箱、手机号、头像、登录平台等基本信息
- **用户信息更新**：支持更新用户的基本信息，如昵称、手机号、头像URL等
- **密码修改**：用户可以修改自己的密码，需要验证当前密码的正确性
- **用户列表查询**：支持分页查询用户列表，便于管理员进行用户管理
- **用户角色管理**：支持管理员标识（isAdmin），区分普通用户和管理员

#### 数据字段

- `id`：用户唯一标识（UUID）
- `nickname`：用户昵称
- `email`：用户邮箱
- `phone`：用户手机号
- `password`：加密后的密码
- `avatarUrl`：用户头像URL
- `githubId`：GitHub 用户ID（可选）
- `githubLogin`：GitHub 登录名（可选）
- `loginPlatform`：登录平台标识（normal/github）
- `isAdmin`：是否为管理员

### 2.2 登录认证

登录认证模块支持多种登录方式，提供灵活的身份验证机制。

#### 功能特性

- **普通登录**：支持通过邮箱或手机号加密码的方式进行登录认证
- **第三方登录**：集成 GitHub OAuth2 登录，支持通过第三方向用户信息创建或关联本地账户
- **登录方式配置**：通过 AuthSettingDomainService 控制不同登录方式的启用/禁用
- **会话管理**：使用 JWT Token 进行会话管理，登录成功后生成并返回 Token
  - Access Token: 短期有效（默认 15 分钟）
  - Refresh Token: 长期有效（默认 7 天），用于刷新 Access Token
- **账户关联**：第三方登录时支持通过邮箱或平台特定 ID 查找已有账户，实现账户关联
- **限流保护**：基于 IP 的登录限流机制，防止暴力破解
  - 每 IP 5 分钟内最多 5 次登录尝试
  - 超过限制后触发冷却时间

#### 安全要求

- **密码强度**: 
  - 最小长度：8 字符
  - 必须包含：大小写字母、数字、特殊字符
  - 密码历史检查：不能使用最近 3 次用过的密码
- **验证码机制**:
  - 图形验证码：连续失败 3 次后强制要求
  - 邮箱验证码：注册和密码重置时使用
  - 防刷机制：每 IP 5 分钟限 3 次
- **JWT 安全**:
  - 使用 HS256 或 RS256 算法
  - Token 包含用户 ID、过期时间、签发者信息
  - 支持 Token 黑名单机制（用于登出）
- **会话安全**:
  - Refresh Token 一次性使用，刷新后作废旧 Token
  - 支持多设备登录，每个设备独立 Token
  - 异常登录检测（异地、新设备）

#### 认证流程

1. **普通登录流程**:
   ```python
   # 伪代码示例 - Python/FastAPI 风格
   async def login(email: str, password: str, ip: str):
       # 1. 检查登录限流
       if await rate_limiter.is_exceeded(ip):
           raise RateLimitError()
       
       # 2. 查找用户
       user = await user_repo.find_by_email(email)
       if not user:
           raise InvalidCredentialsError()
       
       # 3. 验证密码 (使用 bcrypt)
       if not verify_password(password, user.password_hash):
           await login_attempt_tracker.record_failure(ip)
           raise InvalidCredentialsError()
       
       # 4. 检查登录方式是否启用
       if not auth_settings.is_normal_login_enabled():
           raise LoginMethodDisabledError()
       
       # 5. 生成 JWT Token (使用 PyJWT)
       tokens = await jwt_service.generate_tokens(user)
       
       # 6. 记录登录日志
       await audit_logger.log_login(user.id, ip, "SUCCESS")
       
       return tokens
   ```

2. **第三方登录流程**:
   ```python
   # 伪代码示例 - OAuth2 + Authlib
   async def handle_sso_callback(provider: str, auth_code: str):
       # 1. 通过授权码获取 access_token
       sso_service = SsoServiceFactory.get_provider(provider)
       token_response = await sso_service.exchange_token(auth_code)
       
       # 2. 获取用户信息
       sso_user_info = await sso_service.get_user_info(token_response.access_token)
       
       # 3. 查找或创建本地用户
       user = await find_or_create_user(sso_user_info)
       
       # 4. 更新用户信息（头像、昵称等）
       await update_user_profile(user, sso_user_info)
       
       # 5. 生成 JWT Token
       tokens = await jwt_service.generate_tokens(user)
       
       return tokens
   ```

### 2.3 用户注册

用户注册模块支持新用户通过邮箱或手机号创建账户。

#### 功能特性

- **邮箱注册**：用户可以通过邮箱注册账户，需要提供验证码进行验证
- **手机号注册**：预留手机号注册功能（未来扩展）
- **验证码验证**：注册时需要验证邮箱验证码的有效性
- **注册开关控制**：通过 AuthSettingDomainService 控制用户注册功能的启用/禁用
- **密码加密存储**：用户密码使用 bcrypt 加密后存储（cost factor=10）
- **初始昵称生成**：注册时自动生成随机昵称
- **自动创建账户设置**：注册时自动创建默认用户设置记录
- **邮箱唯一性校验**：确保邮箱地址不重复

#### 安全要求

- **验证码安全**:
  - 验证码有效期：5 分钟
  - 验证码长度：6 位数字
  - 发送频率限制：同一邮箱 60 秒内只能发送一次
  - 验证失败限制：连续错误 5 次后验证码失效
- **密码强度验证**:
  - 最小长度 8 字符
  - 包含大小写字母、数字、特殊字符
  - 密码复杂度评分 ≥ 3/4
- **防刷机制**:
  - 基于 IP 的注册限制：每 IP 每小时最多 5 次注册
  - 图形验证码：检测到异常流量时强制要求

#### 注册流程

```python
# 伪代码示例 - 完整注册流程
async def register(email: str, password: str, code: str, ip: str):
    # 1. 检查注册功能是否启用
    if not auth_settings.is_registration_enabled():
        raise RegistrationDisabledError()
    
    # 2. 检查 IP 限流
    if await rate_limiter.is_registration_exceeded(ip):
        raise RateLimitError()
    
    # 3. 验证邮箱验证码
    if not await verification_service.verify_email_code(email, code):
        raise InvalidVerificationCodeError()
    
    # 4. 检查邮箱是否已存在
    existing_user = await user_repo.find_by_email(email)
    if existing_user:
        raise EmailAlreadyExistsError()
    
    # 5. 密码加密（使用 bcrypt）
    password_hash = get_password_hash(password)
    
    # 6. 创建用户记录
    user = User(
        email=email,
        password_hash=password_hash,
        nickname=generate_random_nickname(),
        login_platform="normal"
    )
    await user_repo.create(user)
    
    # 7. 自动创建用户设置
    await user_settings_service.create_default_settings(user.id)
    
    # 8. 记录注册日志
    await audit_logger.log_registration(user.id, ip)
    
    return user
```

### 2.4 密码找回

密码找回模块为忘记密码的用户提供安全的密码重置功能。

#### 功能特性

- **邮箱验证**：通过邮箱验证码确认用户身份
- **安全验证**：需要验证图形验证码和邮箱验证码（双重验证）
- **密码重置**：验证通过后可以设置新密码
- **登录方式检查**：仅在普通登录启用时才允许密码重置
- **Token 失效**：密码重置后，使所有已颁发的 Refresh Token 失效
- **通知机制**：密码修改成功后发送邮件通知

#### 安全要求

- **验证码安全**:
  - 重置密码验证码有效期：10 分钟
  - 验证码使用后立即失效
  - 发送频率限制：同一邮箱 5 分钟内只能发送一次
- **密码强度**:
  - 遵循与注册相同的密码强度要求
  - 不能与最近 3 次用过的密码相同
- **防暴力破解**:
  - 基于 IP 的请求限制：每 IP 每小时最多 3 次重置请求
  - 连续失败 5 次后锁定 30 分钟

#### 密码重置流程

```python
# 伪代码示例 - 密码重置流程
async def reset_password(email: str, new_password: str, code: str, ip: str):
    # 1. 检查普通登录是否启用
    if not auth_settings.is_normal_login_enabled():
        raise LoginMethodDisabledError()
    
    # 2. 查找用户
    user = await user_repo.find_by_email(email)
    if not user:
        raise UserNotFoundError()
    
    # 3. 验证邮箱验证码
    if not await verification_service.verify_reset_code(email, code):
        raise InvalidVerificationCodeError()
    
    # 4. 验证新密码强度
    if not validate_password_strength(new_password):
        raise PasswordTooWeakError()
    
    # 5. 检查密码历史
    if await password_history_service.is_recent_password(user.id, new_password):
        raise PasswordReuseNotAllowedError()
    
    # 6. 更新密码（bcrypt 加密）
    new_password_hash = get_password_hash(new_password)
    user.password_hash = new_password_hash
    await user_repo.update(user)
    
    # 7. 记录密码历史
    await password_history_service.record_password(user.id, new_password_hash)
    
    # 8. 使所有 Refresh Token 失效
    await jwt_service.revoke_all_refresh_tokens(user.id)
    
    # 9. 发送通知邮件
    await email_service.send_password_change_notification(user.email)
    
    # 10. 记录审计日志
    await audit_logger.log_password_reset(user.id, ip)
```

### 2.5 用户设置

用户设置模块支持用户个性化的配置管理，包括默认模型选择、降级策略等。

#### 功能特性

- **默认模型设置**：用户可以设置默认的聊天模型、OCR 模型、嵌入模型
- **降级链配置**：支持配置模型降级策略，当主模型不可用时自动降级到备用模型
- **设置持久化**：用户设置持久化存储（PostgreSQL JSONB），保持用户个性化配置
- **灵活配置管理**：使用 JSON 格式存储复杂配置，便于扩展
- **版本控制**：设置变更历史记录，支持回滚到历史版本
- **批量更新**：支持部分字段更新和全量更新

#### 设置内容

```python
# Pydantic 模型示例
from pydantic import BaseModel, Field
from typing import List, Optional

class FallbackConfig(BaseModel):
    """降级配置模型"""
    enabled: bool = Field(default=False, description="是否启用降级")
    fallback_chain: List[str] = Field(
        default_factory=list,
        description="降级模型 ID 列表（按优先级排序）"
    )
    max_retries: int = Field(default=3, description="最大重试次数")

class UserSettingsConfig(BaseModel):
    """用户设置配置模型"""
    default_model: Optional[str] = Field(None, description="默认聊天模型 ID")
    default_ocr_model: Optional[str] = Field(None, description="默认 OCR 模型 ID")
    default_embedding_model: Optional[str] = Field(None, description="默认嵌入模型 ID")
    fallback_config: Optional[FallbackConfig] = Field(None, description="降级配置")
    theme: str = Field(default="light", description="界面主题")
    language: str = Field(default="zh-CN", description="语言设置")
    
    class Config:
        json_schema_extra = {
            "example": {
                "default_model": "gpt-4",
                "default_ocr_model": "azure-ocr",
                "fallback_config": {
                    "enabled": True,
                    "fallback_chain": ["gpt-3.5-turbo", "claude-instant"]
                }
            }
        }
```

#### 边缘案例处理

- **模型不存在**: 如果设置的模型 ID 无效，自动回退到系统默认模型
- **降级链循环**: 检测并防止降级链中的循环引用
- **并发更新**: 使用乐观锁（version 字段）处理并发更新冲突
- **配置迁移**: 当系统升级时，自动迁移旧版配置到新格式

#### API 设计原则

- **RESTful 风格**: 遵循 RESTful API 设计规范
- **幂等性**: 更新操作保证幂等性
- **部分更新**: 支持 PATCH 方法进行部分字段更新
- **数据验证**: 使用 Pydantic 进行严格的请求/响应数据验证

## 3. 使用场景

### 3.1 首次用户注册场景

**场景描述**：新用户首次访问系统，需要创建账户。

**操作流程**：
1. 用户点击注册按钮
2. 选择邮箱注册方式
3. 输入邮箱地址和密码
4. 点击发送验证码
5. 查收邮件，输入验证码
6. 提交注册信息
7. 系统创建账户并自动登录

**关键功能**：用户注册、验证码验证、密码加密存储

### 3.2 已有用户登录场景

**场景描述**：已有账户用户通过邮箱密码或第三方登录访问系统。

**操作流程（普通登录）**：
1. 用户输入邮箱和密码
2. 点击登录按钮
3. 系统验证账号密码
4. 生成 JWT Token
5. 返回 Token，用户进入系统

**操作流程（GitHub SSO）**：
1. 用户点击 GitHub 登录
2. 跳转到 GitHub 授权页面
3. 用户授权
4. GitHub 回调至系统
5. 系统获取用户信息
6. 创建或查找账户
7. 生成 JWT Token
8. 返回 Token，用户进入系统

**关键功能**：登录认证、第三方登录、会话管理

### 3.3 用户个人资料维护场景

**场景描述**：用户需要更新个人信息或修改密码。

**操作流程**：
1. 用户进入个人中心
2. 查看个人基本信息
3. 修改昵称、手机号或上传新头像
4. 保存更新

**操作流程（修改密码）**：
1. 用户进入安全设置
2. 输入当前密码、新密码、确认密码
3. 提交修改
4. 系统验证当前密码
5. 更新密码并加密存储

**关键功能**：用户信息更新、密码修改

### 3.4 用户配置偏好设置场景

**场景描述**：用户需要设置默认模型或配置降级策略。

**操作流程**：
1. 用户进入设置页面
2. 选择默认的聊天模型
3. 配置 OCR 和嵌入模型
4. 启用模型降级并配置降级链
5. 保存设置

**关键功能**：用户设置管理、默认模型配置、降级链配置

### 3.5 密码找回场景

**场景描述**：用户忘记密码，需要重置密码。

**操作流程**：
1. 用户在登录页点击"忘记密码"
2. 输入注册邮箱
3. 输入图形验证码
4. 点击发送验证码
5. 查收邮件获取验证码
6. 输入验证码和新密码
7. 提交重置
8. 使用新密码登录

**关键功能**：密码重置、邮箱验证码验证

## 4. 功能特性

### 4.1 多租户支持

系统支持多租户架构，每个用户拥有独立的账户和设置，数据隔离安全可靠。

**隔离机制**:
- 数据库级别：通过 user_id 字段进行逻辑隔离
- 缓存级别：Redis key 包含 user_id 前缀
- 容器级别：每个用户独立的 MCP 网关容器（参考 [容器管理模块](../006-container-management/spec.md)）

### 4.2 认证方式可配置

通过 AuthSettingDomainService 可以灵活控制不同登录方式的启用/禁用状态，包括：
- 普通登录开关
- 用户注册开关
- 第三方登录开关

**动态配置**:
- 支持运行时动态调整，无需重启服务
- 配置变更自动广播到所有实例
- 审计日志记录所有配置变更

### 4.3 第三方登录集成

无缝集成 GitHub OAuth2 登录，支持：
- 自动创建账户
- 账户关联
- 同步用户信息（昵称、头像等）
- 安全的授权流程（OAuth 2.0 PKCE）

**扩展性**:
```python
# SSO Provider 抽象基类 - 易于扩展新的提供商
from abc import ABC, abstractmethod

class SsoProvider(ABC):
    """SSO 提供者抽象接口"""
    
    @abstractmethod
    async def get_authorization_url(self, redirect_uri: str) -> str:
        """获取授权 URL"""
        pass
    
    @abstractmethod
    async def exchange_token(self, auth_code: str) -> TokenResponse:
        """用授权码交换访问令牌"""
        pass
    
    @abstractmethod
    async def get_user_info(self, access_token: str) -> SsoUserInfo:
        """获取用户信息"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供者名称"""
        pass

# 实现示例：GitHub Provider
class GitHubSsoProvider(SsoProvider):
    async def get_authorization_url(self, redirect_uri: str) -> str:
        # GitHub OAuth2 实现
        ...
```

### 4.4 密码安全性

采用业界标准的密码安全措施：
- **Bcrypt 加密算法**: 
  - cost factor = 10（可配置）
  - 自动加盐，防止彩虹表攻击
  - 自适应哈希算法
- **密码强度验证**:
  - 最小长度 8 字符
  - 复杂度要求（大小写 + 数字 + 特殊字符）
  - 密码历史检查（最近 3 次）
- **修改密码需要验证旧密码**: 防止未授权访问
- **重置密码需要邮箱验证码**: 双重验证确保安全
- **密码传输加密**: HTTPS + 前端加密（可选）

### 4.5 用户个性化设置

提供丰富的个性化配置选项：
- 多类型模型默认设置（聊天、OCR、嵌入）
- 灵活的模型降级策略
- JSON 格式配置存储，易于扩展
- 设置持久化，保持用户偏好
- 配置版本控制和回滚

### 4.6 可扩展性

模块设计具有良好的可扩展性：
- **插件式 SSO 提供者**: 支持添加新的第三方登录提供商（Google、微信等）
- **用户设置灵活扩展**: JSON 结构便于添加新配置项
- **认证流程可定制**: 通过依赖注入自定义认证逻辑
- **登录方式可动态配置**: 运行时调整认证策略
- **事件驱动架构**: 基于领域事件的解耦设计（参考 [ARCHITECTURE.md](../../ARCHITECTURE.md)）

**扩展点**:
- 用户注册后的钩子函数
- 登录成功的回调处理
- 密码修改的审计日志
- 自定义 JWT claims

### 4.7 安全性保障

全面的安全机制：
- **验证码防刷机制**: 
  - IP 限流（每 IP 5 分钟 3 次）
  - 时间窗口限制
  - 图形验证码备用方案
- **账号唯一性校验**: 
  - 邮箱唯一性约束（数据库 UNIQUE 索引）
  - 并发注册冲突检测
- **密码加密存储**: bcrypt 强哈希
- **JWT Token 会话管理**: 
  - Access Token + Refresh Token 双令牌
  - Token 过期时间控制
  - Token 黑名单支持
- **SQL 注入防护**: SQLAlchemy ORM 参数化查询
- **XSS 防护**: 输入验证和输出转义
- **CSRF 防护**: CSRF Token 验证
- **审计日志**: 所有敏感操作记录详细日志

### 4.8 性能优化

**缓存策略**:
- 用户信息 Redis 缓存（TTL=5 分钟）
- JWT 公钥/私钥内存缓存
- 验证码 Redis 集中存储

**数据库优化**:
- 邮箱、手机号字段建立唯一索引
- 复合索引优化常用查询组合
- 分页查询限制最大页数

**异步处理**:
- 邮件发送异步化（Celery/RabbitMQ）
- 审计日志异步写入
- 批量操作使用连接池

**量化指标**:
- 登录响应 P95 < 200ms
- 支持 1000+ 并发用户
- 数据库查询 P95 < 50ms
- Redis 缓存命中率 > 90%

### 4.9 监控与告警

**关键指标监控**:
- 登录成功率/失败率
- 注册转化率
- Token 生成/验证延迟
- 验证码发送量/通过率
- 活跃用户数（DAU/MAU）

**告警规则**:
- 登录失败率突增（> 20%）
- 验证码发送异常（> 1000 次/小时）
- 数据库连接池耗尽
- Redis 不可用

**审计追踪**:
- 所有登录尝试记录 IP 和时间
- 密码修改操作详细日志
- 敏感数据访问审计
- 登录状态验证

## 5. 实施指南

### 5.1 依赖管理

**Python 依赖包** (`requirements.txt`):
```txt
# Web 框架
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# 数据库
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1

# 认证和安全
pyjwt==2.8.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
authlib==1.2.1

# 数据验证
pydantic==2.5.0
pydantic-settings==2.1.0
email-validator==2.1.0

# 工具库
httpx==0.25.2  # 异步 HTTP 客户端
celery==5.3.4  # 异步任务队列
```

**系统依赖**:
- Python 3.9+
- PostgreSQL 14+ (含 PGVector 插件)
- Redis 7.0+
- RabbitMQ 3.10+ (可选，用于异步任务)

### 5.2 环境变量配置

`.env` 文件示例:
```bash
# JWT 配置
JWT_SECRET_KEY=your-super-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/agentx
REDIS_URL=redis://localhost:6379/0

# 安全配置
BCRYPT_COST_FACTOR=10
PASSWORD_MIN_LENGTH=8
PASSWORD_REQUIRE_SPECIAL_CHAR=true

# 限流配置
RATE_LIMIT_WINDOW_SECONDS=300
RATE_LIMIT_MAX_ATTEMPTS=5

# SSO 配置（GitHub 示例）
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GITHUB_REDIRECT_URI=http://localhost:8088/api/v1/auth/github/callback

# 邮件服务配置
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@agentx.ai

# 管理员配置
AGENTX_ADMIN_PASSWORD=admin123
```

### 5.3 项目结构

```
app/
├── api/
│   ├── v1/
│   │   ├── routes/
│   │   │   ├── auth.py          # 认证相关路由
│   │   │   └── users.py         # 用户管理路由
│   │   └── dependencies.py      # FastAPI 依赖注入
│   └── middleware/
│       └── auth.py              # JWT 认证中间件
├── domain/
│   ├── user/
│   │   ├── model.py             # User 实体和 Pydantic 模型
│   │   ├── repository.py        # 用户仓储接口
│   │   └── service.py           # 用户领域服务
│   └── auth/
│       ├── jwt_service.py       # JWT 服务
│       ├── password_service.py  # 密码加密服务
│       └── sso_service.py       # SSO 服务
├── application/
│   ├── user/
│   │   ├── user_app_service.py  # 用户应用服务
│   │   └── dtos.py              # DTO 定义
│   └── auth/
│       ├── login_app_service.py     # 登录应用服务
│       ├── register_app_service.py  # 注册应用服务
│       └── sso_app_service.py       # SSO 应用服务
├── infrastructure/
│   ├── persistence/
│   │   ├── models.py            # SQLAlchemy ORM 模型
│   │   └── repositories.py      # 仓储实现
│   ├── cache/
│   │   └── redis_client.py      # Redis 客户端
│   └── external/
│       ├── email_service.py     # 邮件服务
│       └── sms_service.py       # 短信服务（预留）
└── core/
    ├── config.py                # 配置管理
    ├── security.py              # 安全工具函数
    └── exceptions.py            # 自定义异常
```

### 5.4 数据库迁移

使用 Alembic 管理数据库迁移:

```bash
# 初始化 Alembic
alembic init alembic

# 创建新迁移
alembic revision --m "create users table"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

**users 表迁移示例** (`alembic/versions/001_create_users.py`):
```python
"""create users table

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None

def upgrade():
    op.create_table('users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('nickname', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('github_id', sa.String(length=100), nullable=True),
        sa.Column('github_login', sa.String(length=100), nullable=True),
        sa.Column('login_platform', sa.String(length=20), nullable=False),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('github_id')
    )
    
    # 创建索引加速查询
    op.create_index('ix_users_email', 'users', ['email'])
    op.create_index('ix_users_created_at', 'users', ['created_at'])

def downgrade():
    op.drop_index('ix_users_created_at')
    op.drop_index('ix_users_email')
    op.drop_table('users')
```

### 5.5 测试策略

**单元测试** (pytest):
```python
# tests/unit/test_user_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.domain.user.service import UserDomainService

@pytest.fixture
def mock_user_repo():
    return AsyncMock()

@pytest.fixture
def user_service(mock_user_repo):
    return UserDomainService(mock_user_repo)

@pytest.mark.asyncio
async def test_register_user_success(user_service, mock_user_repo):
    # Arrange
    mock_user_repo.find_by_email.return_value = None
    
    # Act
    user = await user_service.register(
        email="test@example.com",
        password="SecurePass123!",
        nickname="TestUser"
    )
    
    # Assert
    assert user.email == "test@example.com"
    assert user.nickname == "TestUser"
    mock_user_repo.create.assert_called_once()

@pytest.mark.asyncio
async def test_register_user_duplicate_email(user_service, mock_user_repo):
    # Arrange
    existing_user = MagicMock(email="test@example.com")
    mock_user_repo.find_by_email.return_value = existing_user
    
    # Act & Assert
    with pytest.raises(EmailAlreadyExistsError):
        await user_service.register(
            email="test@example.com",
            password="SecurePass123!",
            nickname="TestUser"
        )
```

**集成测试**:
```python
# tests/integration/test_auth_api.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
```

**测试覆盖率目标**:
- 领域服务层：≥ 90%
- 应用服务层：≥ 85%
- API 路由层：≥ 80%
- 总体覆盖率：≥ 85%

### 5.6 最佳实践

**代码规范**:
- 遵循 PEP 8 编码规范
- 使用 type hints 进行类型注解
- 函数和类必须有文档字符串
- 异常处理要明确，避免裸 try-except

**安全实践**:
- 所有密码必须 bcrypt 加密
- 敏感操作必须记录审计日志
- API 端点必须进行身份验证
- 输入数据必须验证（Pydantic）
- SQL 查询必须使用 ORM（禁止字符串拼接）

**性能优化**:
- 使用异步 IO 提高并发能力
- 热点数据使用 Redis 缓存
- 数据库查询添加合适索引
- 批量操作使用连接池
- 避免 N+1 查询问题

**错误处理**:
```python
from fastapi import HTTPException, status
from app.core.exceptions import BusinessException

async def get_user_or_404(user_id: str) -> User:
    """获取用户，不存在则抛出 404"""
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )
    return user

async def handle_registration(email: str, password: str):
    """注册错误处理示例"""
    try:
        return await user_service.register(email, password)
    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessException as e:
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )
```

### 5.7 部署建议

**Docker 部署**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8088"]
```

**Docker Compose**:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8088:8088"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/agentx
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=agentx
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine
    volumes:
      - redis-data:/data

volumes:
  pgdata:
  redis-data:
```

### 5.8 交叉引用

本文档引用的其他模块:
- [容器管理模块](../006-container-management/spec.md) - 用户容器隔离
- [LLM 管理模块](../004-llm-management/spec.md) - 默认模型配置
- [计费模块](../019-account-billing/spec.md) - 用户配额管理
- [Auth 设置模块](../003-auth-settings/spec.md) - 认证开关配置

被本文档引用的核心文档:
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - 整体架构设计
- [开发规范](../../docs/develop_document.md) - 开发标准

---

*文档版本：2.0 | 最后更新：2026 年 3 月 | 技术栈：Python/FastAPI*