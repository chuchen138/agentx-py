from typing import Dict, Set
from pydantic import BaseModel


class FileTypeWhitelist(BaseModel):
    """文件类型白名单"""
    # 图片类型
    images: Set[str] = {
        "jpg", "jpeg", "png", "webp", "gif"
    }
    # 文档类型
    documents: Set[str] = {
        "pdf", "doc", "docx", "txt", "md", "csv"
    }
    # 其他类型
    others: Set[str] = {
        "zip", "rar", "7z",
        "mp4", "avi", "mov",
        "mp3", "wav", "flac"
    }
    # 扩展名到MIME类型的映射
    mime_types: Dict[str, str] = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "pdf": "application/pdf",
        "doc": "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "txt": "text/plain",
        "md": "text/markdown",
        "csv": "text/csv",
        "zip": "application/zip",
        "rar": "application/x-rar-compressed",
        "7z": "application/x-7z-compressed",
        "mp4": "video/mp4",
        "avi": "video/avi",
        "mov": "video/quicktime",
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "flac": "audio/flac"
    }

    def is_allowed(self, extension: str) -> bool:
        """检查扩展名是否在白名单中"""
        ext = extension.lower().lstrip(".")
        return ext in self.images or ext in self.documents or ext in self.others

    def get_mime_type(self, extension: str) -> str:
        """获取扩展名对应的MIME类型"""
        ext = extension.lower().lstrip(".")
        return self.mime_types.get(ext, "application/octet-stream")

    def add_extension(self, extension: str, mime_type: str, category: str = "others") -> None:
        """添加新的扩展名到白名单"""
        ext = extension.lower().lstrip(".")
        if category == "images":
            self.images.add(ext)
        elif category == "documents":
            self.documents.add(ext)
        else:
            self.others.add(ext)
        self.mime_types[ext] = mime_type

    def remove_extension(self, extension: str) -> None:
        """从白名单中移除扩展名"""
        ext = extension.lower().lstrip(".")
        if ext in self.images:
            self.images.remove(ext)
        elif ext in self.documents:
            self.documents.remove(ext)
        elif ext in self.others:
            self.others.remove(ext)
        if ext in self.mime_types:
            del self.mime_types[ext]


# 全局白名单实例
file_type_whitelist = FileTypeWhitelist()
