from abc import ABC, abstractmethod
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.orm import joinedload
from app.domain.account.model import Account, UsageRecord, Order, Product

class AccountRepository(ABC):
    @abstractmethod
    async def create(self, account: Account) -> Account:
        pass
    
    @abstractmethod
    async def get_by_id(self, account_id: int) -> Optional[Account]:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int) -> Optional[Account]:
        pass
    
    @abstractmethod
    async def update(self, account: Account) -> Account:
        pass
    
    @abstractmethod
    async def delete(self, account_id: int) -> bool:
        pass
    
    @abstractmethod
    async def update_balance_with_version(self, account_id: int, new_balance: float, old_version: int) -> bool:
        pass

class AsyncAccountRepository(AccountRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, account: Account) -> Account:
        self.session.add(account)
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def get_by_id(self, account_id: int) -> Optional[Account]:
        result = await self.session.execute(
            select(Account).where(Account.id == account_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int) -> Optional[Account]:
        result = await self.session.execute(
            select(Account).where(Account.user_id == user_id)
            .options(joinedload(Account.orders), joinedload(Account.usage_records))
        )
        return result.scalar_one_or_none()
    
    async def update(self, account: Account) -> Account:
        account.version += 1
        await self.session.commit()
        await self.session.refresh(account)
        return account
    
    async def delete(self, account_id: int) -> bool:
        result = await self.session.execute(
            delete(Account).where(Account.id == account_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def update_balance_with_version(self, account_id: int, new_balance: float, old_version: int) -> bool:
        result = await self.session.execute(
            update(Account)
            .where(Account.id == account_id, Account.version == old_version)
            .values(balance=new_balance, version=Account.version + 1)
        )
        await self.session.commit()
        return result.rowcount > 0

class UsageRecordRepository(ABC):
    @abstractmethod
    async def create(self, usage_record: UsageRecord) -> UsageRecord:
        pass
    
    @abstractmethod
    async def get_by_request_id(self, request_id: str) -> Optional[UsageRecord]:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[UsageRecord]:
        pass

class AsyncUsageRecordRepository(UsageRecordRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, usage_record: UsageRecord) -> UsageRecord:
        self.session.add(usage_record)
        await self.session.commit()
        await self.session.refresh(usage_record)
        return usage_record
    
    async def get_by_request_id(self, request_id: str) -> Optional[UsageRecord]:
        result = await self.session.execute(
            select(UsageRecord).where(UsageRecord.request_id == request_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int, limit: int = 100) -> List[UsageRecord]:
        result = await self.session.execute(
            select(UsageRecord)
            .where(UsageRecord.user_id == user_id)
            .order_by(UsageRecord.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

class OrderRepository(ABC):
    @abstractmethod
    async def create(self, order: Order) -> Order:
        pass
    
    @abstractmethod
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def get_by_order_no(self, order_no: str) -> Optional[Order]:
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: int, status: Optional[str] = None) -> List[Order]:
        pass
    
    @abstractmethod
    async def update(self, order: Order) -> Order:
        pass

class AsyncOrderRepository(OrderRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        return order
    
    async def get_by_id(self, order_id: int) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
    
    async def get_by_order_no(self, order_no: str) -> Optional[Order]:
        result = await self.session.execute(
            select(Order).where(Order.order_no == order_no)
        )
        return result.scalar_one_or_none()
    
    async def get_by_user_id(self, user_id: int, status: Optional[str] = None) -> List[Order]:
        query = select(Order).where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.created_at.desc())
        
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def update(self, order: Order) -> Order:
        await self.session.commit()
        await self.session.refresh(order)
        return order

class ProductRepository(ABC):
    @abstractmethod
    async def create(self, product: Product) -> Product:
        pass
    
    @abstractmethod
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        pass
    
    @abstractmethod
    async def get_active_products(self) -> List[Product]:
        pass
    
    @abstractmethod
    async def update(self, product: Product) -> Product:
        pass

class AsyncProductRepository(ProductRepository):
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.commit()
        await self.session.refresh(product)
        return product
    
    async def get_by_id(self, product_id: int) -> Optional[Product]:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()
    
    async def get_active_products(self) -> List[Product]:
        result = await self.session.execute(
            select(Product).where(Product.status == "active")
        )
        return result.scalars().all()
    
    async def update(self, product: Product) -> Product:
        await self.session.commit()
        await self.session.refresh(product)
        return product
