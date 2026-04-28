from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base

class ToolAuditRecord(Base):
    __tablename__ = "tool_audit_records"
    
    id = Column(Integer, primary_key=True, index=True)
    record_id = Column(String(100), unique=True, nullable=False, index=True)
    tool_id = Column(String(100), nullable=False, index=True)
    applicant_user_id = Column(Integer, nullable=False)
    auditor_admin_id = Column(Integer, nullable=True, index=True)
    audit_status = Column(String(50), nullable=False, index=True)  # PENDING, IN_REVIEW, APPROVED, REJECTED, CANCELLED
    audit_comment = Column(Text, nullable=True)
    submitted_data = Column(Text, nullable=False)  # JSON string of tool data
    audited_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_tool_id', 'tool_id'),
        Index('idx_auditor_admin_id', 'auditor_admin_id'),
        Index('idx_audit_status', 'audit_status'),
    )
