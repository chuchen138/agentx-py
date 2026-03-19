from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON, Index
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base
from app.domain.file.file_type import FileType
from app.domain.file.storage_backend_type import StorageBackendType


class FileRecord(Base):
    """文件记录模型"""
    __tablename__ = "file_records"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    file_type = Column(String, nullable=False, default=FileType.GENERAL.value)
    original_filename = Column(String, nullable=False)
    stored_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_url = Column(String, nullable=False, unique=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    storage_backend = Column(String, nullable=False, default=StorageBackendType.LOCAL.value)
    version = Column(Integer, nullable=False, default=1)
    file_metadata = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # 索引
    __table_args__ = (
        Index('idx_file_url', 'file_url'),
        Index('idx_user_id', 'user_id'),
        Index('idx_file_type', 'file_type'),
    )

    # 关联
    # user = relationship("User", back_populates="files")
