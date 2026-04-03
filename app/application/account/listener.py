import asyncio
import logging
from decimal import Decimal
from app.domain.account.service import AccountDomainService
from app.domain.account.repository import OrderRepository
from app.core.redis import redis_client
import json
import time

logger = logging.getLogger(__name__)

class RechargeEventListener:
    def __init__(self, account_domain_service: AccountDomainService, order_repository: OrderRepository):
        self.account_domain_service = account_domain_service
        self.order_repository = order_repository
        self.queue_name = "recharge_events"
    
    async def start_listening(self):
        """开始监听充值事件"""
        logger.info("Starting recharge event listener...")
        while True:
            try:
                # 从Redis队列中获取事件
                event_data = await redis_client.brpop(self.queue_name, timeout=5)
                if event_data:
                    _, event_json = event_data
                    event = json.loads(event_json)
                    await self.handle_recharge_event(event)
            except Exception as e:
                logger.error(f"Error in recharge event listener: {e}")
                await asyncio.sleep(1)
    
    async def handle_recharge_event(self, event: dict):
        """处理充值事件"""
        order_id = event.get("order_id")
        user_id = event.get("user_id")
        amount = Decimal(str(event.get("amount", 0)))
        transaction_id = event.get("transaction_id")
        
        if not all([order_id, user_id, amount]):
            logger.error(f"Invalid recharge event: {event}")
            return
        
        # 重试机制
        max_retries = 5
        retry_count = 0
        base_delay = 1  # 基础延迟时间（秒）
        
        while retry_count < max_retries:
            try:
                # 更新订单状态
                order = await self.order_repository.get_by_id(order_id)
                if not order:
                    logger.error(f"Order not found: {order_id}")
                    return
                
                if order.status != "pending":
                    logger.info(f"Order already processed: {order_id}, status: {order.status}")
                    return
                
                # 增加用户余额
                await self.account_domain_service.recharge(user_id, amount)
                
                # 更新订单状态为已支付
                order.status = "paid"
                order.transaction_id = transaction_id
                order.paid_at = time.strftime("%Y-%m-%d %H:%M:%S")
                await self.order_repository.update(order)
                
                # 触发余额更新通知（WebSocket推送）
                await self.notify_balance_update(user_id)
                
                logger.info(f"Recharge event processed successfully: order {order_id}, user {user_id}, amount {amount}")
                return
            except Exception as e:
                retry_count += 1
                delay = base_delay * (2 ** (retry_count - 1))  # 指数退避
                logger.error(f"Error processing recharge event (retry {retry_count}/{max_retries}): {e}")
                await asyncio.sleep(delay)
        
        logger.error(f"Failed to process recharge event after {max_retries} retries: {event}")
    
    async def notify_balance_update(self, user_id: int):
        """通知余额更新（WebSocket推送）"""
        try:
            # 获取用户最新余额
            balance_info = await self.account_domain_service.get_account_balance(user_id)
            
            # 构造通知消息
            notification = {
                "type": "balance_update",
                "user_id": user_id,
                "balance_info": balance_info,
                "timestamp": time.time()
            }
            
            # 发送到用户的WebSocket通道
            # 这里需要根据实际的WebSocket实现来发送消息
            # 暂时只记录日志
            logger.info(f"Balance update notification for user {user_id}: {balance_info}")
            
            # 示例：如果使用Redis发布订阅
            # await redis_client.publish(f"user:{user_id}:notifications", json.dumps(notification))
        except Exception as e:
            logger.error(f"Error sending balance update notification: {e}")
    
    async def publish_recharge_event(self, order_id: int, user_id: int, amount: Decimal, transaction_id: str):
        """发布充值事件"""
        event = {
            "order_id": order_id,
            "user_id": user_id,
            "amount": str(amount),
            "transaction_id": transaction_id,
            "timestamp": time.time()
        }
        
        await redis_client.lpush(self.queue_name, json.dumps(event))
        logger.info(f"Published recharge event: {event}")
