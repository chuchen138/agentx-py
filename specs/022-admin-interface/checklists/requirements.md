# 管理后台实施清单

## 概述

本实施清单基于 spec.md 和 design.md，定义管理后台模块的具体实施步骤，包括官方服务商管理、官方工具审核、后台权限控制、管理员服务分层和官方资源查询等功能。

## 实施

### 1. 数据模型层

- [ ] 1.1 定义管理员实体和数据模型
     【目标对象】`app/domain/admin/model/`
     【修改目的】定义管理后台相关的领域模型
     【修改方式】使用 SQLAlchemy 定义 ORM 模型
     【相关依赖】SQLAlchemy, Pydantic
     【修改内容】
        - 创建 AdminUser 模型 (admin_users 表)
          * 字段:id, user_id, username, role, permissions, is_active, created_at, last_login_at
          * 索引:idx_user_id, idx_role, idx_is_active
          * 角色：SUPER_ADMIN, ADMIN, AUDITOR
        - 创建 AuditLog 模型 (audit_logs 表)
          * 字段:id, log_id, admin_user_id, action_type, resource_type, resource_id, action_details, ip_address, created_at
          * 索引:idx_admin_user_id, idx_action_type, idx_created_at
        - 创建 ToolAuditRecord 模型 (tool_audit_records 表)
          * 字段:id, record_id, tool_id, applicant_user_id, auditor_admin_id, audit_status, audit_comment, submitted_data, audited_at, created_at
          * 索引:idx_tool_id, idx_auditor_admin_id, idx_audit_status
        - 实现 Pydantic Schema
          * AdminUserDTO, AdminUserCreateRequest, AdminUserUpdateRequest
          * AuditLogDTO, AuditLogListRequest
          * ToolAuditRecordDTO, ToolAuditSubmitRequest, ToolAuditApproveRequest
          * AdminListRequest

- [ ] 1.2 实现管理员角色枚举
     【目标对象】`app/domain/admin/constant/`
     【修改目的】定义管理员角色和权限
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 AdminRole 枚举
          * SUPER_ADMIN - 超级管理员 (所有权限)
          * ADMIN - 管理员 (常规管理权限)
          * AUDITOR - 审核员 (工具审核权限)
        - 创建 AdminPermission 枚举
          * CREATE_OFFICIAL_PROVIDER - 创建官方服务商
          * MODIFY_OFFICIAL_PROVIDER - 修改官方服务商
          * DELETE_OFFICIAL_PROVIDER - 删除官方服务商
          * AUDIT_TOOL - 审核工具
          * MANAGE_OFFICIAL_TOOL - 管理官方工具
          * VIEW_AUDIT_LOGS - 查看审计日志
          * MANAGE_ADMINS - 管理管理员账户
        - 实现角色与权限的映射关系
        - 实现权限验证逻辑

- [ ] 1.3 实现审核状态枚举
     【目标对象】`app/domain/admin/constant/`
     【修改目的】定义工具审核状态
     【修改方式】使用 Python Enum
     【相关依赖】无
     【修改内容】
        - 创建 AuditStatus 枚举
          * PENDING - 待审核
          * IN_REVIEW - 审核中
          * APPROVED - 审核通过
          * REJECTED - 审核拒绝
          * CANCELLED - 已取消
        - 实现状态转换逻辑
        - 实现状态流转记录

### 2. 仓储层

- [ ] 2.1 实现管理员用户仓储模式
     【目标对象】`app/domain/admin/repository.py`
     【修改目的】定义管理员用户数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AdminUserRepository 接口
        - 实现 SQLAlchemyAdminUserRepository
          * create(admin_data) -> AdminUser
          * get_by_id(admin_id) -> AdminUser
          * get_by_user_id(user_id) -> AdminUser
          * get_by_username(username) -> AdminUser
          * get_admins_by_role(role) -> List[AdminUser]
          * get_all_admins(page, size) -> Page[AdminUser]
          * update_role(admin_id, role)
          * update_permissions(admin_id, permissions)
          * deactivate(admin_id)
          * delete(admin_id)

- [ ] 2.2 实现审计日志仓储模式
     【目标对象】`app/domain/admin/repository.py`
     【修改目的】定义审计日志数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 AuditLogRepository 接口
        - 实现 SQLAlchemyAuditLogRepository
          * record_log(log_data) -> AuditLog
          * get_by_id(log_id) -> AuditLog
          * get_by_admin_user_id(admin_id, page, size) -> Page[AuditLog]
          * get_by_action_type(action_type, page, size) -> Page[AuditLog]
          * get_by_resource(resource_type, resource_id) -> List[AuditLog]
          * get_by_time_range(start_time, end_time) -> List[AuditLog]
          * search_logs(keyword, page, size) -> Page[AuditLog]

- [ ] 2.3 实现工具审核记录仓储模式
     【目标对象】`app/domain/admin/repository.py`
     【修改目的】定义工具审核记录数据访问接口
     【修改方式】实现 Repository 模式
     【相关依赖】SQLAlchemy
     【修改内容】
        - 定义 ToolAuditRecordRepository 接口
        - 实现 SQLAlchemyToolAuditRecordRepository
          * create_audit_record(record_data) -> ToolAuditRecord
          * get_by_id(record_id) -> ToolAuditRecord
          * get_by_tool_id(tool_id) -> ToolAuditRecord
          * get_pending_audits() -> List[ToolAuditRecord]
          * get_by_auditor(admin_id, page, size) -> Page[ToolAuditRecord]
          * get_by_status(audit_status, page, size) -> Page[ToolAuditRecord]
          * update_audit_status(record_id, status, comment)
          * get_audit_history(tool_id) -> List[ToolAuditRecord]

### 3. 领域服务层

- [ ] 3.1 实现管理员权限服务
     【目标对象】`app/domain/admin/service.py`
     【修改目的】管理管理员权限验证
     【修改方式】使用 RBAC 模式
     【相关依赖】AdminUserRepository
     【修改内容】
        - 创建 AdminPermissionService 类
          * _admin_repository: AdminUserRepository
        - 实现方法:
          * verify_admin_role(admin_id, required_role) -> bool
            - 验证管理员角色
            - 角色层级检查 (SUPER_ADMIN > ADMIN > AUDITOR)
          * verify_permission(admin_id, permission) -> bool
            - 验证具体权限
            - 基于角色的权限检查
          * has_any_permission(admin_id, permissions) -> bool
            - 验证是否拥有任一权限
          * has_all_permissions(admin_id, permissions) -> bool
            - 验证是否拥有所有权限
          * get_admin_permissions(admin_id) -> Set[AdminPermission]
            - 获取管理员所有权限
        - 权限缓存:
          * 缓存管理员权限信息
          * 权限变更时刷新缓存

- [ ] 3.2 实现官方服务商管理服务
     【目标对象】`app/domain/admin/service.py`
     【修改目的】管理官方 LLM 服务商
     【修改方式】与 LLM 管理模块集成
     【相关依赖】LLMProviderRepository, AdminPermissionService
     【修改内容】
        - 创建 AdminLLMService 类
          * _provider_repository: LLMProviderRepository
          * _permission_service: AdminPermissionService
        - 实现方法:
          * create_official_provider(admin_id, provider_config) -> ProviderEntity
            - 验证管理员权限
            - 设置 isOfficial=true
            - 加密存储 API Key
            - 记录创建日志
          * update_official_provider(admin_id, provider_id, provider_config) -> ProviderEntity
            - 验证管理员权限
            - 支持密钥掩码处理 (保留原有密钥)
            - 记录更新日志
          * set_admin_level(provider_id, admin_level)
            - 设置管理员级别
            - 限制低级别管理员修改
          * delete_official_provider(admin_id, provider_id)
            - 验证管理员权限
            - 软删除或标记为禁用
            - 记录删除日志
          * list_official_providers(filters) -> List[ProviderEntity]
            - 查询所有官方服务商
            - 支持类型、状态过滤
            - 分页和排序

- [ ] 3.3 实现工具审核服务
     【目标对象】`app/domain/admin/service.py`
     【修改目的】审核和管理用户发布的工具
     【修改方式】实现审核工作流
     【相关依赖】ToolRepository, ToolAuditRecordRepository, AdminPermissionService
     【修改内容】
        - 创建 AdminToolService 类
          * _tool_repository: ToolRepository
          * _audit_repository: ToolAuditRecordRepository
          * _permission_service: AdminPermissionService
        - 实现方法:
          * submit_tool_for_audit(user_id, tool_data) -> ToolAuditRecord
            - 创建工具审核申请
            - 设置状态为 PENDING
            - 保存提交的工具数据
          * start_review(admin_id, record_id) -> ToolAuditRecord
            - 验证审核权限
            - 设置状态为 IN_REVIEW
            - 分配审核员
          * approve_audit(admin_id, record_id, comment) -> ToolAuditRecord
            - 验证审核权限
            - 设置状态为 APPROVED
            - 标记工具为官方工具 (isOfficial=true)
            - 发布工具
            - 记录审核通过日志
          * reject_audit(admin_id, record_id, comment) -> ToolAuditRecord
            - 验证审核权限
            - 设置状态为 REJECTED
            - 提供审核意见
            - 通知申请人
          * cancel_audit(user_id, record_id)
            - 取消待审核的申请
            - 设置状态为 CANCELLED
          * get_pending_audits() -> List[ToolAuditRecord]
            - 获取所有待审核工具
          * get_audit_history(tool_id) -> List[ToolAuditRecord]
            - 获取工具审核历史
        - 审核内容检查:
          * 工具名称和描述合规性
          * 工具接口定义完整性
          * 工具文档齐全性
          * 安全性检查
          * 合规性检查

- [ ] 3.4 实现审计日志服务
     【目标对象】`app/domain/admin/service.py`
     【修改目的】记录管理员操作审计日志
     【修改方式】使用 AOP 切面编程
     【相关依赖】AuditLogRepository
     【修改内容】
        - 创建 AuditLogService 类
          * _log_repository: AuditLogRepository
        - 实现方法:
          * log_action(admin_user_id, action_type, resource_type, resource_id, details, ip_address)
            - 记录操作日志
            - 异步写入数据库
          * get_admin_logs(admin_id, page, size) -> Page[AuditLog]
            - 查询管理员操作日志
          * get_resource_logs(resource_type, resource_id) -> List[AuditLog]
            - 查询资源操作历史
          * get_logs_by_timerange(start_time, end_time, page, size) -> Page[AuditLog]
            - 按时间范围查询日志
          * search_logs(keyword, page, size) -> Page[AuditLog]
            - 搜索日志
          * export_logs(format, filters) -> bytes
            - 导出日志为 CSV/Excel
        - 自动日志记录:
          * 使用装饰器自动记录管理操作
          * 捕获异常并记录

- [ ] 3.5 实现官方工具管理服务
     【目标对象】`app/domain/admin/service.py`
     【修改目的】管理已发布的官方工具
     【修改方式】与工具管理模块集成
     【相关依赖】ToolRepository, AdminPermissionService
     【修改内容】
        - 创建 OfficialToolService 类
          * _tool_repository: ToolRepository
          * _permission_service: AdminPermissionService
        - 实现方法:
          * get_official_tools(filters) -> List[ToolEntity]
            - 查询所有官方工具
            - 支持类型、审核状态过滤
          * update_official_tool(admin_id, tool_id, tool_data) -> ToolEntity
            - 验证管理员权限
            - 更新工具配置
            - 记录更新日志
          * disable_official_tool(admin_id, tool_id)
            - 禁用官方工具
            - 标记为不可用
            - 记录禁用日志
          * enable_official_tool(admin_id, tool_id)
            - 重新启用工具
            - 记录启用日志
          * delete_official_tool(admin_id, tool_id)
            - 删除官方工具 (谨慎操作)
            - 需要 SUPER_ADMIN 权限
            - 记录删除日志

### 4. 应用服务层

- [ ] 4.1 实现管理员用户应用服务
     【目标对象】`app/application/admin/`
     【修改目的】编排管理员用户管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】AdminUserRepository, AdminPermissionService
     【修改内容】
        - 实现 AdminUserAppService
          * create_admin(admin_config, operator_admin_id) -> AdminUserDTO
            - 创建管理员账户
            - 验证操作员权限
            - 分配初始角色
          * update_admin_role(admin_id, new_role, operator_admin_id) -> AdminUserDTO
            - 更新管理员角色
            - 验证权限 (不能创建比自己级别高的管理员)
          * update_admin_permissions(admin_id, permissions, operator_admin_id)
            - 更新管理员权限
          * deactivate_admin(admin_id, operator_admin_id)
            - 停用管理员账户
          * get_admin(admin_id) -> AdminUserDTO
            - 获取管理员详情
          * list_admins(role_filter, page, size) -> Page[AdminUserDTO]
            - 获取管理员列表
            - 支持角色过滤
          * check_admin_permission(admin_id, permission) -> bool
            - 检查管理员权限

- [ ] 4.2 实现官方服务商应用服务
     【目标对象】`app/application/admin/`
     【修改目的】编排官方服务商管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】AdminLLMService, AuditLogService
     【修改内容】
        - 实现 AdminLLMAppService
          * create_official_provider(provider_config, admin_id) -> ProviderDTO
            - 创建官方服务商
            - 记录审计日志
          * update_official_provider(provider_id, provider_config, admin_id) -> ProviderDTO
            - 更新官方服务商
            - 处理密钥掩码
            - 记录审计日志
          * delete_official_provider(provider_id, admin_id)
            - 删除官方服务商
            - 记录审计日志
          * list_official_providers(filters, page, size) -> Page[ProviderDTO]
            - 查询官方服务商列表
            - 分页和排序
          * get_provider(provider_id) -> ProviderDTO
            - 获取服务商详情
          * get_provider_audit_logs(provider_id, page, size) -> Page[AuditLogDTO]
            - 获取服务商操作日志

- [ ] 4.3 实现工具审核应用服务
     【目标对象】`app/application/admin/`
     【修改目的】编排工具审核相关的用例
     【修改方式】实现应用服务
     【相关依赖】AdminToolService, AuditLogService
     【修改内容】
        - 实现 AdminToolAppService
          * submit_tool_for_audit(tool_data, user_id) -> ToolAuditRecordDTO
            - 提交工具审核申请
          * start_review(record_id, admin_id) -> ToolAuditRecordDTO
            - 开始审核工具
            - 锁定审核记录 (防止多人同时审核)
          * approve_audit(record_id, comment, admin_id) -> ToolAuditRecordDTO
            - 审核通过
            - 发布为官方工具
            - 记录审计日志
          * reject_audit(record_id, comment, admin_id) -> ToolAuditRecordDTO
            - 审核拒绝
            - 提供审核意见
            - 记录审计日志
          * cancel_audit(record_id, user_id)
            - 取消审核申请
          * get_pending_audits(admin_id, page, size) -> Page[ToolAuditRecordDTO]
            - 获取待审核列表
          * get_audit_records(admin_id, page, size) -> Page[ToolAuditRecordDTO]
            - 获取审核历史记录
          * get_audit_record(record_id) -> ToolAuditRecordDTO
            - 获取审核记录详情
          * get_audit_history(tool_id) -> List[ToolAuditRecordDTO]
            - 获取工具审核历史

- [ ] 4.4 实现官方工具应用服务
     【目标对象】`app/application/admin/`
     【修改目的】编排官方工具管理相关的用例
     【修改方式】实现应用服务
     【相关依赖】OfficialToolService, AuditLogService
     【修改内容】
        - 实现 OfficialToolAppService
          * get_official_tools(filters, page, size) -> Page[ToolDTO]
            - 查询官方工具列表
            - 分页和过滤
          * update_official_tool(tool_id, tool_data, admin_id) -> ToolDTO
            - 更新官方工具
            - 记录审计日志
          * disable_official_tool(tool_id, admin_id)
            - 禁用官方工具
            - 记录审计日志
          * enable_official_tool(tool_id, admin_id)
            - 启用官方工具
            - 记录审计日志
          * delete_official_tool(tool_id, admin_id)
            - 删除官方工具
            - 记录审计日志
          * get_tool_audit_logs(tool_id, page, size) -> Page[AuditLogDTO]
            - 获取工具操作日志

- [ ] 4.5 实现审计日志应用服务
     【目标对象】`app/application/admin/`
     【修改目的】编排审计日志查询相关的用例
     【修改方式】实现应用服务
     【相关依赖】AuditLogService
     【修改内容】
        - 实现 AuditLogAppService
          * get_admin_logs(admin_id, page, size) -> Page[AuditLogDTO]
            - 查询管理员操作日志
          * get_resource_logs(resource_type, resource_id, page, size) -> Page[AuditLogDTO]
            - 查询资源操作日志
          * get_logs_by_timerange(start_time, end_time, page, size) -> Page[AuditLogDTO]
            - 按时间范围查询日志
          * search_logs(keyword, page, size) -> Page[AuditLogDTO]
            - 搜索日志
          * export_logs(format, filters, admin_id) -> ExportFileDTO
            - 导出审计日志
          * get_action_types() -> List[str]
            - 获取所有操作类型
          * get_resource_types() -> List[str]
            - 获取所有资源类型

- [ ] 4.6 实现管理后台配置服务
     【目标对象】`app/application/admin/`
     【修改目的】管理后台配置
     【修改方式】使用配置中心
     【相关依赖】无
     【修改内容】
        - 实现 AdminConfigService
          * get_audit_log_retention_days() -> int
            - 审计日志保留天数
          * get_max_upload_size() -> int
            - 工具上传最大大小
          * get_audit_timeout() -> int
            - 审核超时时间
          * is_auto_audit_enabled() -> bool
            - 是否启用自动审核
          * get_required_approval_level() -> AdminRole
            - 获取需要的审批级别

### 5. API 路由层

- [ ] 5.1 创建管理员用户管理 API 路由
     【目标对象】`app/api/v1/admin/users/`
     【修改目的】暴露管理员用户管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AdminUserAppService
     【修改内容】
        - `POST /api/v1/admin/users` - 创建管理员
          * 请求:AdminUserCreateRequest
          * 响应:AdminUserDTO
          * 权限:SUPER_ADMIN 或 ADMIN
        - `GET /api/v1/admin/users` - 获取管理员列表
          * 参数:role, page, size
          * 响应:Page[AdminUserDTO]
          * 权限:ADMIN
        - `GET /api/v1/admin/users/{admin_id}` - 获取管理员详情
          * 响应:AdminUserDTO
          * 权限:ADMIN
        - `PUT /api/v1/admin/users/{admin_id}/role` - 更新管理员角色
          * 请求:{role: str}
          * 响应:AdminUserDTO
          * 权限:SUPER_ADMIN
        - `PUT /api/v1/admin/users/{admin_id}/permissions` - 更新管理员权限
          * 请求:{permissions: List[str]}
          * 响应:AdminUserDTO
          * 权限:SUPER_ADMIN
        - `POST /api/v1/admin/users/{admin_id}/deactivate` - 停用管理员
          * 权限:SUPER_ADMIN
        - `DELETE /api/v1/admin/users/{admin_id}` - 删除管理员
          * 权限:SUPER_ADMIN

- [ ] 5.2 创建官方服务商管理 API 路由
     【目标对象】`app/api/v1/admin/providers/`
     【修改目的】暴露官方服务商管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AdminLLMAppService
     【修改内容】
        - `POST /api/v1/admin/providers` - 创建官方服务商
          * 请求:ProviderCreateRequest
          * 响应:ProviderDTO
          * 权限:ADMIN
        - `GET /api/v1/admin/providers` - 获取官方服务商列表
          * 参数:type, status, page, size
          * 响应:Page[ProviderDTO]
          * 权限:ALL (所有用户可查)
        - `GET /api/v1/admin/providers/{provider_id}` - 获取服务商详情
          * 响应:ProviderDTO
          * 权限:ALL
        - `PUT /api/v1/admin/providers/{provider_id}` - 更新官方服务商
          * 请求:ProviderUpdateRequest
          * 响应:ProviderDTO
          * 权限:ADMIN
        - `DELETE /api/v1/admin/providers/{provider_id}` - 删除官方服务商
          * 权限:SUPER_ADMIN
        - `GET /api/v1/admin/providers/{provider_id}/logs` - 获取操作日志
          * 参数:page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN

- [ ] 5.3 创建工具审核 API 路由
     【目标对象】`app/api/v1/admin/tools/audit/`
     【修改目的】暴露工具审核的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AdminToolAppService
     【修改内容】
        - `POST /api/v1/admin/tools/audit` - 提交工具审核申请
          * 请求:ToolAuditSubmitRequest
          * 响应:ToolAuditRecordDTO
          * 权限:AUTHENTICATED_USER
        - `GET /api/v1/admin/tools/audit/pending` - 获取待审核列表
          * 参数:page, size
          * 响应:Page[ToolAuditRecordDTO]
          * 权限:AUDITOR
        - `GET /api/v1/admin/tools/audit/records` - 获取审核记录列表
          * 参数:status, page, size
          * 响应:Page[ToolAuditRecordDTO]
          * 权限:AUDITOR
        - `GET /api/v1/admin/tools/audit/{record_id}` - 获取审核记录详情
          * 响应:ToolAuditRecordDTO
          * 权限:AUDITOR
        - `POST /api/v1/admin/tools/audit/{record_id}/start` - 开始审核
          * 权限:AUDITOR
        - `POST /api/v1/admin/tools/audit/{record_id}/approve` - 审核通过
          * 请求:{comment: str}
          * 响应:ToolAuditRecordDTO
          * 权限:AUDITOR
        - `POST /api/v1/admin/tools/audit/{record_id}/reject` - 审核拒绝
          * 请求:{comment: str}
          * 响应:ToolAuditRecordDTO
          * 权限:AUDITOR
        - `POST /api/v1/admin/tools/audit/{record_id}/cancel` - 取消审核
          * 权限:APPLICANT
        - `GET /api/v1/admin/tools/audit/tool/{tool_id}/history` - 获取审核历史
          * 响应:List[ToolAuditRecordDTO]
          * 权限:ADMIN

- [ ] 5.4 创建官方工具管理 API 路由
     【目标对象】`app/api/v1/admin/tools/official/`
     【修改目的】暴露官方工具管理的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】OfficialToolAppService
     【修改内容】
        - `GET /api/v1/admin/tools/official` - 获取官方工具列表
          * 参数:type, status, page, size
          * 响应:Page[ToolDTO]
          * 权限:ALL
        - `GET /api/v1/admin/tools/official/{tool_id}` - 获取工具详情
          * 响应:ToolDTO
          * 权限:ALL
        - `PUT /api/v1/admin/tools/official/{tool_id}` - 更新官方工具
          * 请求:ToolUpdateRequest
          * 响应:ToolDTO
          * 权限:ADMIN
        - `POST /api/v1/admin/tools/official/{tool_id}/disable` - 禁用工具
          * 权限:ADMIN
        - `POST /api/v1/admin/tools/official/{tool_id}/enable` - 启用工具
          * 权限:ADMIN
        - `DELETE /api/v1/admin/tools/official/{tool_id}` - 删除工具
          * 权限:SUPER_ADMIN
        - `GET /api/v1/admin/tools/official/{tool_id}/logs` - 获取操作日志
          * 参数:page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN

- [ ] 5.5 创建审计日志 API 路由
     【目标对象】`app/api/v1/admin/logs/`
     【修改目的】暴露审计日志查询的 HTTP API
     【修改方式】使用 FastAPI 创建路由
     【相关依赖】AuditLogAppService
     【修改内容】
        - `GET /api/v1/admin/logs` - 获取审计日志列表
          * 参数:admin_id, action_type, resource_type, page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/resource/{resource_type}/{resource_id}` - 获取资源操作日志
          * 参数:page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/timerange` - 按时间范围查询日志
          * 参数:start_time, end_time, page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/search` - 搜索日志
          * 参数:keyword, page, size
          * 响应:Page[AuditLogDTO]
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/export` - 导出日志
          * 参数:format, filters
          * 响应:文件下载
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/action-types` - 获取操作类型列表
          * 响应:List[str]
          * 权限:ADMIN
        - `GET /api/v1/admin/logs/resource-types` - 获取资源类型列表
          * 响应:List[str]
          * 权限:ADMIN

### 6. 基础设施层

- [ ] 6.1 实现管理后台配置
     【目标对象】`app/infrastructure/config/`
     【修改目的】配置管理后台运行参数
     【修改方式】使用配置文件
     【相关依赖】无
     【修改内容】
        - admin.enabled - 是否启用管理后台
        - admin.audit.log_retention_days - 审计日志保留天数
        - admin.audit.auto_cleanup - 是否自动清理日志
        - admin.tool.max_upload_size - 工具上传最大大小 (字节)
        - admin.tool.audit_timeout - 审核超时时间 (小时)
        - admin.tool.auto_audit_enabled - 是否启用自动审核
        - admin.permission.cache_enabled - 是否缓存权限
        - admin.permission.cache_ttl - 权限缓存 TTL(秒)

- [ ] 6.2 实现定时任务清理
     【目标对象】`app/infrastructure/scheduler/`
     【修改目的】定期清理过期的审计日志
     【修改方式】使用 APScheduler
     【相关依赖】APScheduler, AuditLogRepository
     【修改内容】
        - 创建定时任务
          * 每天凌晨 3 点执行
          * 清理 N 天前的审计日志
          * N 由配置决定
        - 配置任务参数:
          * misfire_grace_time
          * coalesce

### 7. 中间件和权限验证

- [ ] 7.1 实现管理员权限验证中间件
     【目标对象】`app/api/middleware/admin_auth.py`
     【修改目的】验证管理员权限
     【修改方式】实现 FastAPI 中间件
     【相关依赖】FastAPI, AdminPermissionService
     【修改内容】
        - 创建 AdminAuthMiddleware 类
          * _permission_service: AdminPermissionService
        - 实现方法:
          * __call__(request, call_next)
            - 从请求头获取管理员 ID
            - 验证管理员身份
            - 验证所需权限
            - 记录访问日志
            - 调用下一个中间件或路由
        - 权限注解:
          * @require_role(role) - 需要特定角色
          * @require_permission(permission) - 需要特定权限
          * @require_any_permission(permissions) - 需要任一权限

- [ ] 7.2 实现操作审计切面
     【目标对象】`app/api/middleware/audit_aspect.py`
     【修改目的】自动记录管理员操作日志
     【修改方式】使用 AOP 切面编程
     【相关依赖】AuditLogService
     【修改内容】
        - 创建 AuditAspect 类
          * _log_service: AuditLogService
        - 实现方法:
          * around_management_method(func, admin_id, args, kwargs)
            - 记录方法调用前
            - 执行方法
            - 记录方法调用后
            - 捕获异常并记录
            - 异步写入审计日志
        - 审计注解:
          * @audit_log(action_type, resource_type) - 自动记录操作

### 8. 测试

- [ ] 8.1 编写单元测试
     【目标对象】`tests/test_admin_service.py`
     【修改目的】确保管理后台功能正确性
     【修改方式】使用 pytest
     【相关依赖】AdminUserAppService, AdminToolAppService
     【修改内容】
        - 测试管理员创建和权限分配
        - 测试权限验证逻辑
        - 测试官方服务商 CRUD
        - 测试工具审核流程
        - 测试审计日志记录
        - 测试密钥掩码处理
        - 测试越权操作拦截

- [ ] 8.2 编写集成测试
     【目标对象】`tests/integration/test_admin_api.py`
     【修改目的】确保管理后台 API 端到端正常工作
     【修改方式】使用 FastAPI TestClient
     【相关依赖】FastAPI, AdminUserAppService
     【修改内容】
        - 测试管理员管理 API
        - 测试官方服务商管理 API
        - 测试工具审核 API
        - 测试审计日志查询 API
        - 测试权限验证中间件
        - 测试完整审核流程

- [ ] 8.3 编写安全测试
     【目标对象】`tests/security/test_admin_security.py`
     【修改目的】测试管理后台安全性
     【修改方式】使用 pytest
     【相关依赖】AdminPermissionService
     【修改内容】
        - 测试越权访问
        - 测试未授权访问
        - 测试密钥泄露防护
        - 测试 SQL 注入防护
        - 测试 XSS 攻击防护
        - 测试 CSRF 防护

### 9. 监控和日志

- [ ] 9.1 实现管理后台监控指标
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控管理后台运行状态
     【修改方式】使用 Prometheus 指标
     【相关依赖】prometheus_client
     【修改内容】
        - 定义管理员操作指标 Counter
          * admin_actions_total - 管理员操作总次数
          * admin_actions_by_type - 按类型分类的操作次数
          * admin_action_failures_total - 失败次数
        - 定义审核指标 Gauge/Histogram
          * tool_audits_pending - 待审核数量
          * tool_audit_duration_seconds - 审核时长
          * tool_audit_pass_rate - 通过率
        - 定义审计日志指标
          * audit_logs_created_total - 创建的日志数量
          * audit_logs_stored_bytes - 存储的日志大小

- [ ] 9.2 实现管理后台日志记录
     【目标对象】`app/infrastructure/logging/`
     【修改目的】记录管理后台运行日志
     【修改方式】使用结构化日志
     【相关依赖】loguru
     【修改内容】
        - 管理员登录/登出日志
        - 权限验证日志
        - 管理操作日志
        - 审核操作日志
        - 错误日志
        - 安全日志

### 10. 错误处理

- [ ] 10.1 定义管理后台异常
     【目标对象】`app/core/exceptions/`
     【修改目的】定义管理后台相关异常
     【修改方式】自定义异常类
     【相关依赖】无
     【修改内容】
        - AdminUserNotFoundException (404)
          * 管理员不存在时抛出
        - InsufficientPermissionException (403)
          * 权限不足时抛出
        - InvalidAuditStateException (400)
          * 审核状态不合法时抛出
        - AuditAlreadyCompletedException (400)
          * 审核已完成时抛出
        - SecretKeyMaskInvalidException (400)
          * 密钥掩码无效时抛出
        - ResourceNotFoundException (404)
          * 资源不存在时抛出

- [ ] 10.2 实现错误处理中间件
     【目标对象】`app/api/middleware/`
     【修改目的】统一处理管理后台错误
     【修改方式】实现 FastAPI 中间件
     【相关依赖】FastAPI
     【修改内容】
        - 捕获 InsufficientPermissionException
          * 返回 403 错误响应
        - 捕获 InvalidAuditStateException
          * 返回 400 错误响应和当前状态
        - 捕获所有管理后台异常
          * 记录详细错误日志
          * 返回统一的错误格式

### 11. 性能优化

- [ ] 11.1 实现权限缓存
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升权限验证性能
     【修改方式】使用 Redis 缓存
     【相关依赖】Redis
     【修改内容】
        - 缓存管理员权限信息
        - 缓存角色权限映射
        - 实现缓存刷新机制
        - 实现缓存预热

- [ ] 11.2 实现批量操作
     【目标对象】`app/application/admin/`
     【修改目的】支持批量审核和管理操作
     【修改方式】批量处理
     【相关依赖】无
     【修改内容】
        - 批量审核工具
        - 批量更新服务商
        - 批量删除资源
        - 批量导出日志

- [ ] 11.3 实现查询优化
     【目标对象】`app/domain/admin/repository.py`
     【修改目的】优化审计日志查询性能
     【修改方式】数据库索引 + 游标分页 + 覆盖索引
     【相关依赖】SQLAlchemy
     【修改内容】
        - 添加复合索引：
          * idx_audit_logs_admin_created (admin_user_id, created_at DESC)
          * idx_audit_logs_action_resource (action_type, resource_type, resource_id)
          * idx_audit_logs_timerange (created_at DESC) INCLUDE (id, action_type, resource_type)
        - 使用覆盖索引减少回表查询
        - 实现游标分页（基于 keyset pagination，避免 offset 性能问题）
        - 避免全表扫描

### 12. 监控与告警

- [ ] 12.1 实现管理后台监控指标
     【目标对象】`app/infrastructure/monitoring/`
     【修改目的】监控管理后台运行状态
     【修改方式】使用 Prometheus 指标 + Grafana 仪表盘
     【相关依赖】prometheus_client, Grafana
     【修改内容】
        - 定义管理员操作指标 Counter
          * admin_actions_total{action_type, admin_id, status} - 管理员操作总次数
          * admin_action_duration_seconds_bucket{action_type} - 操作耗时直方图
          * admin_action_failures_total{action_type, error_code} - 失败次数
        - 定义审核指标 Gauge/Histogram
          * tool_audits_pending{status} - 待审核数量
          * tool_audit_duration_seconds_bucket - 审核时长直方图
          * tool_audit_pass_rate{auditor_id} - 审核通过率
          * tool_audit_reject_reasons_total{reason} - 拒绝原因分布
        - 定义审计日志指标
          * audit_logs_created_total{day} - 创建的日志数量
          * audit_logs_stored_bytes - 存储的日志大小
          * audit_logs_search_duration_seconds_bucket - 搜索耗时
        - 定义权限验证指标
          * admin_permission_checks_total{result} - 权限验证次数
          * admin_permission_cache_hit_ratio - 缓存命中率

- [ ] 12.2 实现管理后台日志记录
     【目标对象】`app/infrastructure/logging/`
     【修改目的】记录管理后台运行日志
     【修改方式】使用结构化日志 + 日志收集
     【相关依赖】loguru, Loki 或 ELK
     【修改内容】
        - 管理员登录/登出日志（包含 IP、设备指纹、地理位置）
        - 权限验证日志（成功/失败、权限类型）
        - 管理操作日志（操作类型、资源 ID、变更详情）
        - 审核操作日志（审核 ID、审核决策、审核意见）
        - 错误日志（堆栈跟踪、请求上下文）
        - 安全日志（异常登录、越权尝试、暴力破解）
        - 日志格式：JSON 结构化，包含 trace_id、span_id
        - 日志收集：Filebeat -> Loki/ELK，支持实时检索

- [ ] 12.3 实现告警规则
     【目标对象】`ops/monitoring/alerts/`
     【修改目的】异常情况及时通知
     【修改方式】Prometheus AlertManager 规则
     【相关依赖】AlertManager
     【修改内容】
        - 待审核工具超过阈值（>50 持续 1 小时）-> 通知审核员
        - 审核超时超过阈值（>24 小时）-> 通知管理员
        - 官方服务商标记为不健康（连续 3 次调用失败）-> 通知运维
        - 权限验证失败率突增（5 分钟内 > 10%）-> 通知安全团队
        - 审计日志写入失败 -> 通知运维
        - 管理员异地登录（IP 归属地异常）-> 通知管理员本人
        - 告警渠道：邮件、钉钉、企业微信、PagerDuty

### 13. 安全加固

- [ ] 13.1 实现双因素认证（2FA）
     【目标对象】`app/api/v1/admin/auth/`
     【修改目的】增强管理员登录安全
     【修改方式】TOTP（Time-based One-Time Password）
     【相关依赖】pyotp
     【修改内容】
        - 管理员首次登录强制绑定 TOTP（Google Authenticator / Microsoft Authenticator）
        - 生成 TOTP Secret（32 位 Base32 编码），二维码展示
        - 登录时验证 TOTP 验证码（6 位数字，30 秒有效）
        - 备用验证码（10 个一次性验证码，防止手机丢失）
        - 敏感操作二次验证（删除、批量审核、权限变更）
        - 2FA 豁免：受信任设备（30 天内免验证）

- [ ] 13.2 实现 IP 白名单
     【目标对象】`app/api/middleware/admin_ip_whitelist.py`
     【修改目的】限制管理员登录 IP 范围
     【修改方式】中间件 IP 过滤
     【相关依赖】FastAPI, ipaddress
     【修改内容】
        - 支持 IPv4/IPv6 地址段配置（CIDR 格式）
        - 支持多个白名单 IP 段（例：192.168.1.0/24, 10.0.0.0/8）
        - 支持动态更新白名单（Redis 缓存，TTL 永不过期）
        - IP 不在白名单时拒绝访问（403 Forbidden）
        - 例外：SUPER_ADMIN 不受 IP 限制（紧急情况下使用）

- [ ] 13.3 实现审计日志防篡改
     【目标对象】`app/domain/admin/service.py`
     【修改目的】确保审计日志不可篡改
     【修改方式】append-only 表 + 哈希链
     【相关依赖】SQLAlchemy, hashlib
     【修改内容】
        - 审计日志表禁止 UPDATE/DELETE 操作（数据库权限控制）
        - 每条日志包含 prev_log_hash 字段（上一条日志的 SHA-256 哈希）
        - 第一条日志的 prev_log_hash 为全 0
        - 验证日志完整性：遍历日志链，重新计算哈希比对
        - 定期（每天）将日志哈希链根哈希上链（可选：区块链存证）
        - 日志归档时保持哈希链连续性

- [ ] 13.4 实现会话管理
     【目标对象】`app/api/v1/admin/sessions/`
     【修改目的】管理管理员登录会话
     【修改方式】Redis Session + JWT 黑名单
     【相关依赖】Redis, PyJWT
     【修改内容】
        - JWT Token 有效期 2 小时，Refresh Token 有效期 7 天
        - 登出时将 Token 加入 Redis 黑名单（TTL = Token 剩余有效期）
        - 支持强制下线（删除 Session + 加入黑名单）
        - 支持查看活跃会话（设备信息、登录时间、最后活跃时间）
        - 支持单管理员最多 N 个并发会话（默认 5 个）

### 14. 数据归档与清理

- [ ] 14.1 实现审计日志归档
     【目标对象】`app/infrastructure/archiver/`
     【修改目的】将冷数据迁移到低成本存储
     【修改方式】定时任务 + S3 存储
     【相关依赖】APScheduler, boto3
     【修改内容】
        - 热数据：90 天内的审计日志存 PostgreSQL
        - 冷数据：>90 天的日志自动迁移到 S3（Glacier 存储类别）
        - 归档格式：Parquet（列式存储，压缩比高）
        - 归档文件命名：audit_logs_{date}_{sequence}.parquet
        - 归档后可查询：S3 Select 或 Athena 查询
        - 保留策略：至少保留 2 年，到期自动删除

- [ ] 14.2 实现定时清理
     【目标对象】`app/infrastructure/scheduler/`
     【修改目的】定期清理过期数据
     【修改方式】APScheduler 定时任务
     【相关依赖】APScheduler
     【修改内容】
        - 每天凌晨 3 点执行清理任务
        - 清理 >2 年的审计日志（先归档再删除）
        - 清理 >30 天的临时文件（上传的工具包、截图等）
        - 清理 >7 天的审核草稿（未提交的审核申请）
        - 清理黑名单过期的 Token（WHERE 条件必须走索引）
        - 审计日志分区表（按月分区，自动创建新分区）

- [ ] 11.4 实现全文搜索
     【目标对象】`app/infrastructure/search/`
     【修改目的】支持审计日志全文搜索
     【修改方式】pg_trgm 或 Elasticsearch
     【相关依赖】PostgreSQL pg_trgm 扩展 或 elasticsearch-py
     【修改内容】
        - 方案 A（pg_trgm）：
          * 启用 pg_trgm 扩展
          * 创建 gin 索引：CREATE INDEX idx_audit_logs_search ON audit_logs USING gin (action_details gin_trgm_ops)
          * 支持模糊搜索：WHERE action_details ILIKE '%keyword%'
        - 方案 B（Elasticsearch）：
          * 审计日志同步到 ES（Logstash 或 CDC）
          * ES 索引配置：analyzer 使用 ik_max_word（中文分词）
          * 支持复杂查询：多字段匹配、高亮显示、聚合统计
        - 搜索性能目标：百万级数据 < 1s 返回

- [ ] 11.5 实现热点数据预热
     【目标对象】`app/infrastructure/cache/`
     【修改目的】提升高频访问数据的响应速度
     【修改方式】定时任务 + 事件驱动
     【相关依赖】APScheduler, Redis
     【修改内容】
        - 官方服务商列表缓存（TTL 300 秒，变更时主动失效）
        - 待审核工具列表缓存（TTL 60 秒）
        - 管理员权限缓存（登录时预热，权限变更时失效）
        - 审计日志统计缓存（每小时更新一次）
