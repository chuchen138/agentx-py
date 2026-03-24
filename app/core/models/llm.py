from sqlalchemy import Column, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Provider(Base):
    """服务商模型"""
    __tablename__ = "llm_providers"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    protocol = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    config = Column(Text, nullable=False)  # 加密存储
    is_official = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # 关系
    models = relationship("Model", back_populates="provider", cascade="all, delete-orphan")


class Model(Base):
    """模型模型"""
    __tablename__ = "llm_models"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(String, nullable=False, index=True)
    provider_id = Column(String, ForeignKey("llm_providers.id"), nullable=False, index=True)
    model_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    model_endpoint = Column(String, nullable=True)
    type = Column(String, nullable=False, index=True)  # CHAT/EMBEDDING
    is_official = Column(Boolean, default=False, nullable=False, index=True)
    status = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # 关系
    provider = relationship("Provider", back_populates="models")
