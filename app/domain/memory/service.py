import hashlib
import re
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime
from app.domain.memory.model.memory_item import MemoryItemModel, CandidateMemory, MemoryResult
from app.domain.memory.repository import MemoryItemRepository, VectorStoreRepository
from app.domain.memory.constant.memory_metadata_constant import MemoryMetadataConstant
from app.domain.memory.constant.memory_type import MemoryType

class MemoryDomainService:
    """记忆领域服务"""
    
    def __init__(self, memory_item_repo: MemoryItemRepository, vector_store_repo: VectorStoreRepository):
        self.memory_item_repo = memory_item_repo
        self.vector_store_repo = vector_store_repo
    
    def save_memories(self, user_id: str, candidate_memories: List[CandidateMemory], 
                     source_session_id: Optional[str] = None) -> List[MemoryItemModel]:
        """保存记忆（包含去重、合并）"""
        saved_memories = []
        
        for candidate in candidate_memories:
            # 文本标准化
            normalized_text = self._normalize_text(candidate.text)
            
            # 生成去重哈希
            dedupe_hash = self._generate_dedupe_hash(normalized_text)
            
            # 检查是否已存在
            existing_memory = self.memory_item_repo.find_by_dedupe_hash(user_id, dedupe_hash)
            
            if existing_memory:
                # 执行合并逻辑
                merged_memory = self._merge_memories(existing_memory, candidate)
                saved_memories.append(self.memory_item_repo.update(merged_memory))
            else:
                # 创建新记忆
                new_memory = MemoryItemModel(
                    id=uuid.uuid4(),
                    user_id=user_id,
                    type=candidate.type,
                    text=candidate.text,
                    data=candidate.data,
                    importance=candidate.importance,
                    tags=candidate.tags,
                    source_session_id=source_session_id,
                    dedupe_hash=dedupe_hash,
                    status=1
                )
                saved_memory = self.memory_item_repo.create(new_memory)
                saved_memories.append(saved_memory)
        
        return saved_memories
    
    def search_memories(self, user_id: str, query: str, top_k: int = 16, 
                      similarity_weight: float = 0.7, importance_weight: float = 0.3) -> List[MemoryResult]:
        """搜索记忆（相似度 + 重要性加权）"""
        # 这里应该调用嵌入模型生成查询向量
        # 由于没有实际的嵌入模型，这里使用占位实现
        query_embedding = [0.0] * 1536  # 假设使用 1536 维向量
        
        # 搜索向量
        vector_results = self.vector_store_repo.search(query_embedding, user_id, top_k * 2)  # 候选加倍
        
        # 构建结果
        results = []
        for vector_store, similarity in vector_results:
            # 获取完整的记忆信息
            memory_item = self.memory_item_repo.get_by_id(vector_store.item_id)
            if memory_item and memory_item.status == 1:
                # 计算加权评分
                score = (similarity_weight * similarity) + (importance_weight * memory_item.importance)
                
                result = MemoryResult(
                    itemId=memory_item.id,
                    type=memory_item.type,
                    text=memory_item.text,
                    importance=memory_item.importance,
                    tags=memory_item.tags or [],
                    score=score
                )
                results.append(result)
        
        # 排序并返回 Top-K
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def get_memory_by_id(self, item_id: uuid.UUID) -> Optional[MemoryItemModel]:
        """根据 ID 获取记忆"""
        return self.memory_item_repo.get_by_id(item_id)
    
    def get_memories_by_user_id(self, user_id: str, page: int = 1, page_size: int = 20, 
                              memory_type: Optional[str] = None, 
                              tags: Optional[List[str]] = None, 
                              importance_min: Optional[float] = None) -> Tuple[List[MemoryItemModel], int]:
        """分页查询用户记忆"""
        return self.memory_item_repo.get_page_memories(
            user_id=user_id,
            page=page,
            page_size=page_size,
            memory_type=memory_type,
            tags=tags,
            importance_min=importance_min
        )
    
    def archive_memory(self, item_id: uuid.UUID) -> bool:
        """归档记忆（软删除）"""
        return self.memory_item_repo.delete(item_id)
    
    def batch_archive_memories(self, item_ids: List[uuid.UUID]) -> bool:
        """批量归档记忆"""
        return self.memory_item_repo.batch_delete(item_ids)
    
    def _normalize_text(self, text: str) -> str:
        """文本标准化"""
        # 合并多行
        text = text.replace('\n', ' ')
        # 合并连续空白
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        text = text.strip()
        # 转小写
        text = text.lower()
        return text
    
    def _generate_dedupe_hash(self, text: str) -> str:
        """生成去重哈希"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
    
    def _merge_memories(self, existing: MemoryItemModel, candidate: CandidateMemory) -> MemoryItemModel:
        """合并记忆"""
        # 重要性取最大值
        existing.importance = max(existing.importance, candidate.importance)
        
        # 标签合并去重
        existing_tags = set(existing.tags or [])
        candidate_tags = set(candidate.tags or [])
        existing.tags = list(existing_tags.union(candidate_tags))
        
        # 数据智能合并
        existing_data = existing.data or {}
        candidate_data = candidate.data or {}
        existing_data.update(candidate_data)  # 相同 key 保留新值，不同 key 合并
        existing.data = existing_data
        
        # 文本选择更丰富的版本
        if len(candidate.text) > len(existing.text):
            existing.text = candidate.text
        
        # 更新时间戳
        existing.updated_at = datetime.utcnow()
        
        return existing

class MemoryExtractorService:
    """记忆提取服务"""
    
    def __init__(self, memory_domain_service: MemoryDomainService):
        self.memory_domain_service = memory_domain_service
    
    def extract_from_message(self, user_id: str, message: str, 
                           conversation_history: Optional[List[Dict[str, str]]] = None) -> List[CandidateMemory]:
        """从用户消息中提取候选记忆"""
        # 这里应该调用 LLM 进行记忆提取
        # 由于没有实际的 LLM 服务，这里使用占位实现
        # 实际实现应该使用 Prompt 工程，调用 OpenAI 或其他 LLM API
        
        # 示例：简单的规则提取
        candidates = []
        
        # 检测用户偏好
        if any(keyword in message.lower() for keyword in ['偏好', '希望', '要求', '以后', '总是']):
            candidates.append(CandidateMemory(
                type=MemoryType.PROFILE.value,
                text=message,
                importance=0.9,
                tags=['preference']
            ))
        
        # 检测任务目标
        if any(keyword in message.lower() for keyword in ['任务', '目标', '计划', '需要', '完成']):
            candidates.append(CandidateMemory(
                type=MemoryType.TASK.value,
                text=message,
                importance=0.85,
                tags=['task']
            ))
        
        # 检测事实信息
        if any(keyword in message.lower() for keyword in ['是', '在', '有', '位于', '属于']):
            candidates.append(CandidateMemory(
                type=MemoryType.FACT.value,
                text=message,
                importance=0.8,
                tags=['fact']
            ))
        
        # 检测情景信息
        if any(keyword in message.lower() for keyword in ['刚才', '之前', '上一步', '讨论', '提到']):
            candidates.append(CandidateMemory(
                type=MemoryType.EPISODIC.value,
                text=message,
                importance=0.9,
                tags=['episodic']
            ))
        
        # 过滤低重要性记忆
        candidates = [c for c in candidates if self._should_store(c)]
        
        # 限制输出数量
        candidates = candidates[:3]  # 最多输出 3 条
        
        return candidates
    
    def _should_store(self, candidate: CandidateMemory) -> bool:
        """判断是否应该存储该记忆"""
        # 根据类型设置不同的阈值
        if candidate.type == MemoryType.EPISODIC.value:
            return candidate.importance >= 0.9
        else:
            return candidate.importance >= 0.8
    
    def extract_and_save(self, user_id: str, message: str, 
                        source_session_id: Optional[str] = None, 
                        conversation_history: Optional[List[Dict[str, str]]] = None) -> List[MemoryItemModel]:
        """提取并保存记忆"""
        # 提取候选记忆
        candidates = self.extract_from_message(user_id, message, conversation_history)
        
        # 保存记忆
        return self.memory_domain_service.save_memories(user_id, candidates, source_session_id)
