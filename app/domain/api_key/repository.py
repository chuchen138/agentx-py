from __future__ import annotations
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.domain.api_key.model import ApiKey


class ApiKeyRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, api_key: ApiKey) -> ApiKey:
        self.db.add(api_key)
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def get_by_id(self, api_key_id: UUID) -> Optional[ApiKey]:
        return self.db.query(ApiKey).filter(ApiKey.id == api_key_id).first()

    def get_by_api_key(self, api_key: str) -> Optional[ApiKey]:
        return self.db.query(ApiKey).filter(ApiKey.api_key == api_key).first()

    def get_by_user_id(self, user_id: UUID, skip: int = 0, limit: int = 100) -> List[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_agent_id(self, agent_id: UUID, user_id: UUID) -> List[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.agent_id == agent_id, ApiKey.user_id == user_id)
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    def search_by_name(self, user_id: UUID, name: str) -> List[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(
                ApiKey.user_id == user_id,
                ApiKey.name.ilike(f"%{name}%")
            )
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    def get_by_status(self, user_id: UUID, status: bool) -> List[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.user_id == user_id, ApiKey.status == status)
            .order_by(ApiKey.created_at.desc())
            .all()
        )

    def update(self, api_key: ApiKey) -> ApiKey:
        self.db.commit()
        self.db.refresh(api_key)
        return api_key

    def delete(self, api_key: ApiKey) -> None:
        self.db.delete(api_key)
        self.db.commit()

    def exists_by_api_key(self, api_key: str) -> bool:
        return self.db.query(ApiKey).filter(ApiKey.api_key == api_key).first() is not None

    def get_by_user_and_id(self, user_id: UUID, api_key_id: UUID) -> Optional[ApiKey]:
        return (
            self.db.query(ApiKey)
            .filter(ApiKey.id == api_key_id, ApiKey.user_id == user_id)
            .first()
        )
