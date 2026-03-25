from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from typing import List, Optional
from app.application.rag.rag_app_service import (
    RagDatasetAppService, RagDocumentAppService, DocumentUnitAppService,
    RagVersionAppService, RagSearchAppService
)
from app.domain.rag.model import (
    RagDataset, RagDocument, DocumentUnit, RagVersion,
    RagSearchRequest, RagSearchResponse, SearchType
)
from app.infrastructure.dependency_injection import get_rag_services
from app.api.middleware.auth import get_current_user
from app.domain.user.model import User

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/datasets", response_model=RagDataset)
def create_dataset(
    name: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """创建RAG数据集"""
    dataset_service = services["dataset_service"]
    return dataset_service.create_dataset(
        user_id=current_user.id,
        name=name,
        description=description
    )


@router.get("/datasets", response_model=List[RagDataset])
def list_datasets(
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """列出用户的RAG数据集"""
    dataset_service = services["dataset_service"]
    return dataset_service.list_datasets(user_id=current_user.id)


@router.get("/datasets/{dataset_id}", response_model=RagDataset)
def get_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """获取RAG数据集"""
    dataset_service = services["dataset_service"]
    dataset = dataset_service.get_dataset(dataset_id, current_user.id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.put("/datasets/{dataset_id}", response_model=RagDataset)
def update_dataset(
    dataset_id: str,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """更新RAG数据集"""
    dataset_service = services["dataset_service"]
    return dataset_service.update_dataset(
        dataset_id=dataset_id,
        user_id=current_user.id,
        name=name,
        description=description
    )


@router.delete("/datasets/{dataset_id}")
def delete_dataset(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """删除RAG数据集"""
    dataset_service = services["dataset_service"]
    success = dataset_service.delete_dataset(dataset_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"message": "Dataset deleted successfully"}


@router.post("/datasets/{dataset_id}/documents", response_model=RagDocument)
def upload_document(
    dataset_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """上传RAG文档"""
    document_service = services["document_service"]
    file_data = file.file.read()
    return document_service.upload_document(
        dataset_id=dataset_id,
        user_id=current_user.id,
        file_data=file_data,
        filename=file.filename,
        file_type=file.content_type
    )


@router.get("/datasets/{dataset_id}/documents", response_model=List[RagDocument])
def list_documents(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """列出数据集中的文档"""
    document_service = services["document_service"]
    return document_service.list_documents(dataset_id, current_user.id)


@router.get("/documents/{document_id}", response_model=RagDocument)
def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """获取文档"""
    document_service = services["document_service"]
    document = document_service.get_document(document_id, current_user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/documents/{document_id}")
def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """删除文档"""
    document_service = services["document_service"]
    success = document_service.delete_document(document_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}


@router.post("/documents/{document_id}/reprocess", response_model=RagDocument)
def reprocess_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """重新处理文档"""
    document_service = services["document_service"]
    return document_service.reprocess_document(document_id, current_user.id)


@router.get("/documents/{document_id}/units", response_model=List[DocumentUnit])
def list_document_units(
    document_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """列出文档的单元"""
    unit_service = services["unit_service"]
    return unit_service.list_document_units(document_id, current_user.id)


@router.get("/units/{unit_id}", response_model=DocumentUnit)
def get_document_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """获取文档单元"""
    unit_service = services["unit_service"]
    unit = unit_service.get_document_unit(unit_id, current_user.id)
    if not unit:
        raise HTTPException(status_code=404, detail="Document unit not found")
    return unit


@router.put("/units/{unit_id}", response_model=DocumentUnit)
def update_document_unit(
    unit_id: str,
    content: str = Form(...),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """更新文档单元内容"""
    unit_service = services["unit_service"]
    return unit_service.update_document_unit(unit_id, current_user.id, content)


@router.post("/units/{unit_id}/reembed", response_model=DocumentUnit)
def reembed_document_unit(
    unit_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """重新向量化文档单元"""
    unit_service = services["unit_service"]
    return unit_service.reembed_document_unit(unit_id, current_user.id)


@router.post("/datasets/{dataset_id}/versions", response_model=RagVersion)
def create_version(
    dataset_id: str,
    version: str = Form(...),
    description: str = Form(...),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """创建RAG版本"""
    version_service = services["version_service"]
    return version_service.create_version(
        dataset_id=dataset_id,
        user_id=current_user.id,
        version=version,
        description=description
    )


@router.get("/datasets/{dataset_id}/versions", response_model=List[RagVersion])
def list_versions(
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """列出数据集的版本"""
    version_service = services["version_service"]
    return version_service.list_versions(dataset_id, current_user.id)


@router.get("/versions/{version_id}", response_model=RagVersion)
def get_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """获取RAG版本"""
    version_service = services["version_service"]
    version = version_service.get_version(version_id, current_user.id)
    if not version:
        raise HTTPException(status_code=404, detail="Version not found")
    return version


@router.post("/versions/{version_id}/submit", response_model=RagVersion)
def submit_version(
    version_id: str,
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """提交版本审核"""
    version_service = services["version_service"]
    return version_service.submit_for_review(version_id, current_user.id)


@router.post("/versions/{version_id}/review", response_model=RagVersion)
def review_version(
    version_id: str,
    status: str = Form(...),
    review_message: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    services = Depends(get_rag_services)
):
    """审核版本"""
    version_service = services["version_service"]
    return version_service.review_version(
        version_id=version_id,
        reviewer_id=current_user.id,
        status=status,
        review_message=review_message
    )


@router.get("/market/versions", response_model=List[RagVersion])
def list_published_versions(
    services = Depends(get_rag_services)
):
    """列出已发布的版本"""
    version_service = services["version_service"]
    return version_service.list_published_versions()


@router.post("/search", response_model=RagSearchResponse)
def search(
    search_request: RagSearchRequest,
    services = Depends(get_rag_services)
):
    """执行RAG检索"""
    search_service = services["search_service"]
    return search_service.search(search_request)
