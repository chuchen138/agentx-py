from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from app.domain.file.file_record import FileRecord
from app.infrastructure.storage.backend.base import StorageBackend


class FileStorageStrategy(ABC):
    """文件存储策略抽象基类"""

    @abstractmethod
    def save(self, file: bytes, metadata: Dict[str, Any]) -> FileRecord:
        """保存文件"""
        pass

    @abstractmethod
    def update(self, file_record: FileRecord, file: bytes) -> FileRecord:
        """更新文件"""
        pass

    @abstractmethod
    def get_by_url(self, file_url: str) -> FileRecord:
        """根据URL获取文件"""
        pass

    @abstractmethod
    def delete(self, file_url: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def validate_file(self, file: bytes, filename: str) -> bool:
        """验证文件合法性"""
        pass

    @abstractmethod
    def get_storage_backend(self) -> StorageBackend:
        """获取存储后端"""
        pass
