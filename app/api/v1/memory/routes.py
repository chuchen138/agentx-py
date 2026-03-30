from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.api.middleware.auth import get_current_user
from app.domain.user.model import UserModel
from app.domain.memory.model.memory_item import MemoryItemDTO, MemoryResult, CreateMemoryRequest, QueryMemoryRequest
from app.domain.memory.repository import SQLAlchemyMemoryItemRepository, SQLAlchemyVectorStoreRepository
from app.domain.memory.service import MemoryDomainService, MemoryExtractorService
from app.application.memory.memory_app_service import MemoryAppService
from app.core.database import get_db
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

router = APIRouter()

# 依赖项
def get_memory_app_service(db: Session = Depends(get_db)):
    memory_item_repo = SQLAlchemyMemoryItemRepository(db)
    vector_store_repo = SQLAlchemyVectorStoreRepository(db)
    memory_domain_service = MemoryDomainService(memory_item_repo, vector_store_repo)
    memory_extractor_service = MemoryExtractorService(memory_domain_service)
    return MemoryAppService(memory_domain_service, memory_extractor_service)

# 路由
@router.post("", response_model=uuid.UUID)
def create_memory(
    request: CreateMemoryRequest,
    current_user: UserModel = Depends(get_current_user),
    memory_app_service: MemoryAppService = Depends(get_memory_app_service)
):
    """手动创建记忆"""
    try:
        memory_id = memory_app_service.create_memory(
            user_id=str(current_user.id),
            request=request
        )
        return memory_id
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("", response_model=dict)
def list_memories(
    page: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(20, ge=1, le=100, description="每页大小"),
    type: Optional[str] = Query(None, description="记忆类型"),
    tags: Optional[List[str]] = Query(None, description="标签列表"),
    importanceMin: Optional[float] = Query(None, ge=0.0, le=1.0, description="最小重要性"),
    current_user: UserModel = Depends(get_current_user),
    memory_app_service: MemoryAppService = Depends(get_memory_app_service)
):
    """分页列出用户记忆"""
    return memory_app_service.list_user_memories(
        user_id=str(current_user.id),
        page=page,
        page_size=pageSize,
        memory_type=type,
        tags=tags,
        importance_min=importanceMin
    )

@router.get("/{itemId}", response_model=MemoryItemDTO)
def get_memory(
    itemId: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    memory_app_service: MemoryAppService = Depends(get_memory_app_service)
):
    """获取记忆详情"""
    memory = memory_app_service.get_memory_by_id(itemId)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    
    # 验证记忆归属
    if memory.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权访问此记忆"
        )
    
    return memory

@router.delete("/{itemId}", response_model=bool)
def delete_memory(
    itemId: uuid.UUID,
    current_user: UserModel = Depends(get_current_user),
    memory_app_service: MemoryAppService = Depends(get_memory_app_service)
):
    """归档（软删除）记忆"""
    # 验证记忆归属
    memory = memory_app_service.get_memory_by_id(itemId)
    if not memory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="记忆不存在"
        )
    
    if memory.user_id != str(current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权操作此记忆"
        )
    
    return memory_app_service.delete_memory(itemId)

@router.get("/search", response_model=List[MemoryResult])
def search_memories(
    query: str = Query(..., description="搜索查询"),
    topK: int = Query(16, ge=1, le=100, description="返回结果数量"),
    current_user: UserModel = Depends(get_current_user),
    memory_app_service: MemoryAppService = Depends(get_memory_app_service)
):
    """搜索记忆"""
    return memory_app_service.search_memories(
        user_id=str(current_user.id),
        query=query,
        top_k=topK
    )
