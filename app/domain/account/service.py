from typing import Optional, Dict, Any
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.account.model import Account
from app.domain.account.repository import AccountRepository, AsyncAccountRepository
from app.core.redis import redis_client
import json
import logging

logger = logging.getLogger(__name__)

class AccountDomainService:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository
    
    async def create_account(self, user_id: int) -> Account:
        account = Account(
            user_id=user_id,
            balance=Decimal('0.00'),
            credit=Decimal('0.00'),
            total_consumed=Decimal('0.00'),
            version=0
        )
        created_account = await self.account_repository.create(account)
        await self._invalidate_balance_cache(user_id)
        return created_account
    
    async def get_account_by_user_id(self, user_id: int) -> Optional[Account]:
        return await self.account_repository.get_by_user_id(user_id)
    
    async def get_account_by_id(self, account_id: int) -> Optional[Account]:
        return await self.account_repository.get_by_id(account_id)
    
    async def recharge(self, user_id: int, amount: Decimal) -> Account:
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            account = await self.create_account(user_id)
        
        account.balance += amount
        updated_account = await self.account_repository.update(account)
        await self._invalidate_balance_cache(user_id)
        logger.info(f"Recharged {amount} to user {user_id}, new balance: {updated_account.balance}")
        return updated_account
    
    async def add_credit(self, user_id: int, amount: Decimal, reason: str) -> Account:
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            account = await self.create_account(user_id)
        
        account.credit += amount
        updated_account = await self.account_repository.update(account)
        await self._invalidate_balance_cache(user_id)
        logger.info(f"Added credit {amount} to user {user_id}, reason: {reason}")
        return updated_account
    
    async def deduct_balance(self, user_id: int, amount: Decimal) -> bool:
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            return False
        
        available_balance = account.balance + account.credit
        if available_balance < amount:
            return False
        
        account.balance -= amount
        account.total_consumed += amount
        await self.account_repository.update(account)
        await self._invalidate_balance_cache(user_id)
        logger.info(f"Deducted {amount} from user {user_id}, new balance: {account.balance}")
        return True
    
    async def get_available_balance(self, user_id: int) -> Decimal:
        # 先尝试从缓存获取
        cached_balance = await self._get_balance_from_cache(user_id)
        if cached_balance is not None:
            return cached_balance
        
        # 缓存未命中，从数据库获取
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            return Decimal('0.00')
        
        available_balance = account.balance + account.credit
        await self._set_balance_to_cache(user_id, available_balance)
        return available_balance
    
    async def check_sufficient_balance(self, user_id: int, amount: Decimal) -> bool:
        available_balance = await self.get_available_balance(user_id)
        return available_balance >= amount
    
    async def _get_balance_from_cache(self, user_id: int) -> Optional[Decimal]:
        try:
            key = f"account:{user_id}:balance"
            cached_data = await redis_client.get(key)
            if cached_data:
                return Decimal(cached_data)
        except Exception as e:
            logger.error(f"Error getting balance from cache: {e}")
        return None
    
    async def _set_balance_to_cache(self, user_id: int, balance: Decimal) -> None:
        try:
            key = f"account:{user_id}:balance"
            await redis_client.set(key, str(balance), ex=300)  # 5分钟过期
        except Exception as e:
            logger.error(f"Error setting balance to cache: {e}")
    
    async def _invalidate_balance_cache(self, user_id: int) -> None:
        try:
            key = f"account:{user_id}:balance"
            await redis_client.delete(key)
        except Exception as e:
            logger.error(f"Error invalidating balance cache: {e}")

    async def exists_account(self, user_id: int) -> bool:
        account = await self.account_repository.get_by_user_id(user_id)
        return account is not None

    async def get_account_balance(self, user_id: int) -> Dict[str, Any]:
        account = await self.account_repository.get_by_user_id(user_id)
        if not account:
            return {
                "balance": Decimal('0.00'),
                "credit": Decimal('0.00'),
                "total_consumed": Decimal('0.00'),
                "available_balance": Decimal('0.00')
            }
        
        available_balance = account.balance + account.credit
        return {
            "balance": account.balance,
            "credit": account.credit,
            "total_consumed": account.total_consumed,
            "available_balance": available_balance
        }
