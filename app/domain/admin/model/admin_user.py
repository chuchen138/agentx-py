from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.sql import func
from app.core.database import Base

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=False, index=True)
    role = Column(String(50), nullable=False, index=True)  # SUPER_ADMIN, ADMIN, AUDITOR
    permissions = Column(String(500), nullable=True)  # JSON string of permissions
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_user_id', 'user_id'),
        Index('idx_role', 'role'),
        Index('idx_is_active', 'is_active'),
    )
