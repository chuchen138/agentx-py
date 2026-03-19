from typing import Dict, Any, Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.file.file_record import FileRecord
from app.domain.file.file_type import FileType
from app.application.file.factory.file_storage_strategy_factory import strategy_factory
from app.core.database import SessionLocal


class FileStorageAppService:
    """文件存储应用服务"""

    def __init__(self):
        self.strategy_factory = strategy_factory

    def save_file(self, file: bytes, file_type: FileType, user_id: UUID, metadata: Dict[str, Any]) -> FileRecord:
        """保存文件"""
        # 获取对应的存储策略
        strategy = self.strategy_factory.get_strategy(file_type)
        
        # 添加上传用户信息
        metadata["user_id"] = str(user_id)
        
        # 委托策略保存文件
        file_record = strategy.save(file, metadata)
        
        # 确保user_id是字符串
        file_record.user_id = str(user_id)
        
        # 保存到数据库
        db = SessionLocal()
        try:
            db.add(file_record)
            db.commit()
            db.refresh(file_record)
            return file_record
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def update_file(self, file_id: UUID, file: bytes, user_id: UUID) -> FileRecord:
        """更新文件"""
        db = SessionLocal()
        try:
            # 从数据库获取文件记录
            file_record = db.query(FileRecord).filter(
                FileRecord.id == str(file_id),
                FileRecord.user_id == str(user_id),
                FileRecord.deleted_at.is_(None)
            ).first()
            
            if not file_record:
                raise ValueError("File not found")
            
            # 获取对应的存储策略
            strategy = self.strategy_factory.get_strategy(FileType(file_record.file_type))
            
            # 更新文件
            updated_record = strategy.update(file_record, file)
            
            # 保存到数据库
            db.commit()
            db.refresh(updated_record)
            return updated_record
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def get_file(self, file_id: Optional[UUID] = None, file_url: Optional[str] = None, user_id: Optional[UUID] = None) -> FileRecord:
        """获取文件"""
        db = SessionLocal()
        try:
            query = db.query(FileRecord).filter(FileRecord.deleted_at.is_(None))
            
            if file_id:
                query = query.filter(FileRecord.id == str(file_id))
            if file_url:
                query = query.filter(FileRecord.file_url == file_url)
            if user_id:
                query = query.filter(FileRecord.user_id == str(user_id))
            
            file_record = query.first()
            if not file_record:
                raise ValueError("File not found")
            
            return file_record
        finally:
            db.close()

    def get_files_by_user_id(self, user_id: UUID, file_type: Optional[str] = None) -> List[FileRecord]:
        """根据用户ID获取文件列表"""
        db = SessionLocal()
        try:
            query = db.query(FileRecord).filter(
                FileRecord.user_id == str(user_id),
                FileRecord.deleted_at.is_(None)
            )
            
            if file_type:
                query = query.filter(FileRecord.file_type == file_type)
            
            return query.order_by(FileRecord.created_at.desc()).all()
        finally:
            db.close()

    def delete_file(self, file_id: Optional[UUID] = None, file_url: Optional[str] = None, user_id: UUID = None) -> bool:
        """删除文件"""
        db = SessionLocal()
        try:
            query = db.query(FileRecord).filter(
                FileRecord.deleted_at.is_(None)
            )
            
            if file_id:
                query = query.filter(FileRecord.id == str(file_id))
            if file_url:
                query = query.filter(FileRecord.file_url == file_url)
            if user_id:
                query = query.filter(FileRecord.user_id == str(user_id))
            
            file_record = query.first()
            if not file_record:
                return False
            
            # 获取对应的存储策略
            strategy = self.strategy_factory.get_strategy(FileType(file_record.file_type))
            
            # 删除文件
            # 从存储后端删除文件
            strategy.delete(file_record.file_url)
            
            # 软删除文件记录
            from datetime import datetime
            file_record.deleted_at = datetime.utcnow()
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False
        finally:
            db.close()

    def determine_file_type(self, filename: str, content_type: str) -> FileType:
        """根据文件名和内容类型判断文件类型"""
        # 简单的文件类型判断逻辑
        # 实际实现可能需要更复杂的判断
        if any(ext in filename.lower() for ext in [".jpg", ".jpeg", ".png", ".webp"]):
            return FileType.AVATAR
        elif any(ext in filename.lower() for ext in [".pdf", ".doc", ".docx", ".txt", ".md", ".csv"]):
            return FileType.RAG
        else:
            return FileType.GENERAL

    def validate_permission(self, file_record: FileRecord, user_id: UUID) -> bool:
        """验证用户对文件的访问权限"""
        # 简单的权限验证：只有文件所有者可以访问
        return file_record.user_id == user_id
