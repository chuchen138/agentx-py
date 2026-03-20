# 认证设置（Auth Settings）技术实现文档

## 1. 架构设计

### 1.1 整体架构

认证设置模块基于 DDD（领域驱动设计）架构，采用分层设计，核心层次包括：

- **应用层（Application Layer）**：提供认证配置的业务编排服务
- **领域层（Domain Layer）**：封装认证配置的领域模型和业务逻辑
- **基础设施层（Infrastructure Layer）**：提供数据持久化和外部服务集成

```
应用层（Application）
├─ AuthAppService（业务编排）
│  └─ 主要方法：get_auth_config, get_all_auth_settings, 
│    get_auth_setting_by_id, toggle_auth_setting, 
│    update_auth_setting, delete_auth_setting, create_auth_setting
├─ DTO（数据传输对象）
│  └─ AuthConfigDTO, AuthSettingResponse, 
│    LoginMethodDTO, AuthSettingUpdate, AuthSettingCreate
         ↓
领域层（Domain）
├─ AuthDomainService（认证领域服务）
├─ AuthSettingDomainService（认证设置领域服务）
├─ Constant（常量枚举）
│  └─ AuthFeatureKey, FeatureType, SsoProvider
├─ Model（领域模型）
│  └─ AuthSettingModel, VerificationCode
└─ Repository（仓储接口）
   └─ AuthSettingRepository
         ↓
基础设施层（Infrastructure）
└─ Database（数据库）
   └─ auth_settings table
```

### 1.2 设计原则

1. **单一职责原则**：每个类和方法只负责单一职责
2. **开闭原则**：通过枚举和映射关系支持扩展新的认证方式
3. **依赖倒置原则**：领域层不依赖基础设施层，通过接口抽象
4. **接口隔离原则**：提供细粒度的接口方法

## 2. 核心设计

### 2.1 认证策略模式

#### 2.1.1 设计思路

通过功能键（FeatureKey）到 SSO 提供商（SsoProvider）的映射，实现认证策略的灵活选择。不同的登录方式对应不同的认证策略，但对外提供统一的接口。

#### 2.1.2 核心组件

**1. 功能键枚举（AuthFeatureKey）**

定义系统中所有可用的认证功能类型：

- NORMAL_LOGIN：普通登录
- GITHUB_LOGIN：GitHub 登录
- COMMUNITY_LOGIN：敲鸭登录
- USER_REGISTER：用户注册

**2. 功能类型枚举（FeatureType）**

定义功能的大类：

- LOGIN：登录功能
- REGISTER：注册功能

**3. 提供商枚举（SsoProvider）**

定义支持的 SSO 提供商：

- COMMUNITY：敲鸭
- GITHUB：GitHub
- GOOGLE：Google
- WECHAT：微信

**4. 提供商映射逻辑**

在应用层服务中实现功能键到提供商的映射关系，通过字符串匹配转换提供商代码。

#### 2.1.3 设计优势

- **扩展性强**：新增认证方式时，只需添加新的功能键和映射关系
- **类型安全**：使用枚举保证类型安全，避免字符串硬编码
- **可维护性强**：集中管理认证策略，便于维护和修改

### 2.2 配置存储设计

#### 2.2.1 数据模型

**认证配置实体（AuthSettingModel）**

核心字段设计：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| id | String | 主键，UUID |
| feature_type | String | 功能类型（LOGIN/REGISTER） |
| feature_key | String | 功能键，唯一标识 |
| feature_name | String | 功能显示名称 |
| enabled | Boolean | 启用状态 |
| config_data | JSON | 扩展配置数据（JSON） |
| display_order | Integer | 显示顺序 |
| description | String | 功能描述 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

#### 2.2.2 数据库表结构

**auth_settings 表**

| 字段 | 类型 | 约束 | 说明 |
|------|------|--------|------|
| id | VARCHAR(64) | PK | 主键，UUID |
| feature_type | VARCHAR(32) | NOT NULL | 功能类型 |
| feature_key | VARCHAR(64) | UNIQUE | 功能键 |
| feature_name | VARCHAR(128) | NOT NULL | 功能显示名称 |
| enabled | BOOLEAN | NOT NULL | 启用状态 |
| config_data | JSON | NULL | 扩展配置数据 |
| display_order | INT | NULL | 显示顺序 |
| description | TEXT | NULL | 功能描述 |
| created_at | DATETIME | NOT NULL | 创建时间 |
| updated_at | DATETIME | NOT NULL | 更新时间 |

#### 2.2.3 JSON 配置存储

使用 SQLAlchemy 的 JSON 类型实现配置数据的存储，支持灵活存储不同类型的配置参数。

**优势**：
- 灵活存储不同类型的配置参数
- 支持复杂嵌套结构
- 便于扩展新的配置字段

### 2.3 功能键管理

#### 2.3.1 功能键特性

**唯一性约束**

- 每个 `featureKey` 必须唯一
- 创建配置时检查是否已存在相同 `featureKey` 的记录

**分类管理**

- 通过 `featureType` 对功能进行分类（LOGIN/REGISTER）
- 支持按类型查询功能列表

#### 2.3.2 功能键示例

| featureType | featureKey | featureName | 说明 |
|-------------|------------|--------------|------|
| LOGIN | NORMAL_LOGIN | 普通登录 | 用户名密码登录 |
| LOGIN | GITHUB_LOGIN | GitHub登录 | GitHub OAuth 登录 |
| LOGIN | COMMUNITY_LOGIN | 敲鸭登录 | 社区认证登录 |
| REGISTER | USER_REGISTER | 用户注册 | 用户注册功能 |

## 3. 关键接口定义

### 3.1 应用层接口

#### 3.1.1 AuthAppService

**获取前端认证配置**
- 功能：获取前端所需的认证配置，包括所有启用的登录方式和注册开关状态
- 返回：包含登录方式和注册开关的配置对象

**获取所有认证配置**
- 功能：获取系统中所有的认证配置

**根据ID获取认证配置**
- 功能：根据配置 ID 获取单个认证配置

**切换认证配置启用状态**
- 功能：一键切换认证配置的启用状态

**更新认证配置**
- 功能：更新认证配置的部分字段
- 支持部分字段更新

**删除认证配置**
- 功能：删除指定的认证配置

### 3.2 领域层接口

#### 3.2.1 AuthSettingDomainService

**获取启用功能列表**
- 功能：获取指定类型的启用功能列表，按显示顺序排序

**获取所有功能列表**
- 功能：获取指定类型的所有功能列表，按显示顺序排序

**检查功能是否启用**
- 功能：快速判断指定功能是否启用

**根据功能键获取配置**
- 功能：根据功能键获取认证配置

## 4. DTO 设计

### 4.1 AuthConfigDTO

前端认证配置响应 DTO，用于登录界面渲染。

字段设计：
- loginMethods（登录方式集合）：Map<String, LoginMethodDTO>
- registerEnabled（注册是否启用）：Boolean

**返回数据示例**：
```json
{
  "loginMethods": {
    "NORMAL_LOGIN": {
      "enabled": true,
      "name": "普通登录"
    },
    "GITHUB_LOGIN": {
      "enabled": true,
      "name": "GitHub登录",
      "provider": "GITHUB"
    }
  },
  "registerEnabled": true
}
```

### 4.2 LoginMethodDTO

登录方式 DTO，简化认证配置信息。

字段设计：
- enabled（是否启用）：Boolean
- name（显示名称）：String
- provider（SSO 提供商）：String（可选）

### 4.3 AuthSettingDTO

认证配置 DTO，包含完整的配置信息。

字段设计：
- id（配置ID）：String
- featureType（功能类型）：String
- featureKey（功能键）：String
- featureName（功能名称）：String
- enabled（启用状态）：Boolean
- configData（配置数据）：Map<String, Object>
- displayOrder（显示顺序）：Integer
- description（功能描述）：String
- createdAt（创建时间）：LocalDateTime
- updatedAt（更新时间）：LocalDateTime

### 4.4 UpdateAuthSettingRequest

更新认证配置请求 DTO，支持部分更新。

字段设计：
- featureName（功能名称）：String
- enabled（启用状态）：Boolean
- configData（配置数据）：Map<String, Object>
- displayOrder（显示顺序）：Integer
- description（功能描述）：String

## 5. 数据转换

### 5.1 Assembler 设计

**AuthSettingAssembler** 负责实体与 DTO 之间的转换。

**主要方法**：
- toDTO：将 Entity 转换为 DTO
- toDTOs：批量转换 Entity 列表
- updateEntity：根据请求更新 Entity，支持部分字段更新

### 5.2 转换流程

**查询流程**：Entity → Assembler → DTO
```
数据库 → AuthSettingRepository → AuthSettingEntity 
       → AuthSettingAssembler.toDTO() 
       → AuthSettingDTO 
       → Controller → Response
```

**更新流程**：Request → Assembler → Entity
```
Request → UpdateAuthSettingRequest 
       → AuthSettingAssembler.updateEntity() 
       → AuthSettingEntity 
       → AuthSettingDomainService 
       → AuthSettingRepository 
       → Database
```

## 6. 业务流程

### 6.1 获取认证配置流程

```
前端请求
    ↓
Controller.getAuthConfig()
    ↓
AuthAppService.getAuthConfig()
    ↓
1. 查询启用的登录方式
   AuthSettingDomainService.getEnabledFeatures(FeatureType.LOGIN)
    ↓
2. 查询注册是否启用
   AuthSettingDomainService.isFeatureEnabled(USER_REGISTER)
    ↓
3. 构建登录方式 DTO
   遍历登录方式，转换成 LoginMethodDTO
    ↓
4. 映射提供商
   调用映射方法获取 SSO 提供商
    ↓
5. 构建 AuthConfigDTO
   设置 loginMethods 和 registerEnabled
    ↓
返回前端
```

### 6.2 切换启用状态流程

```
前端请求（切换状态）
    ↓
Controller.toggleAuthSetting(id)
    ↓
AuthAppService.toggleAuthSetting(id)
    ↓
1. 查询配置
   AuthSettingDomainService.getById(id)
    ↓
2. 切换启用状态
   AuthSettingDomainService.toggleEnabled(id)
   - 反转 enabled 字段
   - 更新数据库
    ↓
3. 转换 DTO
   AuthSettingAssembler.toDTO(entity)
    ↓
返回结果
```

### 6.3 更新认证配置流程

```
前端请求（更新配置）
    ↓
Controller.updateAuthSetting(id, request)
    ↓
AuthAppService.updateAuthSetting(id, request)
    ↓
1. 查询原配置
   AuthSettingDomainService.getById(id)
    ↓
2. 更新实体
   AuthSettingAssembler.updateEntity(entity, request)
   - 支持部分字段更新
    ↓
3. 保存配置
   AuthSettingDomainService.updateAuthSetting(entity)
    ↓
4. 转换 DTO
   AuthSettingAssembler.toDTO(savedEntity)
    ↓
返回结果
```


## 7. 扩展性设计

### 7.1 新增认证方式

**步骤**：

1. 在 `AuthFeatureKey` 枚举中添加新的功能键
2. 在应用层服务中添加映射关系（功能键 → 提供商）
3. 在数据库 `auth_settings` 表中创建对应的配置记录

**优势**：
- 无需修改核心业务逻辑
- 只需添加枚举和映射关系
- 配置化管理，易于维护

### 7.2 新增配置字段

由于 `configData` 使用 JSON 存储，新增配置字段只需：

1. 在 JSON 中添加新的键值对
2. 前端和后端解析新的字段
3. 无需修改数据库表结构

**示例配置数据**：
```json
{
  "clientId": "xxx",
  "clientSecret": "xxx",
  "scope": "user:email",
  "redirectUri": "http://localhost:8080/callback"
}
```

## 8. 性能优化

### 8.1 查询优化

- 使用 SQLAlchemy 的 ORM 查询，避免 SQL 注入
- 字段索引：在 `feature_type` 和 `feature_key` 上建立索引
- 排序优化：按 `display_order` 排序，减少前端排序负担

### 8.2 缓存策略（可选）

可以考虑对认证配置进行缓存：

- 使用 Redis 缓存认证配置
- 缓存 key：`auth:config:all` 或 `auth:config:{featureType}`
- 缓存过期时间：5-10 分钟
- 配置变更时主动清除缓存

## 9. 安全性设计

### 9.1 权限控制

- 配置管理需要管理员权限
- 查询接口可开放给所有用户
- 更新、删除接口需要管理员权限

### 9.2 数据验证

- 创建配置时验证 `featureKey` 唯一性
- 更新配置时验证字段有效性
- JSON 配置数据格式验证

### 9.3 审计日志

- 记录配置的创建、更新、删除操作
- 记录操作人和操作时间
- 便于追踪和审计

## 10. 异常处理

### 10.1 业务异常

- 配置不存在：抛出配置不存在的业务异常
- 功能键已存在：抛出功能键已存在的业务异常

### 10.2 系统异常

- 数据库连接失败
- 数据转换异常
- JSON 解析异常

## 11. 未来优化方向

### 11.1 配置版本管理

- 支持配置的历史版本记录
- 支持配置的回滚操作
- 支持配置的导出和导入

### 11.2 配置模板

- 提供预定义的配置模板
- 支持一键应用配置模板
- 支持自定义配置模板

### 11.3 分布式配置

- 支持多实例配置同步
- 支持配置的实时推送
- 支持配置的灰度发布

## 12. 技术栈

- **框架**：FastAPI
- **ORM**：SQLAlchemy
- **数据库**：PostgreSQL（或其他关系型数据库）
- **JSON 处理**：Pydantic
- **类型转换**：SQLAlchemy JSON 类型
