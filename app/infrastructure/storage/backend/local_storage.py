import os
import shutil
from pathlib import Path
from typing import List, Dict, Any
import aiofiles
from app.infrastructure.storage.backend.base import StorageBackend, AsyncStorageBackend


class LocalStorageBackend(StorageBackend):
    """本地存储适配器"""

    def __init__(self, root_dir: str = "./uploads", base_url: str = "http://localhost:8000/uploads"):
        self.root_dir = Path(root_dir)
        self.base_url = base_url
        # 确保根目录存在
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 分割路径和文件名
        path_parts = filename.split("/")
        sanitized_parts = []
        
        for part in path_parts:
            # 移除特殊字符，保留字母数字和基本符号
            sanitized_part = "".join(c for c in part if c.isalnum() or c in "._- ")
            # 确保部分不为空
            if sanitized_part:
                sanitized_parts.append(sanitized_part)
        
        # 重新组合路径
        return "/".join(sanitized_parts)

    def _get_file_path(self, filename: str) -> Path:
        """获取文件路径"""
        # 清理文件名
        sanitized_filename = self._sanitize_filename(filename)
        # 构建完整路径
        file_path = self.root_dir / sanitized_filename
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    def _get_url_from_path(self, file_path: Path) -> str:
        """从文件路径生成URL"""
        # 计算相对路径
        relative_path = file_path.relative_to(self.root_dir)
        # 构建URL
        return f"{self.base_url}/{relative_path.as_posix()}"

    def _get_path_from_url(self, file_url: str) -> Path:
        """从URL获取文件路径"""
        # 移除base_url
        if file_url.startswith(self.base_url):
            relative_path = file_url[len(self.base_url) + 1:]
            return self.root_dir / relative_path
        return Path(file_url)

    def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        file_path = self._get_file_path(filename)
        with open(file_path, "wb") as f:
            f.write(file_content)
        return self._get_url_from_path(file_path)

    def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        file_path = self._get_path_from_url(file_url)
        with open(file_path, "rb") as f:
            return f.read()

    def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        file_path = self._get_path_from_url(file_url)
        with open(file_path, "wb") as f:
            f.write(new_content)
        return file_url

    def delete(self, file_url: str) -> bool:
        """删除文件"""
        try:
            file_path = self._get_path_from_url(file_url)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        file_path = self._get_path_from_url(file_url)
        return file_path.exists()

    def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        # 本地存储直接返回原URL，无需签名
        return file_url

    def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        prefix_path = self.root_dir / prefix
        files = []
        if prefix_path.exists():
            for file_path in prefix_path.rglob("*"):
                if file_path.is_file():
                    files.append(self._get_url_from_path(file_path))
        return files

    def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        file_path = self._get_path_from_url(file_url)
        if not file_path.exists():
            return {}
        return {
            "size": file_path.stat().st_size,
            "mtime": file_path.stat().st_mtime,
            "mode": file_path.stat().st_mode,
        }


class AsyncLocalStorageBackend(AsyncStorageBackend):
    """异步本地存储适配器"""

    def __init__(self, root_dir: str = "./uploads", base_url: str = "http://localhost:8000/uploads"):
        self.root_dir = Path(root_dir)
        self.base_url = base_url
        # 确保根目录存在
        self.root_dir.mkdir(parents=True, exist_ok=True)

    def _sanitize_filename(self, filename: str) -> str:
        """清理文件名，防止路径遍历攻击"""
        # 分割路径和文件名
        path_parts = filename.split("/")
        sanitized_parts = []
        
        for part in path_parts:
            # 移除特殊字符，保留字母数字和基本符号
            sanitized_part = "".join(c for c in part if c.isalnum() or c in "._- ")
            # 确保部分不为空
            if sanitized_part:
                sanitized_parts.append(sanitized_part)
        
        # 重新组合路径
        return "/".join(sanitized_parts)

    def _get_file_path(self, filename: str) -> Path:
        """获取文件路径"""
        # 清理文件名
        sanitized_filename = self._sanitize_filename(filename)
        # 构建完整路径
        file_path = self.root_dir / sanitized_filename
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)
        return file_path

    def _get_url_from_path(self, file_path: Path) -> str:
        """从文件路径生成URL"""
        # 计算相对路径
        relative_path = file_path.relative_to(self.root_dir)
        # 构建URL
        return f"{self.base_url}/{relative_path.as_posix()}"

    def _get_path_from_url(self, file_url: str) -> Path:
        """从URL获取文件路径"""
        # 移除base_url
        if file_url.startswith(self.base_url):
            relative_path = file_url[len(self.base_url) + 1:]
            return self.root_dir / relative_path
        return Path(file_url)

    async def save(self, file_content: bytes, filename: str, **kwargs) -> str:
        """保存文件，返回URL"""
        file_path = self._get_file_path(filename)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(file_content)
        return self._get_url_from_path(file_path)

    async def load(self, file_url: str) -> bytes:
        """加载文件内容"""
        file_path = self._get_path_from_url(file_url)
        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def update(self, file_url: str, new_content: bytes) -> str:
        """更新文件"""
        file_path = self._get_path_from_url(file_url)
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(new_content)
        return file_url

    async def delete(self, file_url: str) -> bool:
        """删除文件"""
        try:
            file_path = self._get_path_from_url(file_url)
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    async def exists(self, file_url: str) -> bool:
        """检查文件是否存在"""
        file_path = self._get_path_from_url(file_url)
        return file_path.exists()

    async def get_url(self, file_url: str, expires_in: int = 3600) -> str:
        """获取访问URL"""
        # 本地存储直接返回原URL，无需签名
        return file_url

    async def list_files(self, prefix: str = "") -> List[str]:
        """列出文件"""
        prefix_path = self.root_dir / prefix
        files = []
        if prefix_path.exists():
            for file_path in prefix_path.rglob("*"):
                if file_path.is_file():
                    files.append(self._get_url_from_path(file_path))
        return files

    async def get_metadata(self, file_url: str) -> Dict[str, Any]:
        """获取文件元数据"""
        file_path = self._get_path_from_url(file_url)
        if not file_path.exists():
            return {}
        return {
            "size": file_path.stat().st_size,
            "mtime": file_path.stat().st_mtime,
            "mode": file_path.stat().st_mode,
        }
