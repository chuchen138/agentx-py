from __future__ import annotations
import secrets
import string
from typing import List, Optional, Tuple
import uuid
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from app.domain.api_key.model import ApiKey
from app.domain.api_key.repository import ApiKeyRepository
from app.domain.agent.model import Agent


class ApiKeyService:
    def __init__(self, db: Session):
        self.repository = ApiKeyRepository(db)
        self.db = db

    def generate_api_key(self, agent_id: str) -> str:
        """生成 API 密钥"""
        random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        api_key = f"ak_{agent_id.replace('-', '_')}_{random_part}"
        
        # 确保密钥唯一
        while self.repository.exists_by_api_key(api_key):
            random_part = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
            api_key = f"ak_{agent_id.replace('-', '_')}_{random_part}"
        
        return api_key

    def create_api_key(self, user_id: str, agent_id: str, name: str) -> ApiKey:
        """创建 API 密钥"""
        # 验证 Agent 是否存在且属于该用户
        agent = self.db.query(Agent).filter(Agent.id == agent_id, Agent.user_id == user_id).first()
        if not agent:
            raise ValueError("Agent not found or access denied")
        
        api_key_value = self.generate_api_key(agent_id)
        api_key = ApiKey(
            api_key=api_key_value,
            agent_id=agent_id,
            user_id=user_id,
            name=name,
            status=True
        )
        
        return self.repository.create(api_key)

    def get_api_key_by_id(self, api_key_id: str, user_id: str) -> Optional[ApiKey]:
        """获取 API 密钥详情"""
        return self.repository.get_by_user_and_id(user_id, api_key_id)

    def get_api_keys_by_user(self, user_id: str) -> List[ApiKey]:
        """获取用户的所有 API 密钥"""
        return self.repository.get_by_user_id(user_id)

    def get_api_keys_by_agent(self, agent_id: str, user_id: str) -> List[ApiKey]:
        """获取特定 Agent 的 API 密钥"""
        return self.repository.get_by_agent_id(agent_id, user_id)

    def search_api_keys(self, user_id: str, name: str) -> List[ApiKey]:
        """按名称搜索 API 密钥"""
        return self.repository.search_by_name(user_id, name)

    def get_api_keys_by_status(self, user_id: str, status: bool) -> List[ApiKey]:
        """按状态获取 API 密钥"""
        return self.repository.get_by_status(user_id, status)

    def update_api_key(self, api_key_id: str, user_id: str, name: Optional[str] = None, status: Optional[bool] = None) -> ApiKey:
        """更新 API 密钥"""
        api_key = self.repository.get_by_user_and_id(user_id, api_key_id)
        if not api_key:
            raise ValueError("API key not found or access denied")
        
        if name is not None:
            api_key.name = name
        if status is not None:
            api_key.status = status
        
        return self.repository.update(api_key)

    def toggle_api_key_status(self, api_key_id: str, user_id: str, status: bool) -> ApiKey:
        """切换 API 密钥状态"""
        api_key = self.repository.get_by_user_and_id(user_id, api_key_id)
        if not api_key:
            raise ValueError("API key not found or access denied")
        
        api_key.status = status
        return self.repository.update(api_key)

    def reset_api_key(self, api_key_id: str, user_id: str) -> Tuple[ApiKey, str]:
        """重置 API 密钥"""
        api_key = self.repository.get_by_user_and_id(user_id, api_key_id)
        if not api_key:
            raise ValueError("API key not found or access denied")
        
        # 生成新的密钥值
        new_api_key = self.generate_api_key(api_key.agent_id)
        api_key.api_key = new_api_key
        api_key.usage_count = 0
        api_key.last_used_at = None
        api_key.updated_at = datetime.now(UTC)
        
        updated_api_key = self.repository.update(api_key)
        return updated_api_key, new_api_key

    def delete_api_key(self, api_key_id: str, user_id: str) -> None:
        """删除 API 密钥"""
        api_key = self.repository.get_by_user_and_id(user_id, api_key_id)
        if not api_key:
            raise ValueError("API key not found or access denied")
        
        self.repository.delete(api_key)

    def validate_api_key(self, api_key: str) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
        """验证 API 密钥"""
        api_key_obj = self.repository.get_by_api_key(api_key)
        if not api_key_obj:
            return False, None, None, "Invalid API key"
        
        if not api_key_obj.status:
            return False, None, None, "API key is disabled"
        
        if api_key_obj.is_expired:
            return False, None, None, "API key has expired"
        
        # 更新使用统计
        api_key_obj.update_usage()
        self.repository.update(api_key_obj)
        
        return True, api_key_obj.user_id, api_key_obj.agent_id, "API key is valid"

    def get_agent_name(self, agent_id: str) -> Optional[str]:
        """获取 Agent 名称"""
        agent = self.db.query(Agent).filter(Agent.id == agent_id).first()
        return agent.name if agent else None
