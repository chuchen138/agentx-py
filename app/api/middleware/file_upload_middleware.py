from fastapi import Depends, HTTPException, UploadFile, File
from typing import Optional
import magic


class FileUploadValidator:
    """文件上传验证器"""

    def __init__(self, max_size: int = 50 * 1024 * 1024, allowed_extensions: Optional[set] = None):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions

    async def __call__(self, file: UploadFile = File(...)) -> UploadFile:
        """验证文件"""
        # 检查文件大小
        content = await file.read()
        if len(content) > self.max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds the limit of {self.max_size / (1024 * 1024)}MB"
            )

        # 检查文件扩展名
        if self.allowed_extensions:
            filename = file.filename
            if filename:
                ext = filename.split(".")[-1].lower()
                if ext not in self.allowed_extensions:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File extension not allowed. Allowed extensions: {self.allowed_extensions}"
                    )

        # 检查文件类型
        mime_type = magic.from_buffer(content, mime=True)
        if not self._is_valid_mime_type(mime_type):
            raise HTTPException(
                status_code=400,
                detail=f"File type not allowed: {mime_type}"
            )

        # 重置文件指针
        await file.seek(0)
        return file

    def _is_valid_mime_type(self, mime_type: str) -> bool:
        """验证MIME类型"""
        # 这里可以添加更详细的MIME类型验证
        allowed_mime_types = {
            "image/jpeg", "image/png", "image/webp", "image/gif",  # 图片
            "application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # 文档
            "text/plain", "text/markdown", "text/csv",  # 文本
            "application/zip", "application/x-rar-compressed", "application/x-7z-compressed",  # 压缩包
            "video/mp4", "video/avi", "video/quicktime",  # 视频
            "audio/mpeg", "audio/wav", "audio/flac"  # 音频
        }
        return mime_type in allowed_mime_types


# 预定义的验证器
avatar_validator = FileUploadValidator(max_size=2 * 1024 * 1024, allowed_extensions={"jpg", "jpeg", "png", "webp"})
general_validator = FileUploadValidator(max_size=50 * 1024 * 1024)
rag_validator = FileUploadValidator(max_size=500 * 1024 * 1024, allowed_extensions={"pdf", "doc", "docx", "txt", "md", "csv"})
