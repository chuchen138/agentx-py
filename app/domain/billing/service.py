from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from decimal import Decimal, ROUND_HALF_UP
from app.domain.account.model import UsageRecord, Product
from app.domain.account.repository import UsageRecordRepository, ProductRepository
import logging

logger = logging.getLogger(__name__)

class BillingStrategy(ABC):
    @abstractmethod
    async def calculate(self, product: Product, usage_data: Dict[str, Any]) -> Decimal:
        pass
    
    def _round_amount(self, amount: Decimal) -> Decimal:
        return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class TokenUsageStrategy(BillingStrategy):
    async def calculate(self, product: Product, usage_data: Dict[str, Any]) -> Decimal:
        token_count = usage_data.get('token_count', 0)
        price_per_token = Decimal(str(product.price_config.get('price_per_token', 0)))
        amount = Decimal(token_count) * price_per_token
        return self._round_amount(amount)

class StorageUsageStrategy(BillingStrategy):
    async def calculate(self, product: Product, usage_data: Dict[str, Any]) -> Decimal:
        storage_mb = usage_data.get('storage_mb', 0)
        price_per_mb = Decimal(str(product.price_config.get('price_per_mb', 0)))
        amount = Decimal(storage_mb) * price_per_mb
        return self._round_amount(amount)

class SubscriptionStrategy(BillingStrategy):
    async def calculate(self, product: Product, usage_data: Dict[str, Any]) -> Decimal:
        monthly_price = Decimal(str(product.price_config.get('monthly_price', 0)))
        # 包月计费，固定金额
        return self._round_amount(monthly_price)

class TieredPricingStrategy(BillingStrategy):
    async def calculate(self, product: Product, usage_data: Dict[str, Any]) -> Decimal:
        usage = usage_data.get('usage', 0)
        tiers = product.price_config.get('tiers', [])
        
        amount = Decimal('0.00')
        remaining_usage = usage
        
        for tier in sorted(tiers, key=lambda x: x['max']):
            if remaining_usage <= 0:
                break
            
            tier_max = tier.get('max', float('inf'))
            tier_price = Decimal(str(tier.get('price', 0)))
            
            if tier_max == float('inf'):
                tier_usage = remaining_usage
            else:
                tier_usage = min(remaining_usage, tier_max)
            
            amount += Decimal(tier_usage) * tier_price
            remaining_usage -= tier_usage
        
        return self._round_amount(amount)

class BillingDomainService:
    def __init__(self, usage_record_repository: UsageRecordRepository, product_repository: ProductRepository):
        self.usage_record_repository = usage_record_repository
        self.product_repository = product_repository
        self._strategies = {
            'token': TokenUsageStrategy(),
            'storage': StorageUsageStrategy(),
            'subscription': SubscriptionStrategy(),
            'tiered': TieredPricingStrategy()
        }
    
    async def calculate_usage(self, product_id: int, usage_data: Dict[str, Any]) -> Optional[Decimal]:
        product = await self.product_repository.get_by_id(product_id)
        if not product:
            logger.error(f"Product not found: {product_id}")
            return None
        
        strategy = self._strategies.get(product.billing_type)
        if not strategy:
            logger.error(f"Unknown billing type: {product.billing_type}")
            return None
        
        try:
            amount = await strategy.calculate(product, usage_data)
            # 最低计费金额控制
            if amount < Decimal('0.01'):
                amount = Decimal('0.01')
            return amount
        except Exception as e:
            logger.error(f"Error calculating usage: {e}")
            return None
    
    async def create_usage_record(self, user_id: int, product_id: int, order_id: Optional[int],
                                 request_id: str, billing_type: str, service_id: str,
                                 usage_data: Dict[str, Any], amount: Decimal) -> Optional[UsageRecord]:
        # 检查幂等性
        existing_record = await self.usage_record_repository.get_by_request_id(request_id)
        if existing_record:
            logger.info(f"Usage record already exists for request_id: {request_id}")
            return existing_record
        
        usage_record = UsageRecord(
            user_id=user_id,
            product_id=product_id,
            order_id=order_id,
            request_id=request_id,
            billing_type=billing_type,
            service_id=service_id,
            usage_data=usage_data,
            amount=amount
        )
        
        try:
            created_record = await self.usage_record_repository.create(usage_record)
            logger.info(f"Created usage record: {created_record.id} for user {user_id}")
            return created_record
        except Exception as e:
            logger.error(f"Error creating usage record: {e}")
            return None
    
    async def get_usage_records_by_user(self, user_id: int, limit: int = 100) -> list:
        return await self.usage_record_repository.get_by_user_id(user_id, limit)
    
    async def check_idempotency(self, request_id: str) -> bool:
        existing_record = await self.usage_record_repository.get_by_request_id(request_id)
        return existing_record is not None
