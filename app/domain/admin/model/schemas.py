from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Set

# AdminUser schemas
class AdminUserBase(BaseModel):
    user_id: int
    username: str
    role: str

class AdminUserCreateRequest(AdminUserBase):
    pass

class AdminUserUpdateRequest(BaseModel):
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None

class AdminUserDTO(AdminUserBase):
    id: int
    permissions: Optional[List[str]] = None
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# AuditLog schemas
class AuditLogBase(BaseModel):
    action_type: str
    resource_type: str
    resource_id: str
    action_details: Optional[str] = None
    ip_address: Optional[str] = None

class AuditLogCreateRequest(AuditLogBase):
    admin_user_id: int

class AuditLogDTO(AuditLogBase):
    id: int
    log_id: str
    admin_user_id: int
    created_at: datetime
    prev_log_hash: Optional[str] = None
    
    class Config:
        from_attributes = True

class AuditLogListRequest(BaseModel):
    admin_id: Optional[int] = None
    action_type: Optional[str] = None
    resource_type: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    page: int = 1
    size: int = 20

# ToolAuditRecord schemas
class ToolAuditBase(BaseModel):
    tool_id: str
    submitted_data: str

class ToolAuditSubmitRequest(ToolAuditBase):
    pass

class ToolAuditApproveRequest(BaseModel):
    comment: str

class ToolAuditRecordDTO(BaseModel):
    id: int
    record_id: str
    tool_id: str
    applicant_user_id: int
    auditor_admin_id: Optional[int] = None
    audit_status: str
    audit_comment: Optional[str] = None
    submitted_data: str
    audited_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# AdminListRequest
class AdminListRequest(BaseModel):
    role: Optional[str] = None
    page: int = 1
    size: int = 20
