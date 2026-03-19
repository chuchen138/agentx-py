import pytest
import tempfile
import os
from app.infrastructure.storage.backend.local_storage import LocalStorageBackend


def test_local_storage_save_load():
    """测试本地存储的保存和加载功能"""
    # 创建临时目录作为存储根目录
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建本地存储后端实例
        storage = LocalStorageBackend(root_dir=temp_dir, base_url="http://localhost:8000/uploads")
        
        # 测试文件内容
        test_content = b"Hello, World!"
        test_filename = "test.txt"
        
        # 保存文件
        file_url = storage.save(test_content, test_filename)
        assert file_url.startswith("http://localhost:8000/uploads/")
        
        # 加载文件
        loaded_content = storage.load(file_url)
        assert loaded_content == test_content
        
        # 检查文件是否存在
        assert storage.exists(file_url) is True
        
        # 删除文件
        assert storage.delete(file_url) is True
        assert storage.exists(file_url) is False


def test_local_storage_list_files():
    """测试本地存储的列出文件功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorageBackend(root_dir=temp_dir, base_url="http://localhost:8000/uploads")
        
        # 保存多个文件
        test_files = [
            (b"Content 1", "file1.txt"),
            (b"Content 2", "file2.txt"),
            (b"Content 3", "subdir/file3.txt")
        ]
        
        for content, filename in test_files:
            storage.save(content, filename)
        
        # 列出所有文件
        files = storage.list_files()
        assert len(files) == 3
        
        # 列出特定前缀的文件
        subdir_files = storage.list_files(prefix="subdir")
        assert len(subdir_files) == 1


def test_local_storage_get_metadata():
    """测试本地存储的获取元数据功能"""
    with tempfile.TemporaryDirectory() as temp_dir:
        storage = LocalStorageBackend(root_dir=temp_dir, base_url="http://localhost:8000/uploads")
        
        test_content = b"Hello, World!"
        test_filename = "test.txt"
        
        file_url = storage.save(test_content, test_filename)
        metadata = storage.get_metadata(file_url)
        
        assert "size" in metadata
        assert metadata["size"] == len(test_content)
        assert "mtime" in metadata
        assert "mode" in metadata
