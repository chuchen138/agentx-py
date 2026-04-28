from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.admin.model.admin_user import AdminUser
from app.domain.admin.model.audit_log import AuditLog
from app.domain.admin.model.tool_audit_record import ToolAuditRecord

# 分页结果类
class PageResult:
    def __init__(self, items: List, total: int, page: int, size: int):
        self.items = items
        self.total = total
        self.page = page
        self.size = size
        self.pages = (total + size - 1) // size

# AdminUserRepository 接口
class AdminUserRepository(ABC):
    @abstractmethod
    def create(self, admin_data: AdminUser) -> AdminUser:
        pass
    
    @abstractmethod
    def get_by_id(self, admin_id: int) -> Optional[AdminUser]:
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> Optional[AdminUser]:
        pass
    
    @abstractmethod
    def get_by_username(self, username: str) -> Optional[AdminUser]:
        pass
    
    @abstractmethod
    def get_admins_by_role(self, role: str) -> List[AdminUser]:
        pass
    
    @abstractmethod
    def get_all_admins(self, page: int, size: int) -> PageResult:
        pass
    
    @abstractmethod
    def update_role(self, admin_id: int, role: str):
        pass
    
    @abstractmethod
    def update_permissions(self, admin_id: int, permissions: str):
        pass
    
    @abstractmethod
    def deactivate(self, admin_id: int):
        pass
    
    @abstractmethod
    def delete(self, admin_id: int):
        pass

# AuditLogRepository 接口
class AuditLogRepository(ABC):
    @abstractmethod
    def record_log(self, log_data: AuditLog) -> AuditLog:
        pass
    
    @abstractmethod
    def get_by_id(self, log_id: str) -> Optional[AuditLog]:
        pass
    
    @abstractmethod
    def get_by_admin_user_id(self, admin_id: int, page: int, size: int) -> PageResult:
        pass
    
    @abstractmethod
    def get_by_action_type(self, action_type: str, page: int, size: int) -> PageResult:
        pass
    
    @abstractmethod
    def get_by_resource(self, resource_type: str, resource_id: str) -> List[AuditLog]:
        pass
    
    @abstractmethod
    def get_by_time_range(self, start_time, end_time) -> List[AuditLog]:
        pass
    
    @abstractmethod
    def search_logs(self, keyword: str, page: int, size: int) -> PageResult:
        pass

# ToolAuditRecordRepository 接口
class ToolAuditRecordRepository(ABC):
    @abstractmethod
    def create_audit_record(self, record_data: ToolAuditRecord) -> ToolAuditRecord:
        pass
    
    @abstractmethod
    def get_by_id(self, record_id: str) -> Optional[ToolAuditRecord]:
        pass
    
    @abstractmethod
    def get_by_tool_id(self, tool_id: str) -> Optional[ToolAuditRecord]:
        pass
    
    @abstractmethod
    def get_pending_audits(self) -> List[ToolAuditRecord]:
        pass
    
    @abstractmethod
    def get_by_auditor(self, admin_id: int, page: int, size: int) -> PageResult:
        pass
    
    @abstractmethod
    def get_by_status(self, audit_status: str, page: int, size: int) -> PageResult:
        pass
    
    @abstractmethod
    def update_audit_status(self, record_id: str, status: str, comment: Optional[str] = None):
        pass
    
    @abstractmethod
    def get_audit_history(self, tool_id: str) -> List[ToolAuditRecord]:
        pass

# SQLAlchemyAdminUserRepository 实现
class SQLAlchemyAdminUserRepository(AdminUserRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, admin_data: AdminUser) -> AdminUser:
        self.db.add(admin_data)
        self.db.commit()
        self.db.refresh(admin_data)
        return admin_data
    
    def get_by_id(self, admin_id: int) -> Optional[AdminUser]:
        return self.db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    
    def get_by_user_id(self, user_id: int) -> Optional[AdminUser]:
        return self.db.query(AdminUser).filter(AdminUser.user_id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[AdminUser]:
        return self.db.query(AdminUser).filter(AdminUser.username == username).first()
    
    def get_admins_by_role(self, role: str) -> List[AdminUser]:
        return self.db.query(AdminUser).filter(AdminUser.role == role).all()
    
    def get_all_admins(self, page: int, size: int) -> PageResult:
        total = self.db.query(AdminUser).count()
        items = self.db.query(AdminUser).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)
    
    def update_role(self, admin_id: int, role: str):
        admin = self.get_by_id(admin_id)
        if admin:
            admin.role = role
            self.db.commit()
    
    def update_permissions(self, admin_id: int, permissions: str):
        admin = self.get_by_id(admin_id)
        if admin:
            admin.permissions = permissions
            self.db.commit()
    
    def deactivate(self, admin_id: int):
        admin = self.get_by_id(admin_id)
        if admin:
            admin.is_active = False
            self.db.commit()
    
    def delete(self, admin_id: int):
        admin = self.get_by_id(admin_id)
        if admin:
            self.db.delete(admin)
            self.db.commit()

# SQLAlchemyAuditLogRepository 实现
class SQLAlchemyAuditLogRepository(AuditLogRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def record_log(self, log_data: AuditLog) -> AuditLog:
        self.db.add(log_data)
        self.db.commit()
        self.db.refresh(log_data)
        return log_data
    
    def get_by_id(self, log_id: str) -> Optional[AuditLog]:
        return self.db.query(AuditLog).filter(AuditLog.log_id == log_id).first()
    
    def get_by_admin_user_id(self, admin_id: int, page: int, size: int) -> PageResult:
        total = self.db.query(AuditLog).filter(AuditLog.admin_user_id == admin_id).count()
        items = self.db.query(AuditLog).filter(AuditLog.admin_user_id == admin_id).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)
    
    def get_by_action_type(self, action_type: str, page: int, size: int) -> PageResult:
        total = self.db.query(AuditLog).filter(AuditLog.action_type == action_type).count()
        items = self.db.query(AuditLog).filter(AuditLog.action_type == action_type).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)
    
    def get_by_resource(self, resource_type: str, resource_id: str) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.resource_type == resource_type,
            AuditLog.resource_id == resource_id
        ).all()
    
    def get_by_time_range(self, start_time, end_time) -> List[AuditLog]:
        return self.db.query(AuditLog).filter(
            AuditLog.created_at >= start_time,
            AuditLog.created_at <= end_time
        ).all()
    
    def search_logs(self, keyword: str, page: int, size: int) -> PageResult:
        total = self.db.query(AuditLog).filter(
            AuditLog.action_details.ilike(f"%{keyword}%")
        ).count()
        items = self.db.query(AuditLog).filter(
            AuditLog.action_details.ilike(f"%{keyword}%")
        ).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)

# SQLAlchemyToolAuditRecordRepository 实现
class SQLAlchemyToolAuditRecordRepository(ToolAuditRecordRepository):
    def __init__(self, db: Session):
        self.db = db
    
    def create_audit_record(self, record_data: ToolAuditRecord) -> ToolAuditRecord:
        self.db.add(record_data)
        self.db.commit()
        self.db.refresh(record_data)
        return record_data
    
    def get_by_id(self, record_id: str) -> Optional[ToolAuditRecord]:
        return self.db.query(ToolAuditRecord).filter(ToolAuditRecord.record_id == record_id).first()
    
    def get_by_tool_id(self, tool_id: str) -> Optional[ToolAuditRecord]:
        return self.db.query(ToolAuditRecord).filter(ToolAuditRecord.tool_id == tool_id).first()
    
    def get_pending_audits(self) -> List[ToolAuditRecord]:
        return self.db.query(ToolAuditRecord).filter(ToolAuditRecord.audit_status == "PENDING").all()
    
    def get_by_auditor(self, admin_id: int, page: int, size: int) -> PageResult:
        total = self.db.query(ToolAuditRecord).filter(ToolAuditRecord.auditor_admin_id == admin_id).count()
        items = self.db.query(ToolAuditRecord).filter(ToolAuditRecord.auditor_admin_id == admin_id).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)
    
    def get_by_status(self, audit_status: str, page: int, size: int) -> PageResult:
        total = self.db.query(ToolAuditRecord).filter(ToolAuditRecord.audit_status == audit_status).count()
        items = self.db.query(ToolAuditRecord).filter(ToolAuditRecord.audit_status == audit_status).offset((page - 1) * size).limit(size).all()
        return PageResult(items, total, page, size)
    
    def update_audit_status(self, record_id: str, status: str, comment: Optional[str] = None):
        record = self.get_by_id(record_id)
        if record:
            record.audit_status = status
            if comment:
                record.audit_comment = comment
            self.db.commit()
    
    def get_audit_history(self, tool_id: str) -> List[ToolAuditRecord]:
        return self.db.query(ToolAuditRecord).filter(ToolAuditRecord.tool_id == tool_id).order_by(ToolAuditRecord.created_at.desc()).all()
