from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime
from app.core.database import Base
from app.domain.user.model import UUID
from app.domain.tool.enums import ToolType, UploadType, ToolStatus


class ToolEntity(Base):
    __tablename__ = "tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    icon = Column(String(255), nullable=True)
    subtitle = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    labels = Column(JSON, nullable=True, default=[])
    tool_type = Column(String(50), nullable=False, default=ToolType.MCP.value)
    upload_type = Column(String(50), nullable=False, default=UploadType.GITHUB.value)
    upload_url = Column(String(500), nullable=False, index=True)
    install_command = Column(JSON, nullable=True)
    tool_list = Column(JSON, nullable=True, default=[])
    status = Column(String(50), nullable=False, default=ToolStatus.WAITING_REVIEW.value, index=True)
    is_office = Column(Boolean, nullable=False, default=False)
    reject_reason = Column(Text, nullable=True)
    failed_step_status = Column(String(50), nullable=True)
    mcp_server_name = Column(String(255), nullable=True)
    is_global = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("UserModel", backref="tools")
    versions = relationship("ToolVersionEntity", back_populates="tool", cascade="all, delete-orphan")
    user_tools = relationship("UserToolEntity", back_populates="tool", cascade="all, delete-orphan")


class ToolVersionEntity(Base):
    __tablename__ = "tool_versions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    version_number = Column(String(50), nullable=False)
    config = Column(JSON, nullable=True)
    status = Column(String(50), nullable=False, default="DRAFT")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    tool = relationship("ToolEntity", back_populates="versions")


class UserToolEntity(Base):
    __tablename__ = "user_tools"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(UUID, ForeignKey("users.id"), nullable=False, index=True)
    tool_id = Column(Integer, ForeignKey("tools.id"), nullable=False, index=True)
    installed_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("UserModel", backref="user_tools")
    tool = relationship("ToolEntity", back_populates="user_tools")