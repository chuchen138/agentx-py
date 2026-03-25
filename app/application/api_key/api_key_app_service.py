from __future__ import annotations
from typing import List, Optional
from sqlalchemy.orm import Session
from app.domain.api_key.service import ApiKeyService
from app.domain.api_key.schemas import (
    ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse, ApiKeyListResponse, 
    ApiKeyValidationResponse, ApiKeyResetResponse
)


class ApiKeyAppService:
    def __init__(self, db: Session):
        self.api_key_service = ApiKeyService(db)

    def create_api_key(self, user_id: str, agent_id: str, name: str) -> ApiKeyResponse:
        """创建 API 密钥"""
        api_key = self.api_key_service.create_api_key(user_id, agent_id, name)
        agent_name = self.api_key_service.get_agent_name(agent_id)
        
        return ApiKeyResponse(
            id=api_key.id,
            api_key=api_key.api_key,  # 仅创建时返回
            agent_id=api_key.agent_id,
            agent_name=agent_name,
            user_id=api_key.user_id,
            name=api_key.name,
            status=api_key.status,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_expired=api_key.is_expired,
            is_available=api_key.is_available,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )

    def get_api_key(self, api_key_id: str, user_id: str) -> ApiKeyResponse:
        """获取 API 密钥详情"""
        api_key = self.api_key_service.get_api_key_by_id(api_key_id, user_id)
        if not api_key:
            raise ValueError("API key not found or access denied")
        
        agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
        
        return ApiKeyResponse(
            id=api_key.id,
            api_key=None,  # 不返回密钥值
            agent_id=api_key.agent_id,
            agent_name=agent_name,
            user_id=api_key.user_id,
            name=api_key.name,
            status=api_key.status,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_expired=api_key.is_expired,
            is_available=api_key.is_available,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )

    def get_api_keys(self, user_id: str) -> List[ApiKeyListResponse]:
        """获取用户的所有 API 密钥"""
        api_keys = self.api_key_service.get_api_keys_by_user(user_id)
        responses = []
        
        for api_key in api_keys:
            agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
            # 脱敏显示 API 密钥
            masked_api_key = api_key.api_key[:8] + "****" + api_key.api_key[-4:]
            
            responses.append(ApiKeyListResponse(
                id=api_key.id,
                api_key=masked_api_key,
                agent_id=api_key.agent_id,
                agent_name=agent_name,
                name=api_key.name,
                status=api_key.status,
                usage_count=api_key.usage_count,
                last_used_at=api_key.last_used_at,
                is_expired=api_key.is_expired,
                is_available=api_key.is_available,
                created_at=api_key.created_at
            ))
        
        return responses

    def get_api_keys_by_agent(self, agent_id: str, user_id: str) -> List[ApiKeyListResponse]:
        """获取特定 Agent 的 API 密钥"""
        api_keys = self.api_key_service.get_api_keys_by_agent(agent_id, user_id)
        responses = []
        
        for api_key in api_keys:
            agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
            masked_api_key = api_key.api_key[:8] + "****" + api_key.api_key[-4:]
            
            responses.append(ApiKeyListResponse(
                id=api_key.id,
                api_key=masked_api_key,
                agent_id=api_key.agent_id,
                agent_name=agent_name,
                name=api_key.name,
                status=api_key.status,
                usage_count=api_key.usage_count,
                last_used_at=api_key.last_used_at,
                is_expired=api_key.is_expired,
                is_available=api_key.is_available,
                created_at=api_key.created_at
            ))
        
        return responses

    def search_api_keys(self, user_id: str, name: str) -> List[ApiKeyListResponse]:
        """按名称搜索 API 密钥"""
        api_keys = self.api_key_service.search_api_keys(user_id, name)
        responses = []
        
        for api_key in api_keys:
            agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
            masked_api_key = api_key.api_key[:8] + "****" + api_key.api_key[-4:]
            
            responses.append(ApiKeyListResponse(
                id=api_key.id,
                api_key=masked_api_key,
                agent_id=api_key.agent_id,
                agent_name=agent_name,
                name=api_key.name,
                status=api_key.status,
                usage_count=api_key.usage_count,
                last_used_at=api_key.last_used_at,
                is_expired=api_key.is_expired,
                is_available=api_key.is_available,
                created_at=api_key.created_at
            ))
        
        return responses

    def update_api_key(self, api_key_id: str, user_id: str, name: Optional[str] = None, status: Optional[bool] = None) -> ApiKeyResponse:
        """更新 API 密钥"""
        api_key = self.api_key_service.update_api_key(api_key_id, user_id, name, status)
        agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
        
        return ApiKeyResponse(
            id=api_key.id,
            api_key=None,
            agent_id=api_key.agent_id,
            agent_name=agent_name,
            user_id=api_key.user_id,
            name=api_key.name,
            status=api_key.status,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_expired=api_key.is_expired,
            is_available=api_key.is_available,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )

    def toggle_api_key_status(self, api_key_id: str, user_id: str, status: bool) -> ApiKeyResponse:
        """切换 API 密钥状态"""
        api_key = self.api_key_service.toggle_api_key_status(api_key_id, user_id, status)
        agent_name = self.api_key_service.get_agent_name(api_key.agent_id)
        
        return ApiKeyResponse(
            id=api_key.id,
            api_key=None,
            agent_id=api_key.agent_id,
            agent_name=agent_name,
            user_id=api_key.user_id,
            name=api_key.name,
            status=api_key.status,
            usage_count=api_key.usage_count,
            last_used_at=api_key.last_used_at,
            expires_at=api_key.expires_at,
            is_expired=api_key.is_expired,
            is_available=api_key.is_available,
            created_at=api_key.created_at,
            updated_at=api_key.updated_at
        )

    def reset_api_key(self, api_key_id: str, user_id: str) -> ApiKeyResetResponse:
        """重置 API 密钥"""
        api_key, new_api_key = self.api_key_service.reset_api_key(api_key_id, user_id)
        
        return ApiKeyResetResponse(
            id=api_key.id,
            new_api_key=new_api_key,
            message="API key reset successfully"
        )

    def delete_api_key(self, api_key_id: str, user_id: str) -> None:
        """删除 API 密钥"""
        self.api_key_service.delete_api_key(api_key_id, user_id)

    def validate_api_key(self, api_key: str) -> ApiKeyValidationResponse:
        """验证 API 密钥"""
        valid, user_id, agent_id, message = self.api_key_service.validate_api_key(api_key)
        
        return ApiKeyValidationResponse(
            valid=valid,
            user_id=user_id,
            agent_id=agent_id,
            message=message
        )
