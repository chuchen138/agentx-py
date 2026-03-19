import pytest
from app.domain.file.file_record import FileRecord
from app.domain.file.file_type import FileType
from app.domain.file.storage_backend_type import StorageBackendType
import uuid
from datetime import datetime


def test_file_record_creation():
    """测试文件记录创建"""
    user_id = uuid.uuid4()
    file_record = FileRecord(
        user_id=user_id,
        file_type=FileType.GENERAL.value,
        original_filename="test.txt",
        stored_filename="test_123.txt",
        file_path="/general/123/test_123.txt",
        file_url="http://localhost:8000/uploads/general/123/test_123.txt",
        file_size=1024,
        mime_type="text/plain",
        storage_backend=StorageBackendType.LOCAL.value,
        metadata={"key": "value"}
    )
    
    assert file_record.user_id == user_id
    assert file_record.file_type == FileType.GENERAL.value
    assert file_record.original_filename == "test.txt"
    assert file_record.stored_filename == "test_123.txt"
    assert file_record.file_path == "/general/123/test_123.txt"
    assert file_record.file_url == "http://localhost:8000/uploads/general/123/test_123.txt"
    assert file_record.file_size == 1024
    assert file_record.mime_type == "text/plain"
    assert file_record.storage_backend == StorageBackendType.LOCAL.value
    assert file_record.metadata == {"key": "value"}
    assert file_record.version == 1
    assert isinstance(file_record.created_at, datetime)
    assert isinstance(file_record.updated_at, datetime)
    assert file_record.deleted_at is None
