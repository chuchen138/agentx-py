from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc
from .model import RuleEntity, RuleVersionEntity, RuleAuditLogEntity
from .exceptions import ConcurrencyError


class RuleRepository:
    """规则仓库"""
    
    async def create(self, rule: RuleEntity, session: AsyncSession) -> RuleEntity:
        """创建规则"""
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        return rule
    
    async def get(self, rule_id: str, session: AsyncSession) -> Optional[RuleEntity]:
        """根据ID获取规则"""
        result = await session.execute(
            select(RuleEntity).where(RuleEntity.id == rule_id)
        )
        return result.scalars().first()
    
    async def get_by_handler_key(self, handler_key: str, session: AsyncSession) -> Optional[RuleEntity]:
        """根据handler_key获取规则（最新且启用的）"""
        result = await session.execute(
            select(RuleEntity)
            .where(RuleEntity.handler_key == handler_key)
            .where(RuleEntity.enabled == True)
            .order_by(desc(RuleEntity.priority), desc(RuleEntity.version))
            .limit(1)
        )
        return result.scalars().first()
    
    async def list(
        self,
        session: AsyncSession,
        handler_key: Optional[str] = None,
        enabled: Optional[bool] = None,
        keyword: Optional[str] = None,
        page: int = 1,
        page_size: int = 15
    ) -> Dict[str, Any]:
        """查询规则列表"""
        query = select(RuleEntity)
        
        # 条件过滤
        if handler_key:
            query = query.where(RuleEntity.handler_key == handler_key)
        if enabled is not None:
            query = query.where(RuleEntity.enabled == enabled)
        if keyword:
            query = query.where(
                RuleEntity.name.ilike(f"%{keyword}%") | 
                RuleEntity.description.ilike(f"%{keyword}%")
            )
        
        # 计算总数
        count_query = select(RuleEntity.id).from_statement(query)
        count_result = await session.execute(count_query)
        total = len(count_result.scalars().all())
        
        # 分页
        offset = (page - 1) * page_size
        query = query.order_by(desc(RuleEntity.priority), desc(RuleEntity.updated_at))
        query = query.offset(offset).limit(page_size)
        
        # 执行查询
        result = await session.execute(query)
        rules = result.scalars().all()
        
        # 转换为字典
        records = [rule.dict() for rule in rules]
        
        return {
            "records": records,
            "current": page,
            "size": page_size,
            "total": total
        }
    
    async def update(self, rule: RuleEntity, session: AsyncSession) -> RuleEntity:
        """更新规则（乐观锁）"""
        # 检查版本号
        existing = await self.get(rule.id, session)
        if existing.version != rule.version:
            raise ConcurrencyError(
                f"Rule version conflict: expected {rule.version}, "
                f"but got {existing.version}"
            )
        
        # 递增版本号
        rule.version = existing.version + 1
        
        # 保存规则
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
        
        return rule
    
    async def delete(self, rule_id: str, session: AsyncSession) -> bool:
        """删除规则（软删除）"""
        result = await session.execute(
            update(RuleEntity)
            .where(RuleEntity.id == rule_id)
            .values(enabled=False)
        )
        await session.commit()
        return result.rowcount > 0
    
    async def create_version(self, version: RuleVersionEntity, session: AsyncSession) -> RuleVersionEntity:
        """创建版本快照"""
        session.add(version)
        await session.commit()
        await session.refresh(version)
        return version
    
    async def get_versions(self, rule_id: str, session: AsyncSession) -> List[RuleVersionEntity]:
        """获取规则历史版本"""
        result = await session.execute(
            select(RuleVersionEntity)
            .where(RuleVersionEntity.rule_id == rule_id)
            .order_by(desc(RuleVersionEntity.version))
        )
        return result.scalars().all()
    
    async def create_audit_log(self, log: RuleAuditLogEntity, session: AsyncSession) -> RuleAuditLogEntity:
        """创建审计日志"""
        session.add(log)
        await session.commit()
        await session.refresh(log)
        return log
