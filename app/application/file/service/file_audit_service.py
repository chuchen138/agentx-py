import structlog
from datetime import datetime
from uuid import UUID

logger = structlog.get_logger()


class FileAuditService:
    """文件操作审计服务"""

    def log_upload(self, user_id: UUID, file_id: UUID, file_type: str, size: int, context: dict = None):
        """记录文件上传操作"""
        logger.info(
            "file.upload",
            user_id=str(user_id),
            file_id=str(file_id),
            file_type=file_type,
            file_size=size,
            timestamp=datetime.utcnow().isoformat(),
            **(context or {})
        )

    def log_download(self, user_id: UUID, file_id: UUID, context: dict = None):
        """记录文件下载操作"""
        logger.info(
            "file.download",
            user_id=str(user_id),
            file_id=str(file_id),
            timestamp=datetime.utcnow().isoformat(),
            **(context or {})
        )

    def log_delete(self, user_id: UUID, file_id: UUID, context: dict = None):
        """记录文件删除操作"""
        logger.info(
            "file.delete",
            user_id=str(user_id),
            file_id=str(file_id),
            timestamp=datetime.utcnow().isoformat(),
            **(context or {})
        )

    def log_error(self, user_id: UUID, operation: str, error: str, context: dict = None):
        """记录文件操作错误"""
        logger.error(
            f"file.{operation}.error",
            user_id=str(user_id) if user_id else None,
            error=error,
            timestamp=datetime.utcnow().isoformat(),
            **(context or {})
        )


# 全局审计服务实例
file_audit_service = FileAuditService()
