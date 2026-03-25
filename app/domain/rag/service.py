from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from app.domain.rag.model import (
    RagDataset, RagDocument, DocumentUnit, RagVersion,
    RagSearchRequest, RagSearchResponse, RagSearchResult
)


class RagDatasetService(ABC):
    """RAG数据集服务接口"""

    @abstractmethod
    def create_dataset(self, user_id: str, name: str, description: str) -> RagDataset:
        """创建数据集"""
        pass

    @abstractmethod
    def get_dataset(self, dataset_id: str, user_id: str) -> Optional[RagDataset]:
        """获取数据集"""
        pass

    @abstractmethod
    def list_datasets(self, user_id: str) -> List[RagDataset]:
        """列出用户的数据集"""
        pass

    @abstractmethod
    def update_dataset(self, dataset_id: str, user_id: str, name: str = None, description: str = None) -> RagDataset:
        """更新数据集"""
        pass

    @abstractmethod
    def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """删除数据集"""
        pass


class RagDocumentService(ABC):
    """RAG文档服务接口"""

    @abstractmethod
    def upload_document(self, dataset_id: str, user_id: str, file_data: bytes, filename: str, file_type: str) -> RagDocument:
        """上传文档"""
        pass

    @abstractmethod
    def get_document(self, document_id: str, user_id: str) -> Optional[RagDocument]:
        """获取文档"""
        pass

    @abstractmethod
    def list_documents(self, dataset_id: str, user_id: str) -> List[RagDocument]:
        """列出数据集中的文档"""
        pass

    @abstractmethod
    def delete_document(self, document_id: str, user_id: str) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    def reprocess_document(self, document_id: str, user_id: str) -> RagDocument:
        """重新处理文档"""
        pass


class DocumentUnitService(ABC):
    """文档单元服务接口"""

    @abstractmethod
    def get_document_unit(self, unit_id: str, user_id: str) -> Optional[DocumentUnit]:
        """获取文档单元"""
        pass

    @abstractmethod
    def list_document_units(self, document_id: str, user_id: str) -> List[DocumentUnit]:
        """列出文档的单元"""
        pass

    @abstractmethod
    def update_document_unit(self, unit_id: str, user_id: str, content: str) -> DocumentUnit:
        """更新文档单元内容"""
        pass

    @abstractmethod
    def reembed_document_unit(self, unit_id: str, user_id: str) -> DocumentUnit:
        """重新向量化文档单元"""
        pass


class RagVersionService(ABC):
    """RAG版本服务接口"""

    @abstractmethod
    def create_version(self, dataset_id: str, user_id: str, version: str, description: str) -> RagVersion:
        """创建版本"""
        pass

    @abstractmethod
    def get_version(self, version_id: str, user_id: str) -> Optional[RagVersion]:
        """获取版本"""
        pass

    @abstractmethod
    def list_versions(self, dataset_id: str, user_id: str) -> List[RagVersion]:
        """列出数据集的版本"""
        pass

    @abstractmethod
    def submit_for_review(self, version_id: str, user_id: str) -> RagVersion:
        """提交审核"""
        pass

    @abstractmethod
    def review_version(self, version_id: str, reviewer_id: str, status: str, review_message: str = None) -> RagVersion:
        """审核版本"""
        pass

    @abstractmethod
    def list_published_versions(self) -> List[RagVersion]:
        """列出已发布的版本"""
        pass


class RagSearchService(ABC):
    """RAG检索服务接口"""

    @abstractmethod
    def search(self, search_request: RagSearchRequest) -> RagSearchResponse:
        """执行检索"""
        pass

    @abstractmethod
    def vector_search(self, query: str, dataset_ids: List[str], top_k: int, threshold: float) -> List[RagSearchResult]:
        """向量检索"""
        pass

    @abstractmethod
    def keyword_search(self, query: str, dataset_ids: List[str], top_k: int) -> List[RagSearchResult]:
        """关键词检索"""
        pass

    @abstractmethod
    def hybrid_search(self, query: str, dataset_ids: List[str], top_k: int, threshold: float) -> List[RagSearchResult]:
        """混合检索"""
        pass


class RagProcessingService(ABC):
    """RAG处理服务接口"""

    @abstractmethod
    def process_document(self, document_id: str) -> RagDocument:
        """处理文档"""
        pass

    @abstractmethod
    def extract_text(self, file_path: str, file_type: str) -> str:
        """提取文本"""
        pass

    @abstractmethod
    def split_into_units(self, text: str, document_id: str, dataset_id: str) -> List[DocumentUnit]:
        """分割为文档单元"""
        pass

    @abstractmethod
    def embed_document_units(self, document_units: List[DocumentUnit]) -> List[DocumentUnit]:
        """向量化文档单元"""
        pass
