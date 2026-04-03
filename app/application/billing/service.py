from typing import Dict, Any, Optional
from decimal import Decimal
from app.domain.billing.service import BillingDomainService
from app.domain.account.service import AccountDomainService
from app.domain.account.repository import ProductRepository
from app.domain.account.model import Product
from app.domain.account.schemas import BillingRequest, BillingResponse
from app.core.redis import redis_client
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)

class BillingService:
    def __init__(self, billing_domain_service: BillingDomainService, 
                 account_domain_service: AccountDomainService,
                 product_repository: ProductRepository):
        self.billing_domain_service = billing_domain_service
        self.account_domain_service = account_domain_service
        self.product_repository = product_repository
    
    async def charge(self, billing_request: BillingRequest) -> BillingResponse:
        # 验证计费上下文完整性
        if not all([billing_request.user_id, billing_request.product_id, 
                   billing_request.service_id, billing_request.request_id]):
            return BillingResponse(
                success=False,
                amount=Decimal('0.00'),
                message="Invalid billing request parameters"
            )
        
        # 检查幂等性
        if await self.billing_domain_service.check_idempotency(billing_request.request_id):
            return BillingResponse(
                success=True,
                amount=Decimal('0.00'),
                message="Already charged for this request"
            )
        
        # 查找商品配置
        product = await self.product_repository.get_by_id(billing_request.product_id)
        if not product:
            return BillingResponse(
                success=False,
                amount=Decimal('0.00'),
                message="Product not found"
            )
        
        # 计算费用
        amount = await self.billing_domain_service.calculate_usage(
            billing_request.product_id, 
            billing_request.usage_data
        )
        if amount is None:
            return BillingResponse(
                success=False,
                amount=Decimal('0.00'),
                message="Failed to calculate usage"
            )
        
        # 使用分布式锁防止并发超扣
        lock_key = f"lock:billing:{billing_request.user_id}"
        lock_acquired = False
        retry_count = 0
        max_retries = 3
        
        while retry_count < max_retries:
            try:
                # 尝试获取锁
                lock_acquired = await redis_client.set(
                    lock_key, 
                    str(uuid.uuid4()), 
                    ex=5,  # 5秒过期
                    nx=True
                )
                
                if lock_acquired:
                    # 检查余额是否充足
                    if not await self.account_domain_service.check_sufficient_balance(
                        billing_request.user_id, 
                        amount
                    ):
                        return BillingResponse(
                            success=False,
                            amount=amount,
                            message="Insufficient balance"
                        )
                    
                    # 扣费
                    if not await self.account_domain_service.deduct_balance(
                        billing_request.user_id, 
                        amount
                    ):
                        return BillingResponse(
                            success=False,
                            amount=amount,
                            message="Failed to deduct balance"
                        )
                    
                    # 记录用量
                    usage_record = await self.billing_domain_service.create_usage_record(
                        user_id=billing_request.user_id,
                        product_id=billing_request.product_id,
                        order_id=None,
                        request_id=billing_request.request_id,
                        billing_type=product.billing_type,
                        service_id=billing_request.service_id,
                        usage_data=billing_request.usage_data,
                        amount=amount
                    )
                    
                    if not usage_record:
                        # 扣费成功但记录失败，需要回滚
                        await self.account_domain_service.recharge(
                            billing_request.user_id, 
                            amount
                        )
                        return BillingResponse(
                            success=False,
                            amount=amount,
                            message="Failed to create usage record"
                        )
                    
                    return BillingResponse(
                        success=True,
                        amount=amount,
                        usage_record_id=usage_record.id,
                        message="Billing successful"
                    )
                else:
                    # 锁未获取到，重试
                    retry_count += 1
                    await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error during billing: {e}")
                retry_count += 1
                await asyncio.sleep(0.1)
            finally:
                if lock_acquired:
                    try:
                        await redis_client.delete(lock_key)
                    except Exception as e:
                        logger.error(f"Error releasing lock: {e}")
        
        return BillingResponse(
            success=False,
            amount=amount,
            message="Failed to acquire lock, please try again"
        )
    
    async def get_usage_records(self, user_id: int, limit: int = 100) -> list:
        return await self.billing_domain_service.get_usage_records_by_user(user_id, limit)
