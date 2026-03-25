from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.middleware.auth import get_current_user
from app.domain.user.model import UserModel
from app.application.api_key.api_key_app_service import ApiKeyAppService
from app.domain.api_key.schemas import (
    ApiKeyCreate, ApiKeyUpdate, ApiKeyResponse, ApiKeyListResponse, 
    ApiKeyStatusUpdate, ApiKeyResetResponse, ApiKeyValidationResponse
)

router = APIRouter(prefix="/api-keys", tags=["api-key"])


@router.post("", response_model=ApiKeyResponse, status_code=201)
def create_api_key(
    api_key_data: ApiKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建 API 密钥"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.create_api_key(
            user_id=current_user.id,
            agent_id=api_key_data.agent_id,
            name=api_key_data.name
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("", response_model=List[ApiKeyListResponse])
def get_api_keys(
    agent_id: Optional[UUID] = Query(None, description="Filter by Agent ID"),
    name: Optional[str] = Query(None, description="Search by name"),
    status: Optional[bool] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 API 密钥列表"""
    try:
        app_service = ApiKeyAppService(db)
        
        if agent_id:
            return app_service.get_api_keys_by_agent(agent_id, current_user.id)
        elif name:
            return app_service.search_api_keys(current_user.id, name)
        else:
            return app_service.get_api_keys(current_user.id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/{api_key_id}", response_model=ApiKeyResponse)
def get_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取 API 密钥详情"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.get_api_key(api_key_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{api_key_id}", response_model=ApiKeyResponse)
def update_api_key(
    api_key_id: UUID,
    api_key_data: ApiKeyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 API 密钥"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.update_api_key(
            api_key_id=api_key_id,
            user_id=current_user.id,
            name=api_key_data.name,
            status=api_key_data.status
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.put("/{api_key_id}/status", response_model=ApiKeyResponse)
def update_api_key_status(
    api_key_id: UUID,
    status_data: ApiKeyStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新 API 密钥状态"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.toggle_api_key_status(
            api_key_id=api_key_id,
            user_id=current_user.id,
            status=status_data.status
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/{api_key_id}/reset", response_model=ApiKeyResetResponse)
def reset_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重置 API 密钥"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.reset_api_key(api_key_id, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/{api_key_id}", status_code=204)
def delete_api_key(
    api_key_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除 API 密钥"""
    try:
        app_service = ApiKeyAppService(db)
        app_service.delete_api_key(api_key_id, current_user.id)
        return None
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/validate", response_model=ApiKeyValidationResponse)
def validate_api_key(
    api_key: str = Query(..., description="API key to validate"),
    db: Session = Depends(get_db)
):
    """验证 API 密钥"""
    try:
        app_service = ApiKeyAppService(db)
        return app_service.validate_api_key(api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")
