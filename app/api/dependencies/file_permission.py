from fastapi import Depends, HTTPException
from uuid import UUID
from app.domain.file.file_record import FileRecord
from app.application.file.service.file_storage_app_service import FileStorageAppService

file_service = FileStorageAppService()


def get_file_record(file_id: UUID) -> FileRecord:
    """获取文件记录"""
    try:
        file_record = file_service.get_file(file_id=file_id)
        return file_record
    except Exception as e:
        raise HTTPException(status_code=404, detail="File not found")


def verify_file_ownership(file_record: FileRecord = Depends(get_file_record), user_id: UUID = None) -> FileRecord:
    """验证文件所有权"""
    if not file_service.validate_permission(file_record, user_id):
        raise HTTPException(status_code=403, detail="Permission denied")
    return file_record
