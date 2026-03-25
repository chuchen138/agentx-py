from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import os
import tempfile
from app.domain.rag.model import (
    RagDataset, RagDocument, DocumentUnit, RagVersion,
    RagSearchRequest, RagSearchResponse, RagSearchResult,
    RagDatasetStatus, RagVersionStatus, DocumentProcessingStatus, SearchType
)
from app.domain.rag.repository import (
    RagDatasetRepository, RagDocumentRepository, DocumentUnitRepository, RagVersionRepository
)
from app.domain.rag.service import (
    RagDatasetService, RagDocumentService, DocumentUnitService,
    RagVersionService, RagSearchService, RagProcessingService
)
from app.application.file.service.file_storage_app_service import FileStorageAppService
from app.application.file.strategy.rag_file_storage_strategy import RagFileStorageStrategy


class RagDatasetAppService(RagDatasetService):
    """RAG数据集应用服务"""

    def __init__(self,
                 dataset_repository: RagDatasetRepository):
        self.dataset_repository = dataset_repository

    def create_dataset(self, user_id: str, name: str, description: str) -> RagDataset:
        """创建数据集"""
        dataset = RagDataset(
            user_id=user_id,
            name=name,
            description=description
        )
        return self.dataset_repository.create(dataset)

    def get_dataset(self, dataset_id: str, user_id: str) -> Optional[RagDataset]:
        """获取数据集"""
        dataset = self.dataset_repository.get_by_id(dataset_id)
        if dataset and dataset.user_id == user_id:
            return dataset
        return None

    def list_datasets(self, user_id: str) -> List[RagDataset]:
        """列出用户的数据集"""
        return self.dataset_repository.get_by_user_id(user_id)

    def update_dataset(self, dataset_id: str, user_id: str, name: str = None, description: str = None) -> RagDataset:
        """更新数据集"""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            raise ValueError("Dataset not found or access denied")
        
        if name:
            dataset.name = name
        if description:
            dataset.description = description
        dataset.updated_at = datetime.utcnow()
        
        return self.dataset_repository.update(dataset)

    def delete_dataset(self, dataset_id: str, user_id: str) -> bool:
        """删除数据集"""
        dataset = self.get_dataset(dataset_id, user_id)
        if not dataset:
            return False
        
        return self.dataset_repository.delete(dataset_id)


class RagDocumentAppService(RagDocumentService):
    """RAG文档应用服务"""

    def __init__(self,
                 document_repository: RagDocumentRepository,
                 dataset_repository: RagDatasetRepository,
                 file_storage_service: FileStorageAppService,
                 rag_file_strategy: RagFileStorageStrategy,
                 processing_service: RagProcessingService):
        self.document_repository = document_repository
        self.dataset_repository = dataset_repository
        self.file_storage_service = file_storage_service
        self.rag_file_strategy = rag_file_strategy
        self.processing_service = processing_service

    def upload_document(self, dataset_id: str, user_id: str, file_data: bytes, filename: str, file_type: str) -> RagDocument:
        """上传文档"""
        # 验证数据集存在且属于用户
        dataset = self.dataset_repository.get_by_id(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise ValueError("Dataset not found or access denied")
        
        # 保存文件
        metadata = {
            "user_id": user_id,
            "dataset_id": dataset_id,
            "original_filename": filename
        }
        file_record = self.rag_file_strategy.save(file_data, metadata)
        
        # 创建文档记录
        document = RagDocument(
            dataset_id=dataset_id,
            file_id=file_record.id,
            file_name=filename,
            file_path=file_record.file_path,
            file_url=file_record.file_url,
            file_size=file_record.file_size,
            mime_type=file_record.mime_type
        )
        document = self.document_repository.create(document)
        
        # 异步处理文档
        # 这里应该使用异步任务队列，暂时同步处理
        try:
            self.processing_service.process_document(document.id)
        except Exception as e:
            # 记录错误但不影响上传
            document.error_message = str(e)
            document.processing_status = DocumentProcessingStatus.UPLOADED
            self.document_repository.update(document)
        
        return document

    def get_document(self, document_id: str, user_id: str) -> Optional[RagDocument]:
        """获取文档"""
        document = self.document_repository.get_by_id(document_id)
        if not document:
            return None
        
        dataset = self.dataset_repository.get_by_id(document.dataset_id)
        if dataset and dataset.user_id == user_id:
            return document
        return None

    def list_documents(self, dataset_id: str, user_id: str) -> List[RagDocument]:
        """列出数据集中的文档"""
        dataset = self.dataset_repository.get_by_id(dataset_id)
        if not dataset or dataset.user_id != user_id:
            return []
        
        return self.document_repository.get_by_dataset_id(dataset_id)

    def delete_document(self, document_id: str, user_id: str) -> bool:
        """删除文档"""
        document = self.get_document(document_id, user_id)
        if not document:
            return False
        
        return self.document_repository.delete(document_id)

    def reprocess_document(self, document_id: str, user_id: str) -> RagDocument:
        """重新处理文档"""
        document = self.get_document(document_id, user_id)
        if not document:
            raise ValueError("Document not found or access denied")
        
        # 重置状态
        document.processing_status = DocumentProcessingStatus.UPLOADED
        document.error_message = None
        self.document_repository.update(document)
        
        # 重新处理
        return self.processing_service.process_document(document_id)


class DocumentUnitAppService(DocumentUnitService):
    """文档单元应用服务"""

    def __init__(self,
                 unit_repository: DocumentUnitRepository,
                 document_repository: RagDocumentRepository,
                 dataset_repository: RagDatasetRepository):
        self.unit_repository = unit_repository
        self.document_repository = document_repository
        self.dataset_repository = dataset_repository

    def get_document_unit(self, unit_id: str, user_id: str) -> Optional[DocumentUnit]:
        """获取文档单元"""
        unit = self.unit_repository.get_by_id(unit_id)
        if not unit:
            return None
        
        document = self.document_repository.get_by_id(unit.document_id)
        if not document:
            return None
        
        dataset = self.dataset_repository.get_by_id(document.dataset_id)
        if dataset and dataset.user_id == user_id:
            return unit
        return None

    def list_document_units(self, document_id: str, user_id: str) -> List[DocumentUnit]:
        """列出文档的单元"""
        document = self.document_repository.get_by_id(document_id)
        if not document:
            return []
        
        dataset = self.dataset_repository.get_by_id(document.dataset_id)
        if not dataset or dataset.user_id != user_id:
            return []
        
        return self.unit_repository.get_by_document_id(document_id)

    def update_document_unit(self, unit_id: str, user_id: str, content: str) -> DocumentUnit:
        """更新文档单元内容"""
        unit = self.get_document_unit(unit_id, user_id)
        if not unit:
            raise ValueError("Document unit not found or access denied")
        
        unit.content = content
        unit.updated_at = datetime.utcnow()
        # 重置嵌入状态
        unit.embedding_status = "PENDING"
        
        return self.unit_repository.update(unit)

    def reembed_document_unit(self, unit_id: str, user_id: str) -> DocumentUnit:
        """重新向量化文档单元"""
        unit = self.get_document_unit(unit_id, user_id)
        if not unit:
            raise ValueError("Document unit not found or access denied")
        
        unit.embedding_status = "PROCESSING"
        unit = self.unit_repository.update(unit)
        
        # 这里应该调用嵌入服务
        # 暂时模拟
        unit.embedding_status = "COMPLETED"
        unit.updated_at = datetime.utcnow()
        
        return self.unit_repository.update(unit)


class RagVersionAppService(RagVersionService):
    """RAG版本应用服务"""

    def __init__(self,
                 version_repository: RagVersionRepository,
                 dataset_repository: RagDatasetRepository,
                 document_repository: RagDocumentRepository,
                 unit_repository: DocumentUnitRepository):
        self.version_repository = version_repository
        self.dataset_repository = dataset_repository
        self.document_repository = document_repository
        self.unit_repository = unit_repository

    def create_version(self, dataset_id: str, user_id: str, version: str, description: str) -> RagVersion:
        """创建版本"""
        dataset = self.dataset_repository.get_by_id(dataset_id)
        if not dataset or dataset.user_id != user_id:
            raise ValueError("Dataset not found or access denied")
        
        # 统计文档和单元数量
        documents = self.document_repository.get_by_dataset_id(dataset_id)
        document_count = len(documents)
        
        unit_count = 0
        for doc in documents:
            units = self.unit_repository.get_by_document_id(doc.id)
            unit_count += len(units)
        
        version_obj = RagVersion(
            dataset_id=dataset_id,
            version=version,
            description=description,
            document_count=document_count,
            document_unit_count=unit_count,
            created_by=user_id
        )
        
        return self.version_repository.create(version_obj)

    def get_version(self, version_id: str, user_id: str) -> Optional[RagVersion]:
        """获取版本"""
        version = self.version_repository.get_by_id(version_id)
        if not version:
            return None
        
        dataset = self.dataset_repository.get_by_id(version.dataset_id)
        if dataset and dataset.user_id == user_id:
            return version
        return None

    def list_versions(self, dataset_id: str, user_id: str) -> List[RagVersion]:
        """列出数据集的版本"""
        dataset = self.dataset_repository.get_by_id(dataset_id)
        if not dataset or dataset.user_id != user_id:
            return []
        
        return self.version_repository.get_by_dataset_id(dataset_id)

    def submit_for_review(self, version_id: str, user_id: str) -> RagVersion:
        """提交审核"""
        version = self.get_version(version_id, user_id)
        if not version:
            raise ValueError("Version not found or access denied")
        
        version.status = RagVersionStatus.PENDING_REVIEW
        version.updated_at = datetime.utcnow()
        
        return self.version_repository.update(version)

    def review_version(self, version_id: str, reviewer_id: str, status: str, review_message: str = None) -> RagVersion:
        """审核版本"""
        version = self.version_repository.get_by_id(version_id)
        if not version:
            raise ValueError("Version not found")
        
        # 这里应该验证审核者权限
        
        version.status = RagVersionStatus(status)
        version.reviewed_by = reviewer_id
        version.review_message = review_message
        version.updated_at = datetime.utcnow()
        
        if status == RagVersionStatus.PUBLISHED.value:
            version.published_at = datetime.utcnow()
        
        return self.version_repository.update(version)

    def list_published_versions(self) -> List[RagVersion]:
        """列出已发布的版本"""
        return self.version_repository.get_published_versions()


class RagSearchAppService(RagSearchService):
    """RAG检索应用服务"""

    def __init__(self,
                 unit_repository: DocumentUnitRepository):
        self.unit_repository = unit_repository

    def search(self, search_request: RagSearchRequest) -> RagSearchResponse:
        """执行检索"""
        import time
        start_time = time.time()
        
        results = []
        if search_request.search_type == SearchType.VECTOR:
            results = self.vector_search(
                search_request.query,
                search_request.dataset_ids,
                search_request.top_k,
                search_request.similarity_threshold
            )
        elif search_request.search_type == SearchType.KEYWORD:
            results = self.keyword_search(
                search_request.query,
                search_request.dataset_ids,
                search_request.top_k
            )
        else:  # HYBRID
            results = self.hybrid_search(
                search_request.query,
                search_request.dataset_ids,
                search_request.top_k,
                search_request.similarity_threshold
            )
        
        # 重排序
        if search_request.use_rerank and results:
            # 这里应该实现重排序逻辑
            pass
        
        search_time_ms = int((time.time() - start_time) * 1000)
        
        return RagSearchResponse(
            results=results,
            total_count=len(results),
            search_time_ms=search_time_ms
        )

    def vector_search(self, query: str, dataset_ids: List[str], top_k: int, threshold: float) -> List[RagSearchResult]:
        """向量检索"""
        # 这里应该实现真正的向量检索
        # 暂时返回模拟结果
        return []

    def keyword_search(self, query: str, dataset_ids: List[str], top_k: int) -> List[RagSearchResult]:
        """关键词检索"""
        # 这里应该实现真正的关键词检索
        # 暂时返回模拟结果
        return []

    def hybrid_search(self, query: str, dataset_ids: List[str], top_k: int, threshold: float) -> List[RagSearchResult]:
        """混合检索"""
        # 这里应该实现真正的混合检索
        # 暂时返回模拟结果
        return []


class RagProcessingAppService(RagProcessingService):
    """RAG处理应用服务"""

    def __init__(self,
                 document_repository: RagDocumentRepository,
                 unit_repository: DocumentUnitRepository):
        self.document_repository = document_repository
        self.unit_repository = unit_repository

    def process_document(self, document_id: str) -> RagDocument:
        """处理文档"""
        document = self.document_repository.get_by_id(document_id)
        if not document:
            raise ValueError("Document not found")
        
        try:
            # 更新状态为OCR处理中
            self.document_repository.update_processing_status(
                document_id, DocumentProcessingStatus.OCR_PROCESSING.value
            )
            
            # 提取文本
            text = self.extract_text(document.file_path, document.mime_type)
            
            # 更新状态为OCR完成
            self.document_repository.update_processing_status(
                document_id, DocumentProcessingStatus.OCR_COMPLETED.value
            )
            
            # 分割为文档单元
            units = self.split_into_units(text, document.id, document.dataset_id)
            
            # 更新状态为向量化处理中
            self.document_repository.update_processing_status(
                document_id, DocumentProcessingStatus.EMBEDDING_PROCESSING.value
            )
            
            # 向量化文档单元
            embedded_units = self.embed_document_units(units)
            
            # 更新文档单元数量
            document.unit_count = len(embedded_units)
            document.processing_status = DocumentProcessingStatus.COMPLETED
            document.updated_at = datetime.utcnow()
            
            return self.document_repository.update(document)
            
        except Exception as e:
            # 更新状态为失败
            self.document_repository.update_processing_status(
                document_id, DocumentProcessingStatus.OCR_FAILED.value, str(e)
            )
            document.error_message = str(e)
            document.processing_status = DocumentProcessingStatus.OCR_FAILED
            document.updated_at = datetime.utcnow()
            return self.document_repository.update(document)

    def extract_text(self, file_path: str, file_type: str) -> str:
        """提取文本"""
        # 这里应该根据文件类型实现不同的文本提取逻辑
        # 暂时返回模拟文本
        return "This is a test document content."

    def split_into_units(self, text: str, document_id: str, dataset_id: str) -> List[DocumentUnit]:
        """分割为文档单元"""
        # 简单分割为段落
        paragraphs = text.split('\n')
        units = []
        
        for i, paragraph in enumerate(paragraphs):
            if paragraph.strip():
                unit = DocumentUnit(
                    document_id=document_id,
                    dataset_id=dataset_id,
                    content=paragraph.strip(),
                    metadata={"chunk_index": i},
                    chunk_index=i
                )
                units.append(unit)
                # 保存到数据库
                self.unit_repository.create(unit)
        
        return units

    def embed_document_units(self, document_units: List[DocumentUnit]) -> List[DocumentUnit]:
        """向量化文档单元"""
        # 这里应该调用嵌入模型
        # 暂时模拟
        for unit in document_units:
            unit.embedding_status = "COMPLETED"
            unit.updated_at = datetime.utcnow()
            self.unit_repository.update(unit)
        
        return document_units
