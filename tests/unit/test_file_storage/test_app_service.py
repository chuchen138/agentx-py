import pytest
from app.application.file.service.file_storage_app_service import FileStorageAppService
from app.domain.file.file_type import FileType
import uuid


def test_file_storage_app_service_determine_file_type():
    """测试文件存储应用服务的文件类型判断功能"""
    service = FileStorageAppService()
    
    # 测试头像文件
    assert service.determine_file_type("avatar.png", "image/png") == FileType.AVATAR
    assert service.determine_file_type("profile.jpg", "image/jpeg") == FileType.AVATAR
    
    # 测试RAG文件
    assert service.determine_file_type("document.pdf", "application/pdf") == FileType.RAG
    assert service.determine_file_type("data.csv", "text/csv") == FileType.RAG
    assert service.determine_file_type("notes.md", "text/markdown") == FileType.RAG
    
    # 测试通用文件
    assert service.determine_file_type("file.zip", "application/zip") == FileType.GENERAL
    assert service.determine_file_type("video.mp4", "video/mp4") == FileType.GENERAL
