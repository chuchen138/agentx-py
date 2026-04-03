from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from .model import RuleEntity, RuleVersionEntity, RuleAuditLogEntity
from .repository import RuleRepository
from .handler import RuleContext, RuleResult, auto_discover_handlers
from .factory import RuleHandlerFactory
from .exceptions import RuleExecutionError, RuleValidationError
from .validator import RuleValidator
from app.infrastructure.cache.rule_cache import rule_cache


class RuleDomainService:
    """规则领域服务"""
    
    def __init__(self):
        self.repository = RuleRepository()
        # 自动发现并注册处理器
        auto_discover_handlers()
    
    async def create_rule(
        self,
        name: str,
        handler_key: str,
        description: Optional[str],
        config: Dict[str, Any],
        priority: int,
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> RuleEntity:
        """创建规则"""
        # 验证配置安全性
        RuleValidator.validate_config(config)
        
        # 检查处理器是否存在
        try:
            RuleHandlerFactory.get_handler(handler_key)
        except RuleExecutionError:
            raise RuleValidationError(f"Invalid handler_key: {handler_key}")
        
        # 创建规则实体
        rule = RuleEntity(
            name=name,
            handler_key=handler_key,
            description=description,
            config=config,
            priority=priority,
            updated_by=operator
        )
        
        # 保存规则
        created_rule = await self.repository.create(rule, session)
        
        # 创建审计日志
        audit_log = RuleAuditLogEntity(
            rule_id=created_rule.id,
            action="CREATE",
            new_value=created_rule.dict(),
            operator=operator,
            ip_address=ip_address
        )
        await self.repository.create_audit_log(audit_log, session)
        
        # 创建版本快照
        version = RuleVersionEntity(
            rule_id=created_rule.id,
            version=created_rule.version,
            snapshot=created_rule.dict(),
            changed_by=operator,
            change_reason="Initial creation"
        )
        await self.repository.create_version(version, session)
        
        return created_rule
    
    async def update_rule(
        self,
        rule_id: str,
        name: Optional[str],
        description: Optional[str],
        config: Optional[Dict[str, Any]],
        priority: Optional[int],
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> RuleEntity:
        """更新规则"""
        # 获取现有规则
        existing_rule = await self.repository.get(rule_id, session)
        if not existing_rule:
            raise RuleValidationError(f"Rule not found: {rule_id}")
        
        # 保存旧值用于审计
        old_value = existing_rule.dict()
        
        # 更新字段
        if name is not None:
            existing_rule.name = name
        if description is not None:
            existing_rule.description = description
        if config is not None:
            # 验证配置安全性
            RuleValidator.validate_config(config)
            existing_rule.config = config
        if priority is not None:
            existing_rule.priority = priority
        existing_rule.updated_by = operator
        
        # 保存更新
        updated_rule = await self.repository.update(existing_rule, session)
        
        # 创建审计日志
        audit_log = RuleAuditLogEntity(
            rule_id=updated_rule.id,
            action="UPDATE",
            old_value=old_value,
            new_value=updated_rule.dict(),
            operator=operator,
            ip_address=ip_address
        )
        await self.repository.create_audit_log(audit_log, session)
        
        # 创建版本快照
        version = RuleVersionEntity(
            rule_id=updated_rule.id,
            version=updated_rule.version,
            snapshot=updated_rule.dict(),
            changed_by=operator,
            change_reason="Update"
        )
        await self.repository.create_version(version, session)
        
        # 使缓存失效
        await rule_cache.invalidate(updated_rule.handler_key)
        
        return updated_rule
    
    async def get_rule(self, rule_id: str, session: AsyncSession) -> Optional[RuleEntity]:
        """获取规则详情"""
        return await self.repository.get(rule_id, session)
    
    async def get_rule_by_handler_key(self, handler_key: str, session: AsyncSession) -> Optional[RuleEntity]:
        """根据handler_key获取规则"""
        # 尝试从缓存获取
        cached_rule = await rule_cache.get(handler_key)
        if cached_rule:
            return cached_rule
        
        # 从数据库获取
        rule = await self.repository.get_by_handler_key(handler_key, session)
        if rule:
            # 写入缓存
            await rule_cache.set(handler_key, rule)
        return rule
    
    async def list_rules(
        self,
        session: AsyncSession,
        handler_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 15
    ) -> Dict[str, Any]:
        """查询规则列表"""
        return await self.repository.list(
            handler_key=handler_key,
            enabled=enabled,
            keyword=keyword,
            page=page,
            page_size=page_size,
            session=session
        )
    
    async def delete_rule(
        self,
        rule_id: str,
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> bool:
        """删除规则（软删除）"""
        # 获取现有规则
        existing_rule = await self.repository.get(rule_id, session)
        if not existing_rule:
            return False
        
        # 保存旧值用于审计
        old_value = existing_rule.dict()
        
        # 执行删除
        deleted = await self.repository.delete(rule_id, session)
        
        if deleted:
            # 创建审计日志
            audit_log = RuleAuditLogEntity(
                rule_id=rule_id,
                action="DELETE",
                old_value=old_value,
                operator=operator,
                ip_address=ip_address
            )
            await self.repository.create_audit_log(audit_log, session)
        
        return deleted
    
    async def toggle_rule(
        self,
        rule_id: str,
        enabled: bool,
        reason: Optional[str],
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> RuleEntity:
        """启用/禁用规则"""
        # 获取现有规则
        existing_rule = await self.repository.get(rule_id, session)
        if not existing_rule:
            raise RuleValidationError(f"Rule not found: {rule_id}")
        
        # 保存旧值用于审计
        old_value = existing_rule.dict()
        
        # 更新状态
        existing_rule.enabled = enabled
        existing_rule.updated_by = operator
        
        # 保存更新
        updated_rule = await self.repository.update(existing_rule, session)
        
        # 创建审计日志
        audit_log = RuleAuditLogEntity(
            rule_id=updated_rule.id,
            action="TOGGLE",
            old_value=old_value,
            new_value=updated_rule.dict(),
            operator=operator,
            ip_address=ip_address
        )
        await self.repository.create_audit_log(audit_log, session)
        
        # 创建版本快照
        version = RuleVersionEntity(
            rule_id=updated_rule.id,
            version=updated_rule.version,
            snapshot=updated_rule.dict(),
            changed_by=operator,
            change_reason=reason or f"Toggle to {'enabled' if enabled else 'disabled'}"
        )
        await self.repository.create_version(version, session)
        
        # 使缓存失效
        await rule_cache.invalidate(updated_rule.handler_key)
        
        return updated_rule
    
    async def rollback_rule(
        self,
        rule_id: str,
        version: int,
        reason: str,
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> RuleEntity:
        """回滚到指定版本"""
        # 获取历史版本
        versions = await self.repository.get_versions(rule_id, session)
        target_version = None
        for v in versions:
            if v.version == version:
                target_version = v
                break
        
        if not target_version:
            raise RuleValidationError(f"Version not found: {version}")
        
        # 获取现有规则
        existing_rule = await self.repository.get(rule_id, session)
        if not existing_rule:
            raise RuleValidationError(f"Rule not found: {rule_id}")
        
        # 保存旧值用于审计
        old_value = existing_rule.dict()
        
        # 恢复到目标版本的配置
        snapshot = target_version.snapshot
        existing_rule.name = snapshot.get("name")
        existing_rule.description = snapshot.get("description")
        existing_rule.config = snapshot.get("config", {})
        existing_rule.priority = snapshot.get("priority", 0)
        existing_rule.updated_by = operator
        
        # 保存更新
        updated_rule = await self.repository.update(existing_rule, session)
        
        # 创建审计日志
        audit_log = RuleAuditLogEntity(
            rule_id=updated_rule.id,
            action="ROLLBACK",
            old_value=old_value,
            new_value=updated_rule.dict(),
            operator=operator,
            ip_address=ip_address
        )
        await self.repository.create_audit_log(audit_log, session)
        
        # 创建版本快照
        new_version = RuleVersionEntity(
            rule_id=updated_rule.id,
            version=updated_rule.version,
            snapshot=updated_rule.dict(),
            changed_by=operator,
            change_reason=reason
        )
        await self.repository.create_version(new_version, session)
        
        # 使缓存失效
        await rule_cache.invalidate(updated_rule.handler_key)
        
        return updated_rule
    
    async def execute_rule(
        self,
        rule_id: str,
        context_data: Dict[str, Any],
        operator: str,
        ip_address: Optional[str],
        session: AsyncSession
    ) -> RuleResult:
        """执行规则"""
        # 获取规则
        rule = await self.repository.get(rule_id, session)
        if not rule or not rule.enabled:
            raise RuleExecutionError(
                f"Rule not found or disabled: {rule_id}",
                error_code="RULE_NOT_FOUND"
            )
        
        # 创建执行上下文
        context = RuleContext(**context_data)
        
        # 获取处理器并执行
        handler = RuleHandlerFactory.get_handler(rule.handler_key)
        result = await handler.execute(context, rule.config)
        
        # 创建审计日志
        audit_log = RuleAuditLogEntity(
            rule_id=rule_id,
            action="EXECUTE",
            old_value={"context": context_data},
            new_value={"result": result.dict()},
            operator=operator,
            ip_address=ip_address
        )
        await self.repository.create_audit_log(audit_log, session)
        
        return result
    
    async def get_rule_versions(self, rule_id: str, session: AsyncSession) -> List[RuleVersionEntity]:
        """获取规则历史版本"""
        return await self.repository.get_versions(rule_id, session)
