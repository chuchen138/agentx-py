from sqlalchemy import Column, String, Boolean, Integer, DateTime, JSON, Index, ForeignKey
from sqlalchemy.orm import declarative_base
import uuid
from datetime import datetime

Base = declarative_base()


class RuleEntity(Base):
    """规则实体"""
    __tablename__ = "rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False, index=True)
    handler_key = Column(String(100), nullable=False, index=True)
    description = Column(String(500))
    config = Column(JSON, nullable=False, default=dict)
    enabled = Column(Boolean, default=True, index=True)
    priority = Column(Integer, default=0, comment="优先级，越高越优先")
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100), comment="最后更新人邮箱")
    
    # 索引
    __table_args__ = (
        Index('idx_handler_key_version', 'handler_key', 'version'),
        Index('idx_enabled_priority', 'enabled', 'priority'),
    )
    
    def dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "handler_key": self.handler_key,
            "description": self.description,
            "config": self.config,
            "enabled": self.enabled,
            "priority": self.priority,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "updated_by": self.updated_by
        }


class RuleVersionEntity(Base):
    """规则版本快照"""
    __tablename__ = "rule_versions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), ForeignKey("rules.id"), nullable=False)
    version = Column(Integer, nullable=False)
    snapshot = Column(JSON, nullable=False, comment="规则完整快照")
    changed_by = Column(String(100))
    changed_at = Column(DateTime, default=datetime.utcnow)
    change_reason = Column(String(500))


class RuleAuditLogEntity(Base):
    """审计日志"""
    __tablename__ = "rule_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String(36), nullable=False, index=True)
    action = Column(String(50), nullable=False)  # CREATE/UPDATE/DELETE/EXECUTE
    old_value = Column(JSON, comment="修改前的值")
    new_value = Column(JSON, comment="修改后的值")
    operator = Column(String(100), nullable=False)
    operated_at = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String(45))
