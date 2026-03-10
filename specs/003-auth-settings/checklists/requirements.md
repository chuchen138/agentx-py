## 实施
- [ ] 1.1 定义认证设置实体和数据模型
     【目标对象】`app/domain/auth/`
     【修改目的】定义认证设置相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【修改内容】
        - 创建 AuthSetting 模型（auth_settings 表）
        - 定义字段（feature_key, feature_name, feature_type, enabled, config_json）
        - 实现枚举类型（FeatureType: LOGIN, FEATURE）
        - 实现 Pydantic Schema

- [ ] 1.2 实现认证设置仓储模式
     【目标对象】`app/domain/auth/repository.py`
     【修改目的】定义认证设置数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AuthSettingRepository 接口
        - 实现 SQLAlchemy AuthSettingRepository
        - 实现 CRUD 操作
        - 实现按类型查询
        - 实现按 feature_key 查询
        - 实现查询已启用的配置

- [ ] 1.3 实现认证设置领域服务
     【目标对象】`app/domain/auth/service.py`
     【修改目的】封装认证设置相关的业务逻辑
     【修改方式】实现领域服务层
     【相关依赖】AuthSettingRepository
     【修改内容】
        - 创建认证配置时初始化默认状态
        - 启用/禁用功能切换
        - 配置更新逻辑
        - 按类型获取配置
        - 检查功能是否启用
        - 配置校验逻辑

- [ ] 1.4 实现应用服务层
     【目标对象】`app/application/auth/`
     【修改目的】编排认证设置相关的用例
     【修改方式】实现应用服务
     【相关依赖】AuthSettingDomainService
     【修改内容】
        - 实现 AuthSettingAppService（认证配置管理）
        - getAuthConfig - 获取前端认证配置（包含登录方式和功能开关）
        - getAllAuthSettings - 获取所有认证配置
        - getAuthSettingById - 根据ID获取配置
        - toggleAuthSetting - 切换启用状态
        - updateAuthSetting - 更新认证配置
        - createAuthSetting - 创建认证配置
        - deleteAuthSetting - 删除认证配置

- [ ] 1.5 实现 Assembler 模式
     【目标对象】`app/application/auth/assembler.py`
     【修改目的】在领域模型和 DTO 之间进行转换
     【修改方式】实现 Assembler 模式
     【相关依赖】AuthSettingEntity
     【修改内容】
        - toDTO - 实体转 DTO
        - toDTOs - 实体列表转 DTO 列表
        - updateEntity - 更新实体（从 DTO）
        - 实现配置 JSON 序列化/反序列化

- [ ] 1.6 创建 API 路由（FastAPI）
     【目标对象】`app/api/v1/auth/`
     【修改目的】暴露认证相关的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AuthSettingAppService
     【修改内容】
        - `GET /api/v1/auth/config` - 获取前端认证配置
        - `GET /api/v1/auth/settings` - 获取所有认证配置
        - `GET /api/v1/auth/settings/{id}` - 根据ID获取配置
        - `PUT /api/v1/auth/settings/{id}` - 更新认证配置
        - `POST /api/v1/auth/settings/{id}/toggle` - 切换启用状态
        - `DELETE /api/v1/auth/settings/{id}` - 删除认证配置
        - `POST /api/v1/auth/settings` - 创建认证配置

- [ ] 1.7 实现 OAuth 2.0 提供商支持
     【目标对象】`app/infrastructure/oauth/`
     【修改目的】支持第三方登录（GitHub、Google、WeChat 等）
     【修改方式】使用 Authlib 实现 OAuth 2.0
     【相关依赖】Authlib, AuthSettingService
     【修改内容】
        - 定义 OAuth 提供商枚举
        - 实现 OAuth 客户端注册
        - 实现授权 URL 生成
        - 实现回调处理
        - 实现用户信息获取

- [ ] 1.8 实现配置缓存
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升认证配置查询性能
     【修改方式】使用 Redis 进行缓存
     【相关依赖】Redis, AuthSettingService
     【修改内容】
        - 缓存所有认证配置
        - 缓存前端认证配置
        - 配置变更时清除缓存
        - 实现缓存预热

- [ ] 1.9 编写单元测试
     【目标对象】`tests/test_auth_setting_service.py`
     【修改目的】确保认证设置功能正确性
     【修改方式】使用 pytest
     【相关依赖】AuthSettingAppService
     【修改内容】
        - 测试认证配置创建
        - 测试认证配置更新
        - 测试启用/禁用功能
        - 测试按类型查询
        - 测试按 feature_key 查询
        - 测试功能开关检查
        - 测试前端配置生成
        - 测试配置 JSON 序列化

- [ ] 1.10 编写集成测试
     【目标对象】`tests/integration/test_auth_setting_api.py`
     【修改目的】确保认证 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AuthSettingAppService
     【修改内容】
        - 测试获取前端配置端点
        - 测试获取所有配置端点
        - 测试更新配置端点
        - 测试切换状态端点
        - 测试创建配置端点
        - 测试删除配置端点
        - 测试配置缓存功能
