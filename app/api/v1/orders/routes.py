from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from app.domain.account.repository import OrderRepository
from app.domain.account.schemas import OrderResponse
from app.infrastructure.dependency_injection import get_order_repository
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["orders"])
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    # 这里应该从JWT token中获取用户ID
    # 暂时返回固定用户ID作为示例
    return 1

@router.get("", response_model=List[OrderResponse])
async def get_orders(
    status: Optional[str] = Query(None, description="Order status"),
    user_id: int = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository)
):
    orders = await order_repository.get_by_user_id(user_id, status)
    return orders

@router.get("/{id}", response_model=OrderResponse)
async def get_order_by_id(
    id: int,
    user_id: int = Depends(get_current_user),
    order_repository: OrderRepository = Depends(get_order_repository)
):
    order = await order_repository.get_by_id(id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # 确保用户只能查看自己的订单
    if order.user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order
