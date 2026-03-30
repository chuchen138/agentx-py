from typing import List, Optional, Dict, Any, Tuple
import uuid
from app.domain.memory.service import MemoryDomainService, MemoryExtractorService
from app.domain.memory.model.memory_item import MemoryItemModel, MemoryItemDTO, MemoryResult, CreateMemoryRequest, CandidateMemory
from app.domain.memory.constant.memory_type import MemoryType

class MemoryAppService:
    """记忆应用服务"""
    
    def __init__(self, memory_domain_service: MemoryDomainService, 
                 memory_extractor_service: MemoryExtractorService):
        self.memory_domain_service = memory_domain_service
        self.memory_extractor_service = memory_extractor_service
    
    def list_user_memories(self, user_id: str, page: int = 1, page_size: int = 20, 
                          memory_type: Optional[str] = None, 
                          tags: Optional[List[str]] = None, 
                          importance_min: Optional[float] = None) -> Dict[str, Any]:
        """分页列出用户记忆"""
        memories, total = self.memory_domain_service.get_memories_by_user_id(
            user_id=user_id,
            page=page,
            page_size=page_size,
            memory_type=memory_type,
            tags=tags,
            importance_min=importance_min
        )
        
        # 转换为 DTO
        memory_dtos = [self._to_dto(memory) for memory in memories]
        
        return {
            "records": memory_dtos,
            "total": total,
            "size": page_size,
            "current": page
        }
    
    def create_memory(self, user_id: str, request: CreateMemoryRequest, 
                     source_session_id: Optional[str] = None) -> uuid.UUID:
        """手动创建记忆"""
        # 验证记忆类型
        try:
            MemoryType.fromCode(request.type)
        except ValueError:
            raise ValueError(f"Invalid memory type: {request.type}")
        
        # 创建候选记忆
        candidate = CandidateMemory(
            type=request.type,
            text=request.text,
            importance=request.importance,
            tags=request.tags,
            data=request.data
        )
        
        # 保存记忆
        saved_memories = self.memory_domain_service.save_memories(
            user_id=user_id,
            candidate_memories=[candidate],
            source_session_id=source_session_id
        )
        
        return saved_memories[0].id if saved_memories else None
    
    def get_memory_by_id(self, item_id: uuid.UUID) -> Optional[MemoryItemDTO]:
        """获取记忆详情"""
        memory = self.memory_domain_service.get_memory_by_id(item_id)
        if memory:
            return self._to_dto(memory)
        return None
    
    def delete_memory(self, item_id: uuid.UUID) -> bool:
        """归档记忆（软删除）"""
        return self.memory_domain_service.archive_memory(item_id)
    
    def extract_and_save_memories(self, user_id: str, message: str, 
                                source_session_id: Optional[str] = None, 
                                conversation_history: Optional[List[Dict[str, str]]] = None) -> List[MemoryItemDTO]:
        """自动提取和保存记忆"""
        saved_memories = self.memory_extractor_service.extract_and_save(
            user_id=user_id,
            message=message,
            source_session_id=source_session_id,
            conversation_history=conversation_history
        )
        
        return [self._to_dto(memory) for memory in saved_memories]
    
    def search_memories(self, user_id: str, query: str, top_k: int = 16) -> List[MemoryResult]:
        """搜索记忆"""
        return self.memory_domain_service.search_memories(
            user_id=user_id,
            query=query,
            top_k=top_k
        )
    
    def _to_dto(self, memory: MemoryItemModel) -> MemoryItemDTO:
        """将实体转换为 DTO"""
        return MemoryItemDTO(
            id=memory.id,
            user_id=memory.user_id,
            type=memory.type,
            text=memory.text,
            data=memory.data or {},
            importance=memory.importance,
            tags=memory.tags or [],
            source_session_id=memory.source_session_id,
            status=memory.status,
            created_at=memory.created_at,
            updated_at=memory.updated_at
        )
