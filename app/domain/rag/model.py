import uuid
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional


class RagDatasetStatus(Enum):
    """RAG数据集状态"""
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class RagVersionStatus(Enum):
    """RAG版本状态"""
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    UNPUBLISHED = "UNPUBLISHED"


class DocumentProcessingStatus(Enum):
    """文档处理状态"""
    UPLOADED = "UPLOADED"
    OCR_PROCESSING = "OCR_PROCESSING"
    OCR_COMPLETED = "OCR_COMPLETED"
    EMBEDDING_PROCESSING = "EMBEDDING_PROCESSING"
    COMPLETED = "COMPLETED"
    OCR_FAILED = "OCR_FAILED"
    EMBEDDING_FAILED = "EMBEDDING_FAILED"


class SearchType(Enum):
    """检索类型"""
    VECTOR = "VECTOR"
    KEYWORD = "KEYWORD"
    HYBRID = "HYBRID"


class RagDataset:
    """RAG数据集模型"""

    def __init__(self,
                 id: str = None,
                 user_id: str = None,
                 name: str = None,
                 description: str = None,
                 status: RagDatasetStatus = RagDatasetStatus.ACTIVE,
                 document_count: int = 0,
                 document_unit_count: int = 0,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.id = id or str(uuid.uuid4())
        self.user_id = user_id
        self.name = name
        self.description = description
        self.status = status
        self.document_count = document_count
        self.document_unit_count = document_unit_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "document_count": self.document_count,
            "document_unit_count": self.document_unit_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RagDocument:
    """RAG文档模型"""

    def __init__(self,
                 id: str = None,
                 dataset_id: str = None,
                 file_id: str = None,
                 file_name: str = None,
                 file_path: str = None,
                 file_url: str = None,
                 file_size: int = 0,
                 mime_type: str = None,
                 processing_status: DocumentProcessingStatus = DocumentProcessingStatus.UPLOADED,
                 error_message: str = None,
                 unit_count: int = 0,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.id = id or str(uuid.uuid4())
        self.dataset_id = dataset_id
        self.file_id = file_id
        self.file_name = file_name
        self.file_path = file_path
        self.file_url = file_url
        self.file_size = file_size
        self.mime_type = mime_type
        self.processing_status = processing_status
        self.error_message = error_message
        self.unit_count = unit_count
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "file_id": self.file_id,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "file_url": self.file_url,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "processing_status": self.processing_status.value,
            "error_message": self.error_message,
            "unit_count": self.unit_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class DocumentUnit:
    """文档单元模型"""

    def __init__(self,
                 id: str = None,
                 document_id: str = None,
                 dataset_id: str = None,
                 content: str = None,
                 metadata: Dict[str, Any] = None,
                 embedding_status: str = "PENDING",
                 embedding_vector: List[float] = None,
                 page_number: Optional[int] = None,
                 chunk_index: Optional[int] = None,
                 created_at: datetime = None,
                 updated_at: datetime = None):
        self.id = id or str(uuid.uuid4())
        self.document_id = document_id
        self.dataset_id = dataset_id
        self.content = content
        self.metadata = metadata or {}
        self.embedding_status = embedding_status
        self.embedding_vector = embedding_vector
        self.page_number = page_number
        self.chunk_index = chunk_index
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "dataset_id": self.dataset_id,
            "content": self.content,
            "metadata": self.metadata,
            "embedding_status": self.embedding_status,
            "page_number": self.page_number,
            "chunk_index": self.chunk_index,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class RagVersion:
    """RAG版本模型"""

    def __init__(self,
                 id: str = None,
                 dataset_id: str = None,
                 version: str = None,
                 status: RagVersionStatus = RagVersionStatus.DRAFT,
                 description: str = None,
                 document_count: int = 0,
                 document_unit_count: int = 0,
                 created_by: str = None,
                 reviewed_by: str = None,
                 review_message: str = None,
                 created_at: datetime = None,
                 updated_at: datetime = None,
                 published_at: Optional[datetime] = None):
        self.id = id or str(uuid.uuid4())
        self.dataset_id = dataset_id
        self.version = version
        self.status = status
        self.description = description
        self.document_count = document_count
        self.document_unit_count = document_unit_count
        self.created_by = created_by
        self.reviewed_by = reviewed_by
        self.review_message = review_message
        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()
        self.published_at = published_at

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "dataset_id": self.dataset_id,
            "version": self.version,
            "status": self.status.value,
            "description": self.description,
            "document_count": self.document_count,
            "document_unit_count": self.document_unit_count,
            "created_by": self.created_by,
            "reviewed_by": self.reviewed_by,
            "review_message": self.review_message,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None
        }


class RagSearchRequest:
    """RAG检索请求模型"""

    def __init__(self,
                 query: str,
                 dataset_ids: List[str],
                 search_type: SearchType = SearchType.HYBRID,
                 top_k: int = 10,
                 similarity_threshold: float = 0.7,
                 use_rerank: bool = False,
                 rerank_top_k: int = 5,
                 use_hyde: bool = False):
        self.query = query
        self.dataset_ids = dataset_ids
        self.search_type = search_type
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.use_rerank = use_rerank
        self.rerank_top_k = rerank_top_k
        self.use_hyde = use_hyde

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "query": self.query,
            "dataset_ids": self.dataset_ids,
            "search_type": self.search_type.value,
            "top_k": self.top_k,
            "similarity_threshold": self.similarity_threshold,
            "use_rerank": self.use_rerank,
            "rerank_top_k": self.rerank_top_k,
            "use_hyde": self.use_hyde
        }


class RagSearchResult:
    """RAG检索结果模型"""

    def __init__(self,
                 document_unit_id: str,
                 content: str,
                 similarity_score: float,
                 metadata: Dict[str, Any]):
        self.document_unit_id = document_unit_id
        self.content = content
        self.similarity_score = similarity_score
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "document_unit_id": self.document_unit_id,
            "content": self.content,
            "similarity_score": self.similarity_score,
            "metadata": self.metadata
        }


class RagSearchResponse:
    """RAG检索响应模型"""

    def __init__(self,
                 results: List[RagSearchResult],
                 total_count: int,
                 search_time_ms: int):
        self.results = results
        self.total_count = total_count
        self.search_time_ms = search_time_ms

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "results": [result.to_dict() for result in self.results],
            "total_count": self.total_count,
            "search_time_ms": self.search_time_ms
        }
