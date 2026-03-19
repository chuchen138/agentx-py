from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class StorageBackend(ABC):
    """存储后端抽象基类"""

    @abstractmethod
    def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        pass

    @abstractmethod
    def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        pass

    @abstractmethod
    def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        pass

    @abstractmethod
    def delete(self, file_url: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        pass

    @abstractmethod
    def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        pass


class AsyncStorageBackend(ABC):
    """异步存储后端抽象基类"""

    @abstractmethod
    async def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        pass

    @abstractmethod
    async def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        pass

    @abstractmethod
    async def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        pass

    @abstractmethod
    async def delete(self, file_url: str) -> bool:
        """删除文件"""
        pass

    @abstractmethod
    async def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        pass

    @abstractmethod
    async def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        pass

    @abstractmethod
    async def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        pass
