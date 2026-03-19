import pytest
import tempfile
from app.application.file.strategy.avatar_file_storage_strategy import AvatarFileStorageStrategy
from app.application.file.strategy.general_file_storage_strategy import GeneralFileStorageStrategy
from app.application.file.strategy.rag_file_storage_strategy import RagFileStorageStrategy
import uuid


def test_avatar_strategy_validate_file():
    """测试头像策略的文件验证功能"""
    strategy = AvatarFileStorageStrategy()
    
    # 测试有效文件
    valid_content = b"fake image content"
    valid_filename = "avatar.png"
    assert strategy.validate_file(valid_content, valid_filename) is True
    
    # 测试无效文件大小
    invalid_content = b"x" * (3 * 1024 * 1024)  # 3MB
    invalid_filename = "avatar.png"
    assert strategy.validate_file(invalid_content, invalid_filename) is False
    
    # 测试无效文件格式
    valid_content = b"fake image content"
    invalid_filename = "avatar.exe"
    assert strategy.validate_file(valid_content, invalid_filename) is False


def test_general_strategy_validate_file():
    """测试通用策略的文件验证功能"""
    strategy = GeneralFileStorageStrategy()
    
    # 测试有效文件
    valid_content = b"fake file content"
    valid_filename = "document.txt"
    assert strategy.validate_file(valid_content, valid_filename) is True
    
    # 测试无效文件大小
    invalid_content = b"x" * (60 * 1024 * 1024)  # 60MB
    invalid_filename = "document.txt"
    assert strategy.validate_file(invalid_content, invalid_filename) is False


def test_rag_strategy_validate_file():
    """测试RAG策略的文件验证功能"""
    strategy = RagFileStorageStrategy()
    
    # 测试有效文件
    valid_content = b"fake document content"
    valid_filename = "document.pdf"
    assert strategy.validate_file(valid_content, valid_filename) is True
    
    # 测试无效文件格式
    valid_content = b"fake document content"
    invalid_filename = "document.exe"
    assert strategy.validate_file(valid_content, invalid_filename) is False
