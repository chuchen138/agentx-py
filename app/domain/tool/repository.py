from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.domain.tool.model import ToolEntity, ToolVersionEntity, UserToolEntity
from app.domain.tool.enums import ToolStatus, ToolVersionStatus


class ToolRepository(ABC):
    @abstractmethod
    async def create(self, tool: ToolEntity) -> ToolEntity:
        pass

    @abstractmethod
    async def update(self, tool: ToolEntity) -> ToolEntity:
        pass

    @abstractmethod
    async def delete(self, tool_id: int) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, tool_id: int) -> Optional[ToolEntity]:
        pass

    @abstractmethod
    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        pass

    @abstractmethod
    async def get_by_status(self, status: str, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        pass

    @abstractmethod
    async def get_market_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        pass

    @abstractmethod
    async def get_global_tools(self) -> List[ToolEntity]:
        pass

    @abstractmethod
    async def get_pending_review_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        pass

    @abstractmethod
    async def get_statistics(self) -> Dict[str, int]:
        pass


class SQLAlchemyToolRepository(ToolRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, tool: ToolEntity) -> ToolEntity:
        self.session.add(tool)
        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def update(self, tool: ToolEntity) -> ToolEntity:
        await self.session.commit()
        await self.session.refresh(tool)
        return tool

    async def delete(self, tool_id: int) -> bool:
        result = await self.session.execute(
            select(ToolEntity).where(ToolEntity.id == tool_id)
        )
        tool = result.scalar_one_or_none()
        if tool:
            await self.session.delete(tool)
            await self.session.commit()
            return True
        return False

    async def get_by_id(self, tool_id: int) -> Optional[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity).where(ToolEntity.id == tool_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity)
            .where(ToolEntity.user_id == user_id)
            .offset(skip)
            .limit(limit)
            .order_by(ToolEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_by_status(self, status: str, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity)
            .where(ToolEntity.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(ToolEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_market_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity)
            .where(ToolEntity.status == ToolStatus.PUBLISHED.value)
            .offset(skip)
            .limit(limit)
            .order_by(ToolEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_global_tools(self) -> List[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity)
            .where(ToolEntity.is_global == True)
            .order_by(ToolEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_pending_review_tools(self, skip: int = 0, limit: int = 20) -> List[ToolEntity]:
        result = await self.session.execute(
            select(ToolEntity)
            .where(ToolEntity.status.in_([
                ToolStatus.WAITING_REVIEW.value,
                ToolStatus.FETCHING_TOOLS.value,
                ToolStatus.GITHUB_URL_VALIDATION.value,
                ToolStatus.DEPLOYING.value,
                ToolStatus.PUBLISHING.value
            ]))
            .offset(skip)
            .limit(limit)
            .order_by(ToolEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_statistics(self) -> Dict[str, int]:
        total_result = await self.session.execute(
            select(func.count(ToolEntity.id))
        )
        total = total_result.scalar() or 0

        published_result = await self.session.execute(
            select(func.count(ToolEntity.id))
            .where(ToolEntity.status == ToolStatus.PUBLISHED.value)
        )
        published = published_result.scalar() or 0

        pending_result = await self.session.execute(
            select(func.count(ToolEntity.id))
            .where(ToolEntity.status.in_([
                ToolStatus.WAITING_REVIEW.value,
                ToolStatus.FETCHING_TOOLS.value,
                ToolStatus.GITHUB_URL_VALIDATION.value,
                ToolStatus.DEPLOYING.value,
                ToolStatus.PUBLISHING.value
            ]))
        )
        pending = pending_result.scalar() or 0

        rejected_result = await self.session.execute(
            select(func.count(ToolEntity.id))
            .where(ToolEntity.status == ToolStatus.REJECTED.value)
        )
        rejected = rejected_result.scalar() or 0

        return {
            "total_tools": total,
            "published_tools": published,
            "pending_tools": pending,
            "rejected_tools": rejected
        }


class ToolVersionRepository(ABC):
    @abstractmethod
    async def create(self, version: ToolVersionEntity) -> ToolVersionEntity:
        pass

    @abstractmethod
    async def update(self, version: ToolVersionEntity) -> ToolVersionEntity:
        pass

    @abstractmethod
    async def delete(self, version_id: int) -> bool:
        pass

    @abstractmethod
    async def get_by_id(self, version_id: int) -> Optional[ToolVersionEntity]:
        pass

    @abstractmethod
    async def get_by_tool_id(self, tool_id: int, skip: int = 0, limit: int = 20) -> List[ToolVersionEntity]:
        pass

    @abstractmethod
    async def get_published_version(self, tool_id: int) -> Optional[ToolVersionEntity]:
        pass


class SQLAlchemyToolVersionRepository(ToolVersionRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, version: ToolVersionEntity) -> ToolVersionEntity:
        self.session.add(version)
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def update(self, version: ToolVersionEntity) -> ToolVersionEntity:
        await self.session.commit()
        await self.session.refresh(version)
        return version

    async def delete(self, version_id: int) -> bool:
        result = await self.session.execute(
            select(ToolVersionEntity).where(ToolVersionEntity.id == version_id)
        )
        version = result.scalar_one_or_none()
        if version:
            await self.session.delete(version)
            await self.session.commit()
            return True
        return False

    async def get_by_id(self, version_id: int) -> Optional[ToolVersionEntity]:
        result = await self.session.execute(
            select(ToolVersionEntity).where(ToolVersionEntity.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_by_tool_id(self, tool_id: int, skip: int = 0, limit: int = 20) -> List[ToolVersionEntity]:
        result = await self.session.execute(
            select(ToolVersionEntity)
            .where(ToolVersionEntity.tool_id == tool_id)
            .offset(skip)
            .limit(limit)
            .order_by(ToolVersionEntity.created_at.desc())
        )
        return result.scalars().all()

    async def get_published_version(self, tool_id: int) -> Optional[ToolVersionEntity]:
        result = await self.session.execute(
            select(ToolVersionEntity)
            .where(
                and_(
                    ToolVersionEntity.tool_id == tool_id,
                    ToolVersionEntity.status == ToolVersionStatus.PUBLISHED.value
                )
            )
            .order_by(ToolVersionEntity.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


class UserToolRepository(ABC):
    @abstractmethod
    async def create(self, user_tool: UserToolEntity) -> UserToolEntity:
        pass

    @abstractmethod
    async def delete(self, user_id: int, tool_id: int) -> bool:
        pass

    @abstractmethod
    async def get_user_installed_tools(self, user_id: int) -> List[UserToolEntity]:
        pass

    @abstractmethod
    async def is_tool_installed(self, user_id: int, tool_id: int) -> bool:
        pass


class SQLAlchemyUserToolRepository(UserToolRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_tool: UserToolEntity) -> UserToolEntity:
        self.session.add(user_tool)
        await self.session.commit()
        await self.session.refresh(user_tool)
        return user_tool

    async def delete(self, user_id: int, tool_id: int) -> bool:
        result = await self.session.execute(
            select(UserToolEntity)
            .where(
                and_(
                    UserToolEntity.user_id == user_id,
                    UserToolEntity.tool_id == tool_id
                )
            )
        )
        user_tool = result.scalar_one_or_none()
        if user_tool:
            await self.session.delete(user_tool)
            await self.session.commit()
            return True
        return False

    async def get_user_installed_tools(self, user_id: int) -> List[UserToolEntity]:
        result = await self.session.execute(
            select(UserToolEntity)
            .where(UserToolEntity.user_id == user_id)
            .order_by(UserToolEntity.installed_at.desc())
        )
        return result.scalars().all()

    async def is_tool_installed(self, user_id: int, tool_id: int) -> bool:
        result = await self.session.execute(
            select(UserToolEntity)
            .where(
                and_(
                    UserToolEntity.user_id == user_id,
                    UserToolEntity.tool_id == tool_id
                )
            )
        )
        return result.scalar_one_or_none() is not None