from typing import Optional, Dict, Any
from decimal import Decimal
from app.domain.account.service import AccountDomainService
from app.domain.account.repository import OrderRepository
from app.domain.account.model import Order
from app.domain.account.schemas import AccountResponse, RechargeRequest, CreditRequest
import uuid
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class AccountAppService:
    def __init__(self, account_domain_service: AccountDomainService, order_repository: OrderRepository):
        self.account_domain_service = account_domain_service
        self.order_repository = order_repository
    
    async def get_user_account(self, user_id: int) -> Optional[AccountResponse]:
        account = await self.account_domain_service.get_account_by_user_id(user_id)
        if not account:
            # 自动创建账户
            account = await self.account_domain_service.create_account(user_id)
        
        return AccountResponse(
            id=account.id,
            user_id=account.user_id,
            balance=account.balance,
            credit=account.credit,
            total_consumed=account.total_consumed,
            version=account.version,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    
    async def get_account_by_id(self, account_id: int) -> Optional[AccountResponse]:
        account = await self.account_domain_service.get_account_by_id(account_id)
        if not account:
            return None
        
        return AccountResponse(
            id=account.id,
            user_id=account.user_id,
            balance=account.balance,
            credit=account.credit,
            total_consumed=account.total_consumed,
            version=account.version,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
    
    async def recharge(self, user_id: int, recharge_request: RechargeRequest) -> Dict[str, Any]:
        # 检查是否为大额充值
        if recharge_request.amount > Decimal('1000'):
            # 触发二次确认逻辑
            logger.info(f"Large recharge detected: {recharge_request.amount} for user {user_id}")
            # 这里可以添加二次确认的逻辑
        
        # 创建充值订单
        order_no = f"RECHARGE_{uuid.uuid4().hex.upper()[:16]}"
        order = Order(
            user_id=user_id,
            order_no=order_no,
            type="recharge",
            title="账户充值",
            description=f"充值金额: {recharge_request.amount}元",
            amount=recharge_request.amount,
            currency="CNY",
            status="pending",
            payment_platform=recharge_request.payment_platform,
            payment_type=recharge_request.payment_type,
            order_metadata=None,
            expired_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        created_order = await self.order_repository.create(order)
        
        # 这里应该触发异步充值流程
        # 实际的充值逻辑会在支付回调中处理
        
        return {
            "order_id": created_order.id,
            "order_no": created_order.order_no,
            "amount": created_order.amount,
            "status": created_order.status,
            "payment_platform": created_order.payment_platform
        }
    
    async def add_credit(self, user_id: int, credit_request: CreditRequest) -> Dict[str, Any]:
        # 增加信用额度（需要管理员权限）
        account = await self.account_domain_service.add_credit(
            user_id, 
            credit_request.amount, 
            credit_request.reason
        )
        
        return {
            "user_id": user_id,
            "credit_added": credit_request.amount,
            "new_credit": account.credit,
            "reason": credit_request.reason
        }
    
    async def check_sufficient_balance(self, user_id: int, amount: Decimal) -> bool:
        return await self.account_domain_service.check_sufficient_balance(user_id, amount)
    
    async def get_available_balance(self, user_id: int) -> Decimal:
        return await self.account_domain_service.get_available_balance(user_id)
    
    async def exists_account(self, user_id: int) -> bool:
        return await self.account_domain_service.exists_account(user_id)
    
    async def get_account_balance(self, user_id: int) -> Dict[str, Any]:
        return await self.account_domain_service.get_account_balance(user_id)
