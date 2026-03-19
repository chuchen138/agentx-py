import os
from datetime import datetime
from typing import Dict, Any
import uuid
import mimetypes
from app.domain.file.file_record import FileRecord
from app.domain.file.file_type import FileType
from app.domain.file.storage_backend_type import StorageBackendType
from app.application.file.strategy.file_storage_strategy import FileStorageStrategy
from app.infrastructure.storage.backend.base import StorageBackend
from app.infrastructure.storage.backend.minio_storage import MinioStorageBackend
from app.infrastructure.storage.backend.local_storage import LocalStorageBackend


class RagFileStorageStrategy(FileStorageStrategy):
    """RAG文件存储策略"""

    def __init__(self, storage_backend: MinioStorageBackend = None):
        if storage_backend:
            self.storage_backend = storage_backend
        else:
            try:
                # 尝试使用Minio存储
                self.storage_backend = MinioStorageBackend(bucket="rag-documents", base_url="http://localhost:9000/rag-documents")
            except Exception as e:
                # 如果Minio连接失败，降级到本地存储
                print(f"Warning: Minio connection failed, falling back to local storage: {e}")
                self.storage_backend = LocalStorageBackend(root_dir="./uploads/rag")
        self.max_size = 500 * 1024 * 1024  # 500MB
        self.allowed_extensions = {"pdf", "doc", "docx", "txt", "md", "csv"}

    def _generate_filename(self, user_id: str, dataset_id: str, original_filename: str) -> str:
        """生成存储文件名"""
        ext = os.path.splitext(original_filename)[1].lstrip(".").lower()
        return f"{user_id}/{dataset_id}/{uuid.uuid4()}.{ext}"

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

    def _preprocess_file(self, file: bytes, filename: str) -> Dict[str, Any]:
        """预处理文件"""
        # 这里可以添加文件预处理逻辑，如文本提取、OCR等
        # 暂时返回空字典
        return {}

    def save(self, file: bytes, metadata: Dict[str, Any]) -> FileRecord:
        """保存文件"""
        # 验证文件
        original_filename = metadata.get("original_filename", "file")
        if not self.validate_file(file, original_filename):
            raise ValueError("Invalid RAG file")

        # 生成文件名
        user_id = str(metadata.get("user_id"))
        dataset_id = str(metadata.get("dataset_id", "default"))
        filename = self._generate_filename(user_id, dataset_id, original_filename)

        # 获取MIME类型
        mime_type = self._get_mime_type(file, original_filename)

        # 预处理文件
        preprocess_result = self._preprocess_file(file, original_filename)
        metadata.update(preprocess_result)

        # 保存到存储后端
        file_url = self.storage_backend.save(file, filename)

        # 创建文件记录
        import uuid
        return FileRecord(
            id=str(uuid.uuid4()),
            user_id=str(metadata.get("user_id")),
            file_type=FileType.RAG.value,
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
            raise ValueError("Invalid RAG file")

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
        # 验证格式
        if not self._validate_file_format(filename):
            return False
        return True

    def get_storage_backend(self) -> StorageBackend:
        """获取存储后端"""
        return self.storage_backend
