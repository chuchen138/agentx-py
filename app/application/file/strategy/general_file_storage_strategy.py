import os
from datetime import datetime
from typing import Dict, Any
import uuid
import hashlib
import mimetypes
from app.domain.file.file_record import FileRecord
from app.domain.file.file_type import FileType
from app.domain.file.storage_backend_type import StorageBackendType
from app.application.file.strategy.file_storage_strategy import FileStorageStrategy
from app.infrastructure.storage.backend.base import StorageBackend
from app.infrastructure.storage.backend.minio_storage import MinioStorageBackend
from app.infrastructure.storage.backend.local_storage import LocalStorageBackend


class GeneralFileStorageStrategy(FileStorageStrategy):
    """通用文件存储策略"""

    def __init__(self, storage_backend: MinioStorageBackend = None):
        if storage_backend:
            self.storage_backend = storage_backend
        else:
            try:
                # 尝试使用Minio存储
                self.storage_backend = MinioStorageBackend(bucket="agentx-files", base_url="http://localhost:9000/agentx-files")
            except Exception as e:
                # 如果Minio连接失败，降级到本地存储
                print(f"Warning: Minio connection failed, falling back to local storage: {e}")
                self.storage_backend = LocalStorageBackend(root_dir="./uploads/general")
        self.max_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = {
            "jpg", "jpeg", "png", "webp", "gif", "bmp", "svg",  # 图片
            "pdf", "doc", "docx", "txt", "md", "csv", "xls", "xlsx", "ppt", "pptx", "rtf",  # 文档
            "zip", "rar", "7z", "tar", "gz", "bz2",  # 压缩包
            "mp4", "avi", "mov", "wmv", "flv", "mkv", "webm",  # 视频
            "mp3", "wav", "flac", "ogg", "wma", "aac",  # 音频
            "json", "xml", "yaml", "yml", "toml",  # 配置文件
            "html", "css", "js", "jsx", "ts", "tsx", "py", "java", "c", "cpp", "cs", "go", "rb", "php",  # 代码文件
            "exe", "dll", "msi", "deb", "rpm",  # 可执行文件
            "psd", "ai", "xd", "sketch",  # 设计文件
            "sql", "db", "sqlite",  # 数据库文件
            "log", "ini", "conf", "cfg"  # 日志和配置文件
        }

    def _generate_filename(self, user_id: str, original_filename: str) -> str:
        """生成存储文件名"""
        date_str = datetime.utcnow().strftime("%Y/%m/%d")
        ext = os.path.splitext(original_filename)[1].lstrip(".").lower()
        return f"{user_id}/{date_str}/{uuid.uuid4()}.{ext}"

    def _validate_file_size(self, file: bytes) -> bool:
        """验证文件大小"""
        return len(file) <= self.max_size

    def _validate_file_format(self, filename: str) -> bool:
        """验证文件格式"""
        ext = os.path.splitext(filename)[1].lstrip(".").lower()
        return ext in self.allowed_extensions

    def _get_mime_type(self, file: bytes, filename: str) -> str:
        """获取文件MIME类型"""
        try:
            ext = os.path.splitext(filename)[1].lower()
            mime_type, _ = mimetypes.guess_type(f"file{ext}")
            return mime_type or "application/octet-stream"
        except Exception:
            return "application/octet-stream"

    def _generate_file_hash(self, file: bytes) -> str:
        """生成文件哈希值"""
        return hashlib.sha256(file).hexdigest()

    def save(self, file: bytes, metadata: Dict[str, Any]) -> FileRecord:
        """保存文件"""
        # 验证文件
        original_filename = metadata.get("original_filename", "file")
        if not self.validate_file(file, original_filename):
            raise ValueError("Invalid general file")

        # 生成文件名
        user_id = str(metadata.get("user_id"))
        filename = self._generate_filename(user_id, original_filename)

        # 获取MIME类型
        mime_type = self._get_mime_type(file, original_filename)

        # 保存到存储后端
        file_url = self.storage_backend.save(file, filename)

        # 创建文件记录
        import uuid
        return FileRecord(
            id=str(uuid.uuid4()),
            user_id=str(metadata.get("user_id")),
            file_type=FileType.GENERAL.value,
            original_filename=original_filename,
            stored_filename=filename,
            file_path=filename,
            file_url=file_url,
            file_size=len(file),
            mime_type=mime_type,
            storage_backend=StorageBackendType.LOCAL.value,
            file_metadata=metadata
        )

    def update(self, file_record: FileRecord, file: bytes) -> FileRecord:
        """更新文件"""
        # 验证文件
        if not self.validate_file(file, file_record.original_filename):
            raise ValueError("Invalid general file")

        # 更新文件
        self.storage_backend.update(file_record.file_url, file)

        # 更新记录
        file_record.file_size = len(file)
        file_record.updated_at = datetime.utcnow()
        return file_record

    def get_by_url(self, file_url: str) -> FileRecord:
        """根据URL获取文件"""
        # 这里需要从数据库查询，暂时返回一个模拟对象
        # 实际实现需要从数据库根据file_url查询
        raise NotImplementedError("get_by_url not implemented")

    def delete(self, file_url: str) -> bool:
        """删除文件"""
        return self.storage_backend.delete(file_url)

    def validate_file(self, file: bytes, filename: str) -> bool:
        """验证文件合法性"""
        # 验证大小
        if not self._validate_file_size(file):
            return False
        # 验证格式（如果没有扩展名，默认允许）
        if not self._validate_file_format(filename):
            # 如果文件名没有扩展名，默认允许
            ext = os.path.splitext(filename)[1].lstrip(".").lower()
            if not ext:
                return True
            return False
        return True

    def get_storage_backend(self) -> StorageBackend:
        """获取存储后端"""
        return self.storage_backend
