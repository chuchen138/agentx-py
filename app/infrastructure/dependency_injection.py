from fastapi import Depends
from app.application.rag.rag_app_service import (
    RagDatasetAppService, RagDocumentAppService, DocumentUnitAppService,
    RagVersionAppService, RagSearchAppService, RagProcessingAppService
)
from app.application.file.service.file_storage_app_service import FileStorageAppService
from app.application.file.strategy.rag_file_storage_strategy import RagFileStorageStrategy
from app.domain.tool.service import ToolDomainService, ToolVersionDomainService, UserToolDomainService
from app.application.tool.tool_app_service import ToolAppService, ToolVersionService, ToolStateStateMachineAppService





async def get_rag_services():
    # 这里应该使用实际的仓库实现
    # 暂时使用模拟实现
    class MockRagDatasetRepository:
        def create(self, dataset):
            return dataset
        def get_by_id(self, dataset_id):
            return None
        def get_by_user_id(self, user_id):
            return []
        def update(self, dataset):
            return dataset
        def delete(self, dataset_id):
            return True
        def update_statistics(self, dataset_id):
            return True
    
    class MockRagDocumentRepository:
        def create(self, document):
            return document
        def get_by_id(self, document_id):
            return None
        def get_by_dataset_id(self, dataset_id):
            return []
        def update(self, document):
            return document
        def delete(self, document_id):
            return True
        def update_processing_status(self, document_id, status, error_message=None):
            return True
    
    class MockDocumentUnitRepository:
        def create(self, unit):
            return unit
        def get_by_id(self, unit_id):
            return None
        def get_by_document_id(self, document_id):
            return []
        def get_by_dataset_id(self, dataset_id):
            return []
        def update(self, unit):
            return unit
        def delete(self, unit_id):
            return True
        def update_embedding_status(self, unit_id, status, embedding_vector=None):
            return True
        def search_by_vector(self, query_vector, dataset_ids, top_k, threshold):
            return []
        def search_by_keyword(self, query, dataset_ids, top_k):
            return []
    
    class MockRagVersionRepository:
        def create(self, version):
            return version
        def get_by_id(self, version_id):
            return None
        def get_by_dataset_id(self, dataset_id):
            return []
        def get_published_versions(self):
            return []
        def update(self, version):
            return version
        def delete(self, version_id):
            return True
        def update_status(self, version_id, status, reviewed_by=None, review_message=None):
            return True
    
    # 创建仓库实例
    dataset_repository = MockRagDatasetRepository()
    document_repository = MockRagDocumentRepository()
    unit_repository = MockDocumentUnitRepository()
    version_repository = MockRagVersionRepository()
    
    # 创建文件存储服务
    file_storage_service = FileStorageAppService()
    rag_file_strategy = RagFileStorageStrategy()
    
    # 创建处理服务
    processing_service = RagProcessingAppService(
        document_repository=document_repository,
        unit_repository=unit_repository
    )
    
    # 创建服务实例
    dataset_service = RagDatasetAppService(dataset_repository=dataset_repository)
    document_service = RagDocumentAppService(
        document_repository=document_repository,
        dataset_repository=dataset_repository,
        file_storage_service=file_storage_service,
        rag_file_strategy=rag_file_strategy,
        processing_service=processing_service
    )
    unit_service = DocumentUnitAppService(
        unit_repository=unit_repository,
        document_repository=document_repository,
        dataset_repository=dataset_repository
    )
    version_service = RagVersionAppService(
        version_repository=version_repository,
        dataset_repository=dataset_repository,
        document_repository=document_repository,
        unit_repository=unit_repository
    )
    search_service = RagSearchAppService(unit_repository=unit_repository)
    
    return {
        "dataset_service": dataset_service,
        "document_service": document_service,
        "unit_service": unit_service,
        "version_service": version_service,
        "search_service": search_service,
        "processing_service": processing_service
    }


