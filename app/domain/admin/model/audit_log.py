from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(String(100), unique=True, nullable=False, index=True)
    admin_user_id = Column(Integer, nullable=False, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(100), nullable=False)
    resource_id = Column(String(100), nullable=False)
    action_details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    prev_log_hash = Column(String(64), nullable=True)  # SHA-256 hash of previous log
    
    # Indexes
    __table_args__ = (
        Index('idx_admin_user_id', 'admin_user_id'),
        Index('idx_action_type', 'action_type'),
        Index('idx_created_at', 'created_at'),
        Index('idx_audit_logs_admin_created', 'admin_user_id', 'created_at'),
        Index('idx_audit_logs_action_resource', 'action_type', 'resource_type', 'resource_id'),
        Index('idx_audit_logs_timerange', 'created_at'),
    )
