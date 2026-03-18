## 实施

- [x] 1.1 定义用户实体和数据模型
     【目标对象】`app/domain/user/model.py`
     【修改目的】定义用户相关的领域模型和数据库表结构
     【修改方式】使用 SQLAlchemy 2.0 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 User 模型（users 表）
        - 创建 UserSettings 模型（user_settings 表）
        - 定义 id, email, nickname, password_hash, created_at, updated_at 等字段
        - 创建外键关联（user_settings.user_id -> user.id）
        - 实现 Pydantic Schema（UserCreate, UserUpdate, UserResponse, UserSettingsConfig 等）
        - 定义模型索引和约束

- [x] 1.2 创建数据库迁移脚本
     【目标对象】`alembic/versions/`
     【修改目的】初始化用户管理相关的数据库表
     【修改方式】使用 Alembic 创建并执行迁移脚本
     【相关依赖】Alembic, SQLAlchemy
     【修改内容】
        - 创建 users 表迁移脚本
        - 创建 user_settings 表迁移脚本
        - 定义索引（email 唯一索引）
        - 定义外键约束
        - 添加初始化数据（如默认用户设置）

- [x] 1.3 实现用户仓储模式
     【目标对象】`app/domain/user/repository.py`
     【修改目的】定义用户数据访问接口和实现
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 UserRepository 接口
        - 实现 SQLAlchemy UserRepository
        - 实现 CRUD 操作（create, get_by_id, update, delete）
        - 实现复杂查询（按 email、github_id 查询）
        - 实现事务管理

- [x] 1.4 实现用户领域服务
     【目标对象】`app/domain/user/service.py`
     【修改目的】封装用户相关的核心业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】UserRepository, Passlib, PyJWT
     【修改内容】
        - 密码加密和验证（使用 Passlib/Bcrypt）
        - 用户注册逻辑（验证邮箱唯一性）
        - 生成 JWT Token（包含用户信息和过期时间）
        - 验证 JWT Token
        - 用户设置管理（读取和更新 JSON 配置）

- [x] 1.5 实现 UserAppService
     【目标对象】`app/application/user/user_app_service.py`
     【修改目的】编排用户信息管理的用例
     【修改方式】实现应用服务
     【相关依赖】UserDomainService, UserRepository
     【修改内容】
        - get_current_user() - 获取当前登录用户信息
        - update_user_profile() - 更新用户基本信息（昵称、手机号、头像等）
        - delete_user() - 删除用户账号
        - change_password() - 修改密码
        - validate_user() - 验证用户状态

- [x] 1.6 实现 LoginAppService
     【目标对象】`app/application/user/login_app_service.py`
     【修改目的】处理用户登录和注册流程
     【修改方式】实现应用服务
     【相关依赖】UserDomainService, UserRepository
     【修改内容】
        - register() - 用户注册（邮箱、密码、昵称、手机号）
        - login() - 用户登录（验证凭据、生成 Token）
        - logout() - 用户登出（失效 Token）
        - refresh_token() - 刷新 JWT Token
        - validate_credentials() - 验证用户凭据

- [x] 1.7 实现 SsoAppService
     【目标对象】`app/application/user/sso_app_service.py`
     【修改目的】处理 SSO 单点登录流程
     【修改方式】实现应用服务
     【相关依赖】Authlib, UserDomainService
     【修改内容】
        - get_sso_authorization_url() - 生成 SSO 授权 URL（支持 OAuth 2.0）
        - handle_sso_callback() - 处理 SSO 回调（获取授权码、交换 Token）
        - verify_sso_token() - 验证 SSO Token
        - create_or_link_user() - 创建新用户或关联现有用户
        - 解构用户信息从 SSO Provider（GitHub）

- [x] 1.8 实现 UserSettingsAppService
     【目标对象】`app/application/user/user_settings_app_service.py`
     【修改目的】管理用户偏好设置
     【修改方式】实现应用服务
     【相关依赖】UserRepository, UserDomainService
     【修改内容】
        - get_user_settings() - 获取用户设置（JSON 格式）
        - update_user_settings() - 更新用户设置（部分更新）
        - reset_user_settings() - 重置为默认设置
        - get_setting_value() - 获取单个设置项
        - update_setting_value() - 更新单个设置项

- [x] 1.9 创建认证 API 路由
     【目标对象】`app/api/v1/auth/`
     【修改目的】暴露认证相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】LoginAppService, SsoAppService
     【修改内容】
        - `POST /api/v1/auth/register` - 用户注册
        - `POST /api/v1/auth/login` - 用户登录
        - `POST /api/v1/auth/logout` - 用户登出
        - `POST /api/v1/auth/refresh` - 刷新 Token
        - `GET /api/v1/auth/sso/{provider}/authorize` - SSO 授权入口
        - `GET /api/v1/auth/sso/{provider}/callback` - SSO 回调

- [x] 1.10 创建用户管理 API 路由
     【目标对象】`app/api/v1/users/`
     【修改目的】暴露用户管理相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】UserAppService, UserSettingsAppService
     【修改内容】
        - `GET /api/v1/users/me` - 获取当前用户信息
        - `PUT /api/v1/users/me` - 更新当前用户信息
        - `DELETE /api/v1/users/me` - 删除当前用户账号
        - `POST /api/v1/users/me/change-password` - 修改密码
        - `GET /api/v1/users/me/settings` - 获取用户设置
        - `PUT /api/v1/users/me/settings` - 更新用户设置

- [x] 1.11 实现 JWT 认证中间件
     【目标对象】`app/api/middleware/auth.py`
     【修改目的】保护需要认证的 API 端点
     【修改方式】实现 FastAPI 中间件和依赖注入
     【相关依赖】PyJWT, UserDomainService
     【修改内容】
        - 创建 get_current_user() 依赖函数
        - 验证 Bearer Token
        - 解析 Token 并提取用户信息
        - 将用户信息注入 Request 对象
        - 实现 optional_auth 可选认证依赖
        - 定义认证异常处理器

- [x] 1.12 实现 DTO 和请求/响应模型
     【目标对象】`app/api/v1/auth/routes.py` 和 `app/api/v1/users/routes.py`
     【修改目的】定义 API 数据传输对象
     【修改方式】使用 Pydantic 定义数据模型
     【相关依赖】Pydantic, UserDTO, UserSettingsDTO
     【修改内容】
        - RegisterRequest（邮箱、密码、昵称、手机号）
        - LoginRequest（邮箱、密码）
        - LoginResponse（access_token, refresh_token, expires_in）
        - UserResponse（用户基本信息）
        - UpdateUserRequest（可更新的用户字段）
        - UserSettingsResponse（用户设置 JSON）
        - UpdateUserSettingsRequest（部分更新的设置字段）
        - ChangePasswordRequest（当前密码、新密码、确认密码）
        - RefreshTokenRequest（refresh_token）

- [x] 1.13 实现密码加密配置
     【目标对象】`app/domain/user/service.py`
     【修改目的】配置密码加密和 JWT 相关参数
     【修改方式】使用 Passlib 和 PyJWT 配置
     【相关依赖】Passlib, PyJWT
     【修改内容】
        - 配置密码加密算法（bcrypt）
        - 定义 JWT 算法（HS256）
        - 配置 Token 过期时间（access_token, refresh_token）
        - 配置 JWT 密钥（从环境变量读取）
        - 定义密码强度规则

- [x] 1.14 实现 SSO Provider 配置
     【目标对象】`app/application/user/sso_app_service.py`
     【修改目的】配置支持的 SSO Providers
     【修改方式】使用 Authlib 配置 OAuth 2.0 Clients
     【相关依赖】Authlib
     【修改内容】
        - 配置 GitHub OAuth 2.0
        - 定义 Provider 注册表
        - 配置回调 URL
        - 定义 Provider 元数据（client_id, client_secret 等）

- [ ] 1.15 编写用户领域服务单元测试
     【目标对象】`tests/unit/test_user_domain_service.py`
     【修改目的】确保用户领域逻辑正确性
     【修改方式】使用 pytest 和 pytest-mock
     【相关依赖】UserDomainService, Mock User Repository
     【修改内容】
        - 测试密码加密和验证
        - 测试用户注册业务逻辑
        - 测试 JWT Token 生成（包含正确的用户信息和过期时间）
        - 测试 JWT Token 验证（成功和失败场景）
        - 测试用户设置管理（读取和更新）

- [ ] 1.16 编写登录服务单元测试
     【目标对象】`tests/unit/test_login_app_service.py`
     【修改目的】确保登录逻辑正确性
     【修改方式】使用 pytest 和 pytest-mock
     【相关依赖】LoginAppService, Mock User Domain Service
     【修改内容】
        - 测试用户注册（成功和失败场景）
        - 测试用户登录（正确凭据和凭据错误）
        - 测试登出功能
        - 测试 Token 刷新（有效 Token 和无效 Token）
        - 测试凭据验证

- [ ] 1.17 编写 SSO 服务单元测试
     【目标对象】`tests/unit/test_sso_app_service.py`
     【修改目的】确保 SSO 流程正确性
     【修改方式】使用 pytest 和 pytest-mock
     【相关依赖】SsoAppService, Mock Authlib Client
     【修改内容】
        - 测试生成授权 URL（各 Provider）
        - 测试处理 SSO 回调（成功和失败场景）
        - 测试验证 SSO Token
        - 测试创建新用户
        - 测试关联现有用户

- [ ] 1.18 编写用户设置服务单元测试
     【目标对象】`tests/unit/test_user_settings_app_service.py`
     【修改目的】确保用户设置管理正确性
     【修改方式】使用 pytest 和 pytest-mock
     【相关依赖】UserSettingsAppService, Mock User Repository
     【修改内容】
        - 测试获取用户设置
        - 测试更新用户设置（部分更新和全量更新）
        - 测试重置用户设置
        - 测试获取单个设置项
        - 测试设置验证逻辑

- [ ] 1.19 编写认证 API 集成测试
     【目标对象】`tests/integration/test_auth_api.py`
     【修改目的】确保认证 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient 和测试数据库
     【相关依赖】FastAPI, LoginAppService, SsoAppService
     【修改内容】
        - 测试注册端点（成功和重复注册）
        - 测试登录端点（成功和失败）
        - 测试登出端点
        - 测试刷新 Token 端点
        - 测试 SSO授权端点（各 Provider）
        - 测试 SSO 回调端点
        - 测试认证中间件（未认证、过期 Token、无效 Token）

- [ ] 1.20 编写用户管理 API 集成测试
     【目标对象】`tests/integration/test_user_api.py`
     【修改目的】确保用户管理 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient 和测试数据库
     【相关依赖】FastAPI, UserAppService, UserSettingsAppService
     【修改内容】
        - 测试获取当前用户（已认证和未认证）
        - 测试更新用户信息（成功和无效数据）
        - 测试删除用户账号
        - 测试修改密码（正确旧密码和错误旧密码）
        - 测试获取和更新用户设置
        - 测试头像上传（成功和失败）
        - 测试 API 权限控制

- [ ] 1.21 编写认证中间件集成测试
     【目标对象】`tests/integration/test_auth_middleware.py`
     【修改目的】确保认证中间件正确保护 API
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, Auth Middleware
     【修改内容】
        - 测试需要认证的端点（验证 Bearer Token）
        - 测试未认证访问（返回 401）
        - 测试过期 Token（返回 401）
        - 测试无效 Token（返回 401）
        - 测试可选认证端点（允许未认证访问）
        - 测试用户信息正确注入 Request


- [ ] 1.22 数据库集成测试
     【目标对象】`tests/integration/test_user_repository.py`
     【修改目的】确保数据访问层正确工作
     【修改方式】使用 pytest 和测试数据库
     【相关依赖】SQLAlchemy, Test Database
     【修改内容】
        - 测试创建用户（验证字段和关系）
        - 测试查询用户（按 id、username、email）
        - 测试更新用户
        - 测试删除用户（级联删除 user_settings）
        - 测试事务回滚
        - 测试并发操作

- [ ] 1.23 配置 Swagger/OpenAPI 文档
     【目标对象】`app/main.py`
     【修改目的】为用户管理 API 添加 API 文档
     【修改方式】配置 FastAPI 自动生成文档
     【相关依赖】FastAPI
     【修改内容】
        - 配置 API 标题和描述
        - 为认证端点添加安全配置（Bearer Token）
        - 为所有端点添加详细描述
        - 定义请求/响应示例
        - 配置 Tag 分组（认证、用户管理）

- [x] 1.24 环境变量配置
     【目标对象】`.env`
     【修改目的】定义用户管理模块所需的环境变量
     【修改方式】使用 python-dotenv
     【相关依赖】python-dotenv
     【修改内容】
        - JWT_SECRET_KEY
        - JWT_ALGORITHM
        - ACCESS_TOKEN_EXPIRE_MINUTES
        - REFRESH_TOKEN_EXPIRE_DAYS
        - SSO_GITHUB_CLIENT_ID
        - SSO_GITHUB_CLIENT_SECRET
        - 密码强度配置（最小长度、复杂度要求）

- [ ] 1.25 日志和监控
     【目标对象】`app/infra/logging.py`, `app/api/v1/user/`
     【修改目的】为用户管理模块添加日志记录
     【修改方式】使用 Python logging 模块
     【相关依赖】Python logging
     【修改内容】
        - 登录/注册成功和失败日志
        - SSO 登录流程日志
        - 用户信息修改日志
        - 认证失败日志（安全审计）
        - 敏感操作审计日志（密码修改、账号删除）
