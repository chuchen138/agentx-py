from typing import List, Optional, Dict, Any
from abc import ABC, abstractmethod
from app.domain.rag.model import RagDataset, RagDocument, DocumentUnit, RagVersion


class RagDatasetRepository(ABC):
    """RAG数据集仓库接口"""

    @abstractmethod
    def create(self, dataset: RagDataset) -> RagDataset:
        """创建数据集"""
        pass

    @abstractmethod
    def get_by_id(self, dataset_id: str) -> Optional[RagDataset]:
        """根据ID获取数据集"""
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: str) -> List[RagDataset]:
        """根据用户ID获取数据集"""
        pass

    @abstractmethod
    def update(self, dataset: RagDataset) -> RagDataset:
        """更新数据集"""
        pass

    @abstractmethod
    def delete(self, dataset_id: str) -> bool:
        """删除数据集"""
        pass

    @abstractmethod
    def update_statistics(self, dataset_id: str) -> bool:
        """更新数据集统计信息"""
        pass


class RagDocumentRepository(ABC):
    """RAG文档仓库接口"""

    @abstractmethod
    def create(self, document: RagDocument) -> RagDocument:
        """创建文档"""
        pass

    @abstractmethod
    def get_by_id(self, document_id: str) -> Optional[RagDocument]:
        """根据ID获取文档"""
        pass

    @abstractmethod
    def get_by_dataset_id(self, dataset_id: str) -> List[RagDocument]:
        """根据数据集ID获取文档"""
        pass

    @abstractmethod
    def update(self, document: RagDocument) -> RagDocument:
        """更新文档"""
        pass

    @abstractmethod
    def delete(self, document_id: str) -> bool:
        """删除文档"""
        pass

    @abstractmethod
    def update_processing_status(self, document_id: str, status: str, error_message: str = None) -> bool:
        """更新文档处理状态"""
        pass


class DocumentUnitRepository(ABC):
    """文档单元仓库接口"""

    @abstractmethod
    def create(self, document_unit: DocumentUnit) -> DocumentUnit:
        """创建文档单元"""
        pass

    @abstractmethod
    def get_by_id(self, unit_id: str) -> Optional[DocumentUnit]:
        """根据ID获取文档单元"""
        pass

    @abstractmethod
    def get_by_document_id(self, document_id: str) -> List[DocumentUnit]:
        """根据文档ID获取文档单元"""
        pass

    @abstractmethod
    def get_by_dataset_id(self, dataset_id: str) -> List[DocumentUnit]:
        """根据数据集ID获取文档单元"""
        pass

    @abstractmethod
    def update(self, document_unit: DocumentUnit) -> DocumentUnit:
        """更新文档单元"""
        pass

    @abstractmethod
    def delete(self, unit_id: str) -> bool:
        """删除文档单元"""
        pass

    @abstractmethod
    def update_embedding_status(self, unit_id: str, status: str, embedding_vector: List[float] = None) -> bool:
        """更新嵌入状态"""
        pass

    @abstractmethod
    def search_by_vector(self, query_vector: List[float], dataset_ids: List[str], top_k: int, threshold: float) -> List[Dict[str, Any]]:
        """向量检索"""
        pass

    @abstractmethod
    def search_by_keyword(self, query: str, dataset_ids: List[str], top_k: int) -> List[Dict[str, Any]]:
        """关键词检索"""
        pass


class RagVersionRepository(ABC):
    """RAG版本仓库接口"""

    @abstractmethod
    def create(self, version: RagVersion) -> RagVersion:
        """创建版本"""
        pass

    @abstractmethod
    def get_by_id(self, version_id: str) -> Optional[RagVersion]:
        """根据ID获取版本"""
        pass

    @abstractmethod
    def get_by_dataset_id(self, dataset_id: str) -> List[RagVersion]:
        """根据数据集ID获取版本"""
        pass

    @abstractmethod
    def get_published_versions(self) -> List[RagVersion]:
        """获取已发布的版本"""
        pass

    @abstractmethod
    def update(self, version: RagVersion) -> RagVersion:
        """更新版本"""
        pass

    @abstractmethod
    def delete(self, version_id: str) -> bool:
        """删除版本"""
        pass

    @abstractmethod
    def update_status(self, version_id: str, status: str, reviewed_by: str = None, review_message: str = None) -> bool:
        """更新版本状态"""
        pass
