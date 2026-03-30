from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Tuple
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.domain.memory.model.memory_item import MemoryItemModel, MemoryVectorStoreModel

class MemoryItemRepository(ABC):
    """记忆条目仓储接口"""
    
    @abstractmethod
    def create(self, memory_item: MemoryItemModel) -> MemoryItemModel:
        """创建记忆条目"""
        pass
    
    @abstractmethod
    def get_by_id(self, item_id: uuid.UUID) -> Optional[MemoryItemModel]:
        """根据 ID 获取记忆条目"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        """根据用户 ID 获取记忆条目"""
        pass
    
    @abstractmethod
    def get_by_type(self, user_id: str, memory_type: str, skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        """根据类型获取记忆条目"""
        pass
    
    @abstractmethod
    def get_by_tags(self, user_id: str, tags: List[str], skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        """根据标签获取记忆条目"""
        pass
    
    @abstractmethod
    def get_page_memories(self, user_id: str, page: int = 1, page_size: int = 20, 
                        memory_type: Optional[str] = None, 
                        tags: Optional[List[str]] = None, 
                        importance_min: Optional[float] = None) -> Tuple[List[MemoryItemModel], int]:
        """分页查询记忆条目"""
        pass
    
    @abstractmethod
    def find_by_dedupe_hash(self, user_id: str, dedupe_hash: str) -> Optional[MemoryItemModel]:
        """根据去重哈希查找记忆条目"""
        pass
    
    @abstractmethod
    def update(self, memory_item: MemoryItemModel) -> MemoryItemModel:
        """更新记忆条目"""
        pass
    
    @abstractmethod
    def delete(self, item_id: uuid.UUID) -> bool:
        """删除记忆条目"""
        pass
    
    @abstractmethod
    def batch_insert(self, memory_items: List[MemoryItemModel]) -> List[MemoryItemModel]:
        """批量插入记忆条目"""
        pass
    
    @abstractmethod
    def batch_delete(self, item_ids: List[uuid.UUID]) -> bool:
        """批量删除记忆条目"""
        pass

class VectorStoreRepository(ABC):
    """向量存储仓储接口"""
    
    @abstractmethod
    def add(self, item_id: uuid.UUID, embedding: List[float], text: str, metadata: Dict[str, Any]) -> MemoryVectorStoreModel:
        """添加向量"""
        pass
    
    @abstractmethod
    def search(self, query_embedding: List[float], user_id: str, top_k: int = 16, 
              min_similarity: float = 0.3) -> List[Tuple[MemoryVectorStoreModel, float]]:
        """相似度搜索"""
        pass
    
    @abstractmethod
    def delete_by_item_id(self, item_id: uuid.UUID) -> bool:
        """根据记忆条目 ID 删除向量"""
        pass
    
    @abstractmethod
    def create_index(self, index_type: str = "ivfflat", **kwargs) -> bool:
        """创建向量索引"""
        pass
    
    @abstractmethod
    def batch_add(self, embeddings: List[Tuple[uuid.UUID, List[float], str, Dict[str, Any]]]) -> List[MemoryVectorStoreModel]:
        """批量添加向量"""
        pass

class SQLAlchemyMemoryItemRepository(MemoryItemRepository):
    """SQLAlchemy 记忆条目仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, memory_item: MemoryItemModel) -> MemoryItemModel:
        self.db.add(memory_item)
        self.db.commit()
        self.db.refresh(memory_item)
        return memory_item
    
    def get_by_id(self, item_id: uuid.UUID) -> Optional[MemoryItemModel]:
        return self.db.query(MemoryItemModel).filter(MemoryItemModel.id == item_id).first()
    
    def get_by_user_id(self, user_id: str, skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        return self.db.query(MemoryItemModel).filter(
            MemoryItemModel.user_id == user_id,
            MemoryItemModel.status == 1
        ).offset(skip).limit(limit).all()
    
    def get_by_type(self, user_id: str, memory_type: str, skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        return self.db.query(MemoryItemModel).filter(
            MemoryItemModel.user_id == user_id,
            MemoryItemModel.type == memory_type,
            MemoryItemModel.status == 1
        ).offset(skip).limit(limit).all()
    
    def get_by_tags(self, user_id: str, tags: List[str], skip: int = 0, limit: int = 100) -> List[MemoryItemModel]:
        # 使用 PostgreSQL 的数组操作符
        return self.db.query(MemoryItemModel).filter(
            MemoryItemModel.user_id == user_id,
            MemoryItemModel.status == 1,
            MemoryItemModel.tags.overlap(tags)
        ).offset(skip).limit(limit).all()
    
    def get_page_memories(self, user_id: str, page: int = 1, page_size: int = 20, 
                        memory_type: Optional[str] = None, 
                        tags: Optional[List[str]] = None, 
                        importance_min: Optional[float] = None) -> Tuple[List[MemoryItemModel], int]:
        query = self.db.query(MemoryItemModel).filter(
            MemoryItemModel.user_id == user_id,
            MemoryItemModel.status == 1
        )
        
        if memory_type:
            query = query.filter(MemoryItemModel.type == memory_type)
        
        if tags:
            query = query.filter(MemoryItemModel.tags.overlap(tags))
        
        if importance_min:
            query = query.filter(MemoryItemModel.importance >= importance_min)
        
        total = query.count()
        items = query.order_by(MemoryItemModel.updated_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return items, total
    
    def find_by_dedupe_hash(self, user_id: str, dedupe_hash: str) -> Optional[MemoryItemModel]:
        return self.db.query(MemoryItemModel).filter(
            MemoryItemModel.user_id == user_id,
            MemoryItemModel.dedupe_hash == dedupe_hash,
            MemoryItemModel.status == 1
        ).first()
    
    def update(self, memory_item: MemoryItemModel) -> MemoryItemModel:
        self.db.commit()
        self.db.refresh(memory_item)
        return memory_item
    
    def delete(self, item_id: uuid.UUID) -> bool:
        memory_item = self.get_by_id(item_id)
        if memory_item:
            memory_item.status = 0  # 软删除
            self.db.commit()
            return True
        return False
    
    def batch_insert(self, memory_items: List[MemoryItemModel]) -> List[MemoryItemModel]:
        self.db.add_all(memory_items)
        self.db.commit()
        for item in memory_items:
            self.db.refresh(item)
        return memory_items
    
    def batch_delete(self, item_ids: List[uuid.UUID]) -> bool:
        result = self.db.query(MemoryItemModel).filter(
            MemoryItemModel.id.in_(item_ids)
        ).update({MemoryItemModel.status: 0}, synchronize_session=False)
        self.db.commit()
        return result > 0

class SQLAlchemyVectorStoreRepository(VectorStoreRepository):
    """SQLAlchemy 向量存储仓储实现"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add(self, item_id: uuid.UUID, embedding: List[float], text: str, metadata: Dict[str, Any]) -> MemoryVectorStoreModel:
        vector_store = MemoryVectorStoreModel(
            item_id=item_id,
            embedding=embedding,
            text=text,
            metadata=metadata
        )
        self.db.add(vector_store)
        self.db.commit()
        self.db.refresh(vector_store)
        return vector_store
    
    def search(self, query_embedding: List[float], user_id: str, top_k: int = 16, 
              min_similarity: float = 0.3) -> List[Tuple[MemoryVectorStoreModel, float]]:
        # 这里使用简化的相似度计算，实际项目中应该使用 PGVector 的余弦相似度函数
        # 由于没有实际的 PGVector 环境，这里使用占位实现
        # 实际实现应该使用：from pgvector.sqlalchemy import Vector
        # 并使用 vector.cosine_distance 函数
        
        # 简化实现：返回所有符合条件的向量，按相似度排序
        vectors = self.db.query(MemoryVectorStoreModel).filter(
            MemoryVectorStoreModel.metadata.contains({"user_id": user_id}),
            MemoryVectorStoreModel.metadata.contains({"status": 1})
        ).all()
        
        # 计算相似度（这里使用简化的欧氏距离）
        results = []
        for vector in vectors:
            # 简化的相似度计算
            similarity = 1.0  # 实际应该计算余弦相似度
            if similarity >= min_similarity:
                results.append((vector, similarity))
        
        # 排序并返回 Top-K
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]
    
    def delete_by_item_id(self, item_id: uuid.UUID) -> bool:
        result = self.db.query(MemoryVectorStoreModel).filter(
            MemoryVectorStoreModel.item_id == item_id
        ).delete()
        self.db.commit()
        return result > 0
    
    def create_index(self, index_type: str = "ivfflat", **kwargs) -> bool:
        # 实际项目中应该执行 CREATE INDEX 语句
        # 这里使用占位实现
        return True
    
    def batch_add(self, embeddings: List[Tuple[uuid.UUID, List[float], str, Dict[str, Any]]]) -> List[MemoryVectorStoreModel]:
        vector_stores = []
        for item_id, embedding, text, metadata in embeddings:
            vector_store = MemoryVectorStoreModel(
                item_id=item_id,
                embedding=embedding,
                text=text,
                metadata=metadata
            )
            vector_stores.append(vector_store)
        
        self.db.add_all(vector_stores)
        self.db.commit()
        for store in vector_stores:
            self.db.refresh(store)
        return vector_stores
