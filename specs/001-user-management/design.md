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

### 2.2 关键技术说明


## 3. 核心设计

### 3.1 实体模型设计

#### UserEntity（用户实体）

用户实体是用户信息的核心领域模型，包含用户的基本信息和登录相关信息。

**设计要点**：
- 密码字段存储 BCrypt 加密后的哈希值
- `loginPlatform` 标识用户的登录方式（normal/github）
- `githubId` 和 `githubLogin` 支持 GitHub SSO 登录
- `isAdmin` 标识管理员角色

#### UserSettingsEntity（用户设置实体）

用户设置实体维护用户的个性化配置。

**设计要点**：
- 使用 JSON 字段存储复杂配置
- 支持默认模型、降级链等多种配置
- 配置灵活可扩展

#### UserSettingsConfig（用户设置配置）

配置类使用 JSON 序列化，存储在数据库的 JSON 字段中。

**设计要点**：
- `enabled` 控制是否启用降级
- `fallbackChain` 存储降级模型ID列表（按优先级排序）
- 支持动态添加和删除降级模型

#### SsoUserInfo（SSO 用户信息）

SSO 用户信息抽象，支持多种第三方登录提供商。



### 3.2 认证流程设计

#### 普通登录流程

```
用户请求
  ↓
检查普通登录是否启用（AuthSettingDomainService）
  ↓
通过邮箱或手机号查找用户
  ↓
验证密码（BCrypt匹配）
  ↓
生成 JWT Token
  ↓
返回 Token
```


#### 注册流程

```
用户请求注册
  ↓
检查用户注册是否启用（AuthSettingDomainService）
  ↓
邮箱注册：检查是否提供验证码
  ↓
验证邮箱验证码有效性（VerificationCodeService）
  ↓
检查账号是否已存在
  ↓
创建用户记录（密码BCrypt加密）
  ↓
生成初始昵称
  ↓
创建用户设置记录
```


#### SSO 登录流程

```
请求 SSO 登录 URL
  ↓
跳转到授权页面
  ↓
用户授权，回调至系统
  ↓
使用授权码获取用户信息
  ↓
查找或创建本地用户
  │
  ├─ 通过 GitHub ID 查找
  ├─ 通过邮箱查找
  └─ 创建新用户
  ↓
更新用户信息（头像、昵称）
  ↓
生成 JWT Token
  ↓
返回 Token
```


#### 密码重置流程

```
用户请求重置密码
  ↓
检查普通登录是否启用
  ↓
验证邮箱是否已注册
  ↓
发送重置密码验证码到邮箱
  ↓
用户输入验证码和新密码
  ↓
验证验证码有效性
  ↓
更新用户密码（BCrypt加密）
```

### 3.3 设置存储设计

用户设置采用 JSON 字段存储复杂配置，提供灵活的配置管理能力。

**存储结构**：

```
user_settings 表
├── id
├── user_id
└── setting_config (JSON)
    ├── defaultModel
    ├── defaultOcrModel
    ├── defaultEmbeddingModel
    └── fallbackConfig
        ├── enabled
        └── fallbackChain
            ├── model_id_1
            ├── model_id_2
            └── model_id_3
```

**优势**：
- 配置结构灵活，易于扩展
- 支持复杂的嵌套配置
- 避免频繁修改表结构
- 便于配置版本管理

### 3.4 密码安全设计

#### 密码加密存储

使用 BCrypt 加密算法存储用户密码：

**关键特性**：
- 每次加密产生不同的盐值
- 包含成本因子控制计算强度
- 抗彩虹表攻击
- 自适应哈希算法

#### 密码修改安全机制

修改密码需要验证当前密码，防止未授权访问：

#### 密码重置安全机制

密码重置需要邮箱验证码验证，确保只有邮箱所有者才能重置密码：

## 4. 接口设计

### 4.1 用户管理接口

#### getUserInfo

获取用户信息。

```
方法签名：UserDTO getUserInfo(String id)
参数：
  - id：用户ID
返回：
  - UserDTO：用户信息 DTO
异常：
  - 用户不存在异常
```

#### updateUserInfo

更新用户信息。

```
方法签名：void updateUserInfo(UserUpdateRequest request, String userId)
参数：
  - request：用户更新请求
  - userId：用户ID
返回：无
异常：
  - 业务异常（如数据验证失败）
```

#### changePassword

修改用户密码。

```
方法签名：void changePassword(ChangePasswordRequest request, String userId)
参数：
  - request：修改密码请求（包含当前密码、新密码、确认密码）
  - userId：用户ID
返回：无
异常：
  - 当前密码错误异常
  - 两次密码不一致异常
```

#### getUsers

分页获取用户列表。

```
方法签名：Page<UserDTO> getUsers(QueryUserRequest request)
参数：
  - request：查询请求（包含分页参数和查询条件）
返回：
  - Page<UserDTO>：用户分页数据
异常：无
```

### 4.2 认证接口

#### login

用户登录。

```
方法签名：String login(LoginRequest request)
参数：
  - request：登录请求（包含账号和密码）
返回：
  - String：JWT Token
异常：
  - 登录方式禁用异常
  - 账号或密码错误异常
```

#### register

用户注册。

```
方法签名：void register(RegisterRequest request)
参数：
  - request：注册请求（包含邮箱/手机号、密码、验证码）
返回：无
异常：
  - 注册禁用异常
  - 验证码无效异常
  - 账号已存在异常
```

#### sendEmailVerificationCode

发送注册邮箱验证码。

```
方法签名：void sendEmailVerificationCode(String email, String captchaUuid, 
                                         String captchaCode, String ip)
参数：
  - email：邮箱地址
  - captchaUuid：图形验证码 UUID
  - captchaCode：图形验证码
  - ip：客户端 IP
返回：无
异常：
  - 注册禁用异常
  - 邮箱已存在异常
```

#### sendResetPasswordCode

发送重置密码邮箱验证码。

```
方法签名：void sendResetPasswordCode(String email, String captchaUuid, 
                                     String captchaCode, String ip)
参数：
  - email：邮箱地址
  - captchaUuid：图形验证码 UUID
  - captchaCode：图形验证码
  - ip：客户端 IP
返回：无
异常：
  - 登录方式禁用异常
  - 邮箱未注册异常
```



#### verifyEmailCode

验证邮箱验证码（注册）。

```
方法签名：boolean verifyEmailCode(String email, String code)
参数：
  - email：邮箱地址
  - code：验证码
返回：
  - boolean：验证码是否有效
异常：无
```

#### verifyResetPasswordCode

验证重置密码邮箱验证码。

```
方法签名：boolean verifyResetPasswordCode(String email, String code)
参数：
  - email：邮箱地址
  - code：验证码
返回：
  - boolean：验证码是否有效
异常：无
```

#### resetPassword

重置密码。

```
方法签名：void resetPassword(String email, String newPassword, String code)
参数：
  - email：邮箱地址
  - newPassword：新密码
  - code：验证码
返回：无
异常：
  - 登录方式禁用异常
  - 验证码无效异常
  - 用户不存在异常
```


### 4.3 SSO 接口

#### getSsoLoginUrl

获取 SSO 登录 URL。

```
方法签名：String getSsoLoginUrl(String provider, String redirectUrl)
参数：
  - provider：SSO 提供商（如 github）
  - redirectUrl：回调 URL
返回：
  - String：SSO 登录 URL
异常：
  - 不支持的 SSO 提供商异常
```

#### handleSsoCallback

处理 SSO 回调。

```
方法签名：String handleSsoCallback(String provider, String authCode)
参数：
  - provider：SSO 提供商
  - authCode：授权码
返回：
  - String：JWT Token
异常：
  - SSO 授权异常
  - 用户信息获取异常
```

### 4.4 用户设置接口

#### getUserSettings

获取用户设置。

```
方法签名：UserSettingsDTO getUserSettings(String userId)
参数：
  - userId：用户ID
返回：
  - UserSettingsDTO：用户设置 DTO
异常：无
```

#### updateUserSettings

更新用户设置。

```
方法签名：UserSettingsDTO updateUserSettings(UserSettingsUpdateRequest request, 
                                             String userId)
参数：
  - request：用户设置更新请求
  - userId：用户ID
返回：
  - UserSettingsDTO：更新后的用户设置 DTO
异常：无
```

#### getUserDefaultModelId

获取用户默认模型 ID。

```
方法签名：String getUserDefaultModelId(String userId)
参数：
  - userId：用户ID
返回：
  - String：默认模型 ID，如果未设置则返回 null
异常：无
```

#### getUserFallbackChain

获取用户降级链配置。

```
方法签名：List<String> getUserFallbackChain(String userId)
参数：
  - userId：用户ID
返回：
  - List<String>：降级模型ID列表，如果未启用降级则返回 null
异常：无
```

## 5. 集成设计

### 5.1 与 AuthSettingDomainService 集成

用户管理模块依赖 AuthSettingDomainService 进行认证开关控制。

**集成点**：
- 普通登录开关（AuthFeatureKey.NORMAL_LOGIN）
- 用户注册开关（AuthFeatureKey.USER_REGISTER）
- 第三方登录开关（AuthFeatureKey.SSO_LOGIN）

**用途**：
- 灵活控制登录方式的启用/禁用
- 管理员可以根据需要关闭注册功能
- 支持运维层面的认证策略调整

**示例**：
```java
if (!authSettingDomainService.isFeatureEnabled(AuthFeatureKey.NORMAL_LOGIN)) {
    throw new BusinessException("普通登录已禁用");
}
```

### 5.2 与 EmailService 集成

用户管理模块依赖 EmailService 发送验证邮件。

**集成点**：
- 注册验证码邮件
- 重置密码验证码邮件

**用途**：
- 验证用户邮箱所有权
- 完成注册和密码重置流程的安全验证


### 5.3 与 VerificationCodeService 集成

用户管理模块依赖 VerificationCodeService 管理验证码。

**集成点**：
- 验证码生成
- 验证码验证
- 验证码过期管理
- 业务类型区分（注册、重置密码）

**用途**：
- 防止恶意注册
- 验证用户邮箱所有权
- 防止验证码滥用


### 5.4 与 SsoServiceFactory 集成

用户管理模块依赖 SsoServiceFactory 处理第三方登录。

**集成点**：
- 获取 SSO 登录 URL
- 获取 SSO 用户信息
- 支持多种 SSO 提供商（GitHub）

**用途**：
- 提供第三方登录能力
- 统一管理不同 SSO 提供商
- 便于扩展新的 SSO 提供商

## 6. 数据流程图

### 6.1 登录流程图

```
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 1. 发送登录请求（账号、密码）
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 2. 检查普通登录是否启用
     ↓
┌─────────────────────────────┐
│ AuthSettingDomainService   │
└────┬──────────────────────┘
     │ 3. 返回启用状态
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 4. 查找用户
     ↓
┌─────────────────────────────┐
│ UserRepository            │
└────┬──────────────────────┘
     │ 5. 返回用户信息
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 6. 验证密码（BCrypt）
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 7. 生成 JWT Token
     ↓
┌─────────────────────────────┐
│ JwtUtils                  │
└────┬──────────────────────┘
     │ 8. 返回 Token
     ↓
┌─────────────────────────────┐
│ 客户端                   │
└─────────────────────────────┘
```

### 6.2 注册流程图

```
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 1. 发送注册请求（邮箱、密码、验证码）
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 2. 检查用户注册是否启用
     ↓
┌─────────────────────────────┐
│ AuthSettingDomainService   │
└────┬──────────────────────┘
     │ 3. 返回启用状态
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 4. 验证邮箱验证码
     ↓
┌─────────────────────────────┐
│ VerificationCodeService    │
└────┬──────────────────────┘
     │ 5. 返回验证结果
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 6. 检查账号是否已存在
     ↓
┌─────────────────────────────┐
│ UserRepository            │
└────┬──────────────────────┘
     │ 7. 返回查询结果
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 8. 创建用户记录（密码加密）
     ↓
┌─────────────────────────────┐
│ UserRepository            │
└────┬──────────────────────┘
     │ 9. 保存用户
     ↓
┌─────────────────────────────┐
│ UserSettingsRepository    │
└────┬──────────────────────┘
     │ 10. 创建用户设置记录
     ↓
┌─────────────────────────────┐
│ 客户端                   │
└─────────────────────────────┘
```

### 6.3 SSO 流程图

```
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 1. 请求 SSO 登录
     ↓
┌─────────────────────────────┐
│ SsoAppService             │
└────┬──────────────────────┘
     │ 2. 获取 SSO 登录 URL
     ↓
┌─────────────────────────────┐
│ SsoServiceFactory         │
└────┬──────────────────────┘
     │ 3. 获取 SSO 服务
     ↓
┌─────────────────────────────┐
│ SsoService (GitHub)       │
└────┬──────────────────────┘
     │ 4. 返回登录 URL
     ↓
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 5. 跳转到 SSO 授权页面
     ↓
┌─────────────────────────────┐
│ SSO 提供商 (GitHub)       │
└────┬──────────────────────┘
     │ 6. 用户授权，回调
     ↓
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 7. 授权码回调
     ↓
┌─────────────────────────────┐
│ SsoAppService             │
└────┬──────────────────────┘
     │ 8. 处理 SSO 回调
     ↓
┌─────────────────────────────┐
│ SsoService                │
└────┬──────────────────────┘
     │ 9. 获取用户信息
     ↓
┌─────────────────────────────┐
│ SsoAppService             │
└────┬──────────────────────┘
     │ 10. 查找或创建用户
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 11. 返回用户实体
     ↓
┌─────────────────────────────┐
│ SsoAppService             │
└────┬──────────────────────┘
     │ 12. 生成 JWT Token
     ↓
┌─────────────────────────────┐
│ 客户端                   │
└─────────────────────────────┘
```

### 6.4 密码重置流程图

```
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 1. 请求重置密码（邮箱）
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 2. 检查普通登录是否启用
     ↓
┌─────────────────────────────┐
│ AuthSettingDomainService   │
└────┬──────────────────────┘
     │ 3. 返回启用状态
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 4. 验证邮箱是否已注册
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 5. 查找用户
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 6. 生成验证码
     ↓
┌─────────────────────────────┐
│ VerificationCodeService    │
└────┬──────────────────────┘
     │ 7. 返回验证码
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 8. 发送验证邮件
     ↓
┌─────────────────────────────┐
│ EmailService              │
└────┬──────────────────────┘
     │ 9. 邮件发送成功
     ↓
┌─────────┐
│ 客户端   │
└────┬────┘
     │ 10. 查收邮件，输入验证码和新密码
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 11. 验证验证码
     ↓
┌─────────────────────────────┐
│ VerificationCodeService    │
└────┬──────────────────────┘
     │ 12. 返回验证结果
     ↓
┌─────────────────────────────┐
│ LoginAppService           │
└────┬──────────────────────┘
     │ 13. 更新密码
     ↓
┌─────────────────────────────┐
│ UserDomainService         │
└────┬──────────────────────┘
     │ 14. 密码加密并更新
     ↓
┌─────────────────────────────┐
│ UserRepository            │
└────┬──────────────────────┘
     │ 15. 保存更新
     ↓
┌─────────────────────────────┐
│ 客户端                   │
└─────────────────────────────┘
```
